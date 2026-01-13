"""
纸质数据转换工具 - 网页版后端服务
基于 FastAPI 实现
"""

import os
import sys
import uuid
import asyncio
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加父目录到路径，以便导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr_processor import OCRProcessor
from table_processor import CSVParser
from excel_writer import ExcelWriter
from llm_config import get_config, LLMConfig, LLMConfigManager, get_config_manager


# ==================== 数据模型 ====================

class ColumnConfig(BaseModel):
    """列配置模型"""
    headers: List[str]
    column_count: int


class ProcessRequest(BaseModel):
    """处理请求模型"""
    task_id: str
    column_config: ColumnConfig


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    current_file: Optional[str] = None
    total_files: int = 0
    processed_files: int = 0
    success_count: int = 0
    fail_count: int = 0
    message: Optional[str] = None
    output_file: Optional[str] = None


# ==================== 全局状态 ====================

app = FastAPI(
    title="纸质数据转换服务",
    description="基于OCR的纸质表格识别与转换API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务存储
tasks: dict[str, TaskStatus] = {}

# 目录配置
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== 辅助函数 ====================

def get_image_files(directory: Path) -> List[Path]:
    """获取目录中的所有图片文件（包括子目录）"""
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    files = []
    # 使用 rglob 递归扫描所有子目录
    for f in directory.rglob('*'):
        if f.is_file() and f.suffix.lower() in extensions:
            files.append(f)
    return sorted(files)


async def process_task(task_id: str, column_headers: List[str]):
    """后台处理任务"""
    try:
        task = tasks[task_id]
        task.status = "processing"

        # 初始化计数器（确保从0开始）
        task.success_count = 0
        task.fail_count = 0
        task.processed_files = 0
        print(f"[DEBUG] Initialized counters: success={task.success_count}, fail={task.fail_count}")

        # 获取上传的图片
        task_dir = UPLOAD_DIR / task_id
        print(f"[DEBUG] task_dir: {task_dir}")
        print(f"[DEBUG] task_dir exists: {task_dir.exists()}")

        image_files = get_image_files(task_dir)
        print(f"[DEBUG] Found {len(image_files)} image files: {[f.name for f in image_files]}")

        if not image_files:
            task.status = "failed"
            task.message = "未找到有效的图片文件"
            print(f"[DEBUG] No image files found in {task_dir}")
            return

        task.total_files = len(image_files)

        # 创建Excel写入器
        output_filename = f"{task_id}_output.xlsx"
        output_path = OUTPUT_DIR / output_filename
        excel_writer = ExcelWriter(str(output_path), column_headers)

        # 创建OCR处理器（使用配置管理器）
        llm_config = get_config()
        ocr_processor = OCRProcessor(llm_config)

        # 处理每张图片
        for idx, image_path in enumerate(image_files):
            task.current_file = image_path.name
            task.progress = int((idx / len(image_files)) * 100)
            print(f"[DEBUG] Processing {idx+1}/{len(image_files)}: {image_path.name}")

            try:
                csv_text = ocr_processor.process_image_with_headers(
                    str(image_path),
                    column_headers,
                    max_retries=3
                )

                if csv_text:
                    headers, rows, parse_error = CSVParser.parse(csv_text)

                    if not parse_error and len(headers) == len(column_headers):
                        excel_writer.add_data(rows, image_path.name)
                        task.success_count += 1
                        print(f"[DEBUG] Success: {image_path.name} (total success: {task.success_count})")
                    else:
                        task.fail_count += 1
                        print(f"[DEBUG] Failed (parse error or column mismatch): {image_path.name} (total fail: {task.fail_count})")
                else:
                    task.fail_count += 1
                    print(f"[DEBUG] Failed (no csv_text): {image_path.name} (total fail: {task.fail_count})")

            except Exception as e:
                task.fail_count += 1
                print(f"[DEBUG] Failed (exception): {image_path.name} - {str(e)} (total fail: {task.fail_count})")

            task.processed_files = idx + 1
            print(f"[DEBUG] After processing {image_path.name}: success={task.success_count}, fail={task.fail_count}, processed={task.processed_files}")
            await asyncio.sleep(0.5)  # 限流

        # 保存Excel
        excel_writer.save()
        task.output_file = output_filename
        task.status = "completed"
        task.progress = 100
        task.message = f"处理完成：成功 {task.success_count} 张，失败 {task.fail_count} 张"
        print(f"[DEBUG] Final: success={task.success_count}, fail={task.fail_count}, total={task.total_files}")

    except Exception as e:
        task = tasks[task_id]
        task.status = "failed"
        task.message = f"处理失败：{str(e)}"
        print(f"[DEBUG] Outer exception: {str(e)}")


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路由"""
    return {
        "name": "纸质数据转换服务 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """上传图片文件"""
    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")

    # 生成任务ID
    task_id = str(uuid.uuid4())
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(exist_ok=True, parents=True)

    # 保存文件
    uploaded_files = []
    for file in files:
        # 获取纯文件名（去除路径）
        filename = os.path.basename(file.filename)
        file_path = task_dir / filename

        # 如果文件名包含路径分隔符，创建子目录
        if '/' in file.filename or '\\' in file.filename:
            # 获取相对路径的目录部分
            relative_dir = os.path.dirname(file.filename)
            if relative_dir:
                # 创建子目录
                subdir = task_dir / relative_dir.replace('\\', '/')
                subdir.mkdir(exist_ok=True, parents=True)
                file_path = subdir / filename

        # 写入文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        uploaded_files.append(filename)

    # 创建任务状态
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0,
        total_files=len(uploaded_files),
        processed_files=0,
        success_count=0,
        fail_count=0,
        message=f"已上传 {len(uploaded_files)} 个文件"
    )

    return {
        "task_id": task_id,
        "file_count": len(uploaded_files),
        "files": uploaded_files
    }


@app.post("/api/process")
async def start_process(request: ProcessRequest, background_tasks: BackgroundTasks):
    """开始处理任务"""
    # 打印请求数据用于调试
    import json
    print(f"[DEBUG] Received request: {request.model_dump()}")

    task_id = request.task_id

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status == "processing":
        raise HTTPException(status_code=400, detail="任务正在处理中")

    # 添加后台任务
    background_tasks.add_task(
        process_task,
        task_id,
        request.column_config.headers
    )

    return {"task_id": task_id, "status": "started"}


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "current_file": task.current_file,
        "total_files": task.total_files,
        "processed_files": task.processed_files,
        "success_count": task.success_count,
        "fail_count": task.fail_count,
        "message": task.message,
        "output_file": task.output_file
    }


@app.get("/api/download/{task_id}")
async def download_file(task_id: str):
    """下载处理结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务未完成")

    if not task.output_file:
        raise HTTPException(status_code=404, detail="输出文件不存在")

    file_path = OUTPUT_DIR / task.output_file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已过期或不存在")

    return FileResponse(
        path=file_path,
        filename=f"转换结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status,
                "progress": t.progress,
                "total_files": t.total_files,
                "success_count": t.success_count,
                "fail_count": t.fail_count
            }
            for t in tasks.values()
        ]
    }


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务及其文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除上传的文件
    task_dir = UPLOAD_DIR / task_id
    if task_dir.exists():
        import shutil
        shutil.rmtree(task_dir)

    # 删除任务记录
    del tasks[task_id]

    return {"message": "任务已删除"}


# ==================== 配置管理 API ====================

@app.get("/api/config/providers")
async def get_providers():
    """获取所有支持的大模型提供商"""
    return {"providers": LLMConfigManager.list_providers()}


@app.get("/api/config")
async def get_current_config():
    """获取当前的大模型配置（不包含敏感信息）"""
    config = get_config()
    return {
        "provider": config.provider,
        "model": config.model,
        "api_key": "",  # 前端不显示真实的API密钥，始终返回空字符串
        "has_api_key": bool(config.api_key),  # 标记是否已配置API密钥
        "base_url": config.base_url,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "timeout": config.timeout
    }


@app.post("/api/config")
async def update_llm_config(config_data: dict):
    """更新大模型配置"""
    try:
        # 使用全局单例获取当前配置
        manager = get_config_manager()
        current_config = manager.get_config()

        # 处理API密钥：如果前端传入的api_key为空且指定了keep_api_key，则保持原密钥不变
        api_key = config_data.get("api_key", "")
        keep_api_key = config_data.get("keep_api_key", False)

        if keep_api_key and not api_key:
            # 保持原API密钥
            api_key = current_config.api_key

        # 创建新的配置对象
        new_config = LLMConfig(
            provider=config_data.get("provider", "doubao"),
            model=config_data.get("model", ""),
            api_key=api_key,
            base_url=config_data.get("base_url"),
            temperature=config_data.get("temperature", 0.01),
            max_tokens=config_data.get("max_tokens", 4096),
            timeout=config_data.get("timeout", 180)
        )

        # 验证配置
        is_valid, error_msg = new_config.validate()
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 保存配置（使用全局单例，确保全局状态同步）
        success = manager.save_config(new_config)

        if not success:
            raise HTTPException(status_code=500, detail="保存配置失败")

        return {
            "message": "配置已保存",
            "provider": new_config.provider,
            "model": new_config.model,
            "has_api_key": bool(new_config.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置无效: {str(e)}")


# ==================== 启动服务 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
