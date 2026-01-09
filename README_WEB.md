# 纸质数据转换工具 - 网页版

基于 OCR 的纸质表格识别与转换工具，支持批量上传图片并转换为 Excel 文件。

## 功能特点

- 🖼️ **文件夹上传**: 支持选择文件夹或多选图片文件
- 📊 **智能识别**: 基于豆包 OCR API 的高精度表格识别
- ⚙️ **灵活配置**: 自定义表格列数和列标题
- 📈 **实时进度**: 实时显示处理进度和状态
- 💾 **一键下载**: 处理完成后直接下载 Excel 文件
- 🎨 **现代界面**: 简洁美观的用户界面

## 技术栈

### 后端
- **FastAPI**: 现代化的 Python Web 框架
- **Uvicorn**: ASGI 服务器
- **豆包 OCR API**: 表格识别引擎

### 前端
- **Vue.js 3**: 渐进式 JavaScript 框架
- **Vite**: 下一代前端构建工具
- **简洁现代风格**: 参考 Stripe/Notion 的设计风格

## 项目结构

```
纸质数据转换 -网页版/
├── backend/                 # 后端服务
│   ├── app.py              # FastAPI 主应用
│   ├── requirements.txt    # Python 依赖
│   ├── ocr_processor.py    # OCR 处理器
│   ├── table_processor.py  # 表格处理器
│   └── excel_writer.py     # Excel 写入器
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── App.vue        # 主应用组件
│   │   ├── main.js        # 入口文件
│   │   ├── style.css      # 全局样式
│   │   ├── api.js         # API 服务
│   │   └── components/    # 子组件
│   │       ├── FileUpload.vue      # 文件上传
│   │       ├── ColumnConfig.vue    # 列配置
│   │       ├── ProcessProgress.vue # 进度显示
│   │       └── CompletionView.vue  # 完成视图
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── images/                 # 测试图片目录
└── README_WEB.md          # 本文档
```

## 快速开始

### 1. 安装依赖

**后端依赖:**
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖:**
```bash
cd frontend
npm install
```

### 2. 配置环境变量（可选）

创建 `.env` 文件设置豆包 OCR API 密钥：

```bash
ARK_API_KEY=your_api_key_here
ARK_ENDPOINT_ID=your_endpoint_id_here
```

如果不配置，将使用代码中的默认值。

### 3. 启动服务

**启动后端服务（端口 8000）:**
```bash
cd backend
python app.py
```

**启动前端开发服务器（端口 3000）:**
```bash
cd frontend
npm run dev
```

### 4. 访问应用

打开浏览器访问: `http://localhost:3000`

## 使用说明

### 步骤 1: 上传文件
- 点击上传区域选择文件夹
- 或直接拖拽多个图片文件到上传区域
- 支持的格式: JPG, PNG, BMP, WebP

### 步骤 2: 配置列结构
- 输入表格的列数（1-20）
- 为每列设置标题
- 预览表格结构

### 步骤 3: 处理
- 点击"开始处理"按钮
- 系统将逐个识别图片中的表格
- 实时显示处理进度

### 步骤 4: 下载
- 处理完成后点击"下载 Excel"
- 数据将以统一格式导出到 Excel 文件

## API 文档

后端启动后，访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传图片文件 |
| `/api/process` | POST | 开始处理任务 |
| `/api/status/{task_id}` | GET | 获取任务状态 |
| `/api/download/{task_id}` | GET | 下载结果文件 |

## 生产部署

### 前端构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录。

### 后端部署

使用 Docker 部署：

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
COPY frontend/dist ./static

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 注意事项

1. **API 限流**: 系统设置了 0.5 秒的处理间隔，避免超出 API 限制
2. **文件大小**: 单个图片建议不超过 10MB
3. **并发处理**: 当前版本为串行处理，适合中小规模批量转换
4. **数据保留**: 上传的文件和处理结果会定期清理

## 许可证

MIT License

## 更新日志

### V3.0 网页版
- 添加 FastAPI 后端服务
- 实现 Vue.js 前端界面
- 支持文件夹上传
- 实时进度显示
- 一键下载功能
