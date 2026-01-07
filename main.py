import os
import base64
import requests
import glob
import time
import pandas as pd
import io

# 配置部分
# 如果你不想每次运行都输入，可以直接在这里填入
API_KEY_DEFAULT = "f56d7c74-5e13-4a71-8973-d4cebd7aece1"
ENDPOINT_ID_DEFAULT = "ep-20260104183112-7c7dt"  # 例如: ep-20240604012345-abcde
INPUT_DIR = "images"  # 图片文件夹名称，所有图片请放在这个文件夹内

def get_mime_type(image_path):
    """根据文件扩展名确定的MIME type"""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.webp':
        return 'image/webp'
    elif ext == '.bmp':
        return 'image/bmp'
    else:
        return 'image/jpeg' # 默认

def encode_image(image_path):
    """将图片编码为Base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image(api_key, endpoint_id, image_path, retry_reason=None, expected_columns=None):
    """调用豆包模型API处理单张图片，可携带纠错提示和期望列数"""
    
    # 构造请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 读取并编码图片
    base64_image = encode_image(image_path)
    mime_type = get_mime_type(image_path)
    
    # 构造请求体 - 适配 OpenAI 兼容格式 (火山引擎 Ark)
    user_text = (
        "请仔细分析这张图片中的表格数据。"
        "重要要求："
        "1) 只识别图片中的主数据表格，忽略其他文字、标题、页码等无关信息；"
        "2) 先识别表格的第一行（表头），确定表头有多少列，表头列数就是整个表格的列数；"
        "3) 严格按照识别的表头列数输出，所有数据行的列数必须与表头完全一致；"
        "4) 只输出表头行和数据行，不要添加任何额外的列（如序号列、来源列等）；"
        "5) 空白单元格输出空字符串''；"
        "6) 如果图片中有多个表格，只识别最大的主表格；"
        "7) 输出标准CSV格式（逗号分隔），第一行为表头，后续行为数据；"
        "8) 不要输出任何解释、翻译、Markdown标记或代码块标记，只输出纯CSV文本。"
    )
    
    if expected_columns:
        user_text += f" 特别注意：此表格应该有且仅有 {expected_columns} 列，请严格按照此列数输出。"
    
    if retry_reason:
        user_text += f" 发现结构问题：{retry_reason}。请严格修正后重新输出。"

    data = {
        "model": endpoint_id,
        "temperature": 0.01,  # 降低随机性，提高数据提取的准确率 - 关键参数
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是专业的OCR表格识别专家。"
                    "核心任务：识别图片中的主数据表格，严格按照表头列数输出CSV。"
                    "关键规则："
                    "1) 只识别主表格，忽略页眉、页脚、标题、页码等；"
                    "2) 表头列数 = 所有数据行的列数，必须完全一致；"
                    "3) 不得添加序号列、来源列等额外列；"
                    "4) 空白格输出空字符串''；"
                    "5) 不得合并、拆分、新增或删除列；"
                    "6) 不翻译、不解释、不输出Markdown或代码块；"
                    "7) 只输出纯CSV文本，第一行表头，后续行数据。"
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096
    }

    # 火山引擎 Ark API 端点 (通常是这个，或者是 https://ark.cn-beijing.volces.com/api/v3/chat/completions)
    api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    try:
        # 大模型处理图片可能较慢，将超时时间延长至 180 秒
        response = requests.post(api_url, headers=headers, json=data, timeout=600)
        
        if response.status_code == 200:
            result = response.json()
            # 提取回复内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                # 清理可能存在的 markdown 代码块标记
                content = content.replace("```csv", "").replace("```", "").strip()
                # 移除可能的说明文字（在CSV之前或之后）
                lines = content.splitlines()
                csv_lines = []
                in_csv = False
                for line in lines:
                    line = line.strip()
                    # 如果包含逗号，可能是CSV行
                    if ',' in line:
                        in_csv = True
                        csv_lines.append(line)
                    elif in_csv and line == '':
                        # CSV块结束后的空行，停止
                        break
                    elif in_csv:
                        # 仍在CSV块中，继续添加
                        csv_lines.append(line)
                if csv_lines:
                    content = '\n'.join(csv_lines)
                return content
            else:
                return f"Error: API返回结构异常 - {result}"
        else:
            return f"Error: 请求失败 {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error: 发生异常 - {str(e)}"

def validate_csv_structure(csv_text):
    """校验CSV每行列数是否与表头一致"""
    import csv
    lines = [line for line in csv_text.splitlines() if line.strip() != ""]
    if not lines:
        return False, "空内容"
    reader = csv.reader(lines)
    rows = list(reader)
    header_len = len(rows[0]) if rows else 0
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != header_len:
            return False, f"第{idx}行列数{len(row)}与表头{header_len}不一致"
    return True, ""

def main():
    print("=== 豆包纸质数据转电子数据批量处理工具 (Excel版) ===")
    
    # 获取配置
    api_key = API_KEY_DEFAULT or os.environ.get("ARK_API_KEY")
    if not api_key:
        api_key = input("请输入您的 API Key: ").strip()
    
    endpoint_id = ENDPOINT_ID_DEFAULT or os.environ.get("ARK_ENDPOINT_ID")
    if not endpoint_id:
        endpoint_id = input("请输入您的 Endpoint ID (例如 ep-202xxxx): ").strip()

    # 检查图片目录是否存在
    if not os.path.exists(INPUT_DIR):
        print(f"提示: 图片文件夹 '{INPUT_DIR}' 不存在，已为您自动创建。")
        print(f"请将需要转换的图片放入 '{INPUT_DIR}' 文件夹中，然后重新运行本程序。")
        os.makedirs(INPUT_DIR)
        return

    # 扫描指定目录下的图片文件
    # 支持 jpg, jpeg, png
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
    image_files = []
    for ext in image_extensions:
        # 使用 os.path.join 拼接路径
        search_pattern = os.path.join(INPUT_DIR, ext)
        image_files.extend(glob.glob(search_pattern))

    if not image_files:
        print(f"未在 '{INPUT_DIR}' 文件夹中找到图片文件。请放入图片后重试。")
        return

    print(f"在 '{INPUT_DIR}' 中找到 {len(image_files)} 张图片，开始处理...")
    
    all_dfs = []

    for i, img_path in enumerate(image_files):
        print(f"[{i+1}/{len(image_files)}] 正在处理: {img_path}")
        
        # 调用API
        text_content = process_image(api_key, endpoint_id, img_path)
        
        # 处理结果保存
        if text_content.startswith("Error"):
            print(f"  FAILED: {text_content}")
            # 记录错误日志
            with open("error_log.txt", "a", encoding="utf-8") as err_log:
                err_log.write(f"{img_path}: {text_content}\n")
        else:
            # 结构校验，不通过则带反馈重试一次
            ok, reason = validate_csv_structure(text_content)
            if not ok:
                print(f"  STRUCT WARN: {reason}，尝试带纠错提示重试...")
                retry_text = process_image(api_key, endpoint_id, img_path, retry_reason=reason)
                if retry_text.startswith("Error"):
                    print(f"  RETRY FAILED: {retry_text}")
                    with open("error_log.txt", "a", encoding="utf-8") as err_log:
                        err_log.write(f"{img_path}: 初次结构问题 {reason}，重试失败：{retry_text}\n")
                    text_content = None
                else:
                    text_content = retry_text
                    ok, reason = validate_csv_structure(text_content)
                    if not ok:
                        print(f"  RETRY STRUCT WARN: {reason}")
                        with open("error_log.txt", "a", encoding="utf-8") as err_log:
                            err_log.write(f"{img_path}: 重试后仍结构异常 {reason}\nContent:\n{text_content}\n")
                        text_content = None

            if text_content:
                print(f"  API响应成功，正在解析CSV...")
                try:
                    csv_io = io.StringIO(text_content)
                    df = pd.read_csv(csv_io, dtype=str)
                    
                    # 检查列数是否异常（超过10列可能是识别错误）
                    num_cols = len(df.columns)
                    if num_cols > 10:
                        print(f"  WARN: 识别出 {num_cols} 列，可能过多。尝试重新识别...")
                        # 尝试用更严格的提示重新识别
                        retry_text = process_image(api_key, endpoint_id, img_path, 
                                                  retry_reason=f"识别出{num_cols}列过多，请只识别主表格的核心数据列（通常3-5列）")
                        if not retry_text.startswith("Error"):
                            retry_ok, retry_reason = validate_csv_structure(retry_text)
                            if retry_ok:
                                csv_io_retry = io.StringIO(retry_text)
                                df_retry = pd.read_csv(csv_io_retry, dtype=str)
                                if len(df_retry.columns) < num_cols:
                                    print(f"  重试后识别出 {len(df_retry.columns)} 列，使用重试结果")
                                    df = df_retry
                                    text_content = retry_text
                    
                    # 添加来源文件名列（在最后添加，不影响原始列结构）
                    df['Source_Image'] = os.path.basename(img_path)
                    all_dfs.append(df)
                    print(f"  SUCCESS: 已解析 {len(df)} 行数据，{len(df.columns)-1} 列（不含Source_Image列）")
                except Exception as e:
                    print(f"  PARSE ERROR: 解析CSV失败 - {e}")
                    print(f"  Raw Content: {text_content[:200]}...")
                    with open("error_log.txt", "a", encoding="utf-8") as err_log:
                        err_log.write(f"{img_path} Parse Error: {e}\nContent:\n{text_content}\n")
        
        # 简单限速
        time.sleep(0.5)

    if all_dfs:
        print("正在合并所有数据并保存为 Excel...")
        try:
            final_df = pd.concat(all_dfs, ignore_index=True)
            output_excel = "output_data.xlsx"
            final_df.to_excel(output_excel, index=False)
            print(f"=== 全部完成！数据已保存至 {output_excel} ===")
        except Exception as e:
            print(f"保存 Excel 失败: {e}")
    else:
        print("未获取到有效数据，无法生成 Excel。")

if __name__ == "__main__":
    main()
