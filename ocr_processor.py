"""
OCR处理器 - 负责与豆包API交互
提供增强的识别能力和多重重试机制
"""

import os
import base64
import requests
from typing import Optional, Tuple, List
from table_processor import TableData, CSVParser, TableStructureAnalyzer


class OCRProcessor:
    """豆包OCR处理器"""

    # 系统提示词 - 专业的表格识别指令
    SYSTEM_PROMPT = """你是专业的纸质表格识别专家。

核心任务：将图片中的表格转换为准确的CSV格式。

严格规则：
1. 只识别图片中的主数据表格，完全忽略标题、页眉、页脚、页码、说明文字
2. 第一行必须是表格的表头（列标题），从第二行开始是数据
3. 表格有多少列，输出的CSV就必须有多少列，所有行列数必须完全一致
4. 绝对禁止添加任何额外的列（如序号、行号、来源等）
5. 空白单元格用两个连续的逗号表示（即空字符串）
6. 不做任何翻译、解释、注释
7. 不输出Markdown代码块标记，只输出纯CSV文本
8. 使用英文逗号(,)作为分隔符
9. 如果单元格内容包含逗号、引号或换行，用双引号包裹该单元格
10. 识别时保持原始内容的准确性，包括数字格式、日期格式等

输出格式要求：
- 第一行：表头（列标题）
- 后续行：数据行
- 所有行必须有相同的列数
- 纯CSV文本，无其他内容"""

    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    def _get_mime_type(self, image_path: str) -> str:
        """根据文件扩展名获取MIME类型"""
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg')

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为Base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _build_user_prompt(self, image_path: str, retry_count: int = 0,
                          previous_error: str = "", expected_columns: int = None) -> str:
        """构建用户提示词"""

        base_prompt = """请仔细识别这张图片中的表格数据。

要求：
1. 找到图片中的主数据表格（最大的那个表格）
2. 识别表格的第一行作为表头
3. 统计表头有多少列，整个表格就输出多少列
4. 确保每一行的列数与表头完全一致
5. 输出标准CSV格式，第一行是表头，后面是数据
6. 只输出CSV文本，不要任何解释说明"""

        if expected_columns:
            base_prompt += f"\n\n特别注意：经过分析，此表格应该有 {expected_columns} 列，请严格按照此列数输出。"

        if retry_count > 0 and previous_error:
            base_prompt += f"\n\n上次识别存在问题：{previous_error}\n请严格修正后重新输出。"

        return base_prompt

    def _call_api(self, image_path: str, user_prompt: str) -> Tuple[bool, str]:
        """
        调用豆包API

        返回: (success, response_content)
        """
        try:
            base64_image = self._encode_image(image_path)
            mime_type = self._get_mime_type(image_path)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.endpoint_id,
                "temperature": 0.01,  # 最低随机性
                "messages": [
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
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

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=180  # 3分钟超时
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return True, content
                else:
                    return False, f"API返回结构异常: {result}"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return False, "请求超时（180秒）"
        except Exception as e:
            return False, f"异常: {str(e)}"

    def process_image(self, image_path: str,
                     max_retries: int = 3) -> Tuple[Optional[TableData], Optional[str]]:
        """
        处理单张图片，支持自动重试

        返回: (TableData, error_message)
        """
        file_name = os.path.basename(image_path)
        expected_columns = None

        for attempt in range(max_retries):
            # 构建提示词
            user_prompt = self._build_user_prompt(
                image_path,
                retry_count=attempt,
                expected_columns=expected_columns
            )

            # 调用API
            success, content = self._call_api(image_path, user_prompt)

            if not success:
                if attempt == max_retries - 1:
                    return None, f"API调用失败: {content}"
                continue

            # 清理响应
            csv_text = CSVParser.clean_markdown(content)

            # 解析CSV
            headers, rows, parse_error = CSVParser.parse(csv_text)

            if parse_error:
                expected_columns = None  # 重置预期列数
                if attempt == max_retries - 1:
                    return None, f"CSV解析失败: {parse_error}"
                continue

            # 创建表格数据对象
            table_data = TableData(
                file_name=file_name,
                headers=headers,
                rows=rows,
                column_count=len(headers),
                raw_csv=csv_text
            )

            # 验证结构
            is_valid, error_msg = TableStructureAnalyzer.validate_structure(table_data)

            if not is_valid:
                expected_columns = len(headers)  # 记录识别出的列数用于下次重试
                if attempt == max_retries - 1:
                    return None, f"结构验证失败: {error_msg}"
                continue

            # 成功
            return table_data, None

        return None, "达到最大重试次数"

    def process_image_with_headers(self, image_path: str,
                                   expected_headers: List[str],
                                   max_retries: int = 3) -> Optional[str]:
        """
        处理单张图片，使用预定义的列标题

        Args:
            image_path: 图片路径
            expected_headers: 预定义的列标题列表
            max_retries: 最大重试次数

        Returns:
            CSV文本或None
        """
        expected_column_count = len(expected_headers)
        file_name = os.path.basename(image_path)

        # 构建包含列标题的提示
        headers_str = " | ".join(expected_headers)

        for attempt in range(max_retries):
            # 构建特殊的用户提示
            user_prompt = f"""请识别这张图片中的表格数据。

重要：表格必须严格按照以下格式输出：
- 列数：{expected_column_count} 列
- 列标题（第一行）：{headers_str}

识别要求：
1. 第一行必须完全使用上述列标题
2. 确保每行都有 {expected_column_count} 列数据
3. 按照列标题的顺序提取对应的数据
4. 如果图片中某列没有数据，用空字符串表示
5. 输出纯CSV格式，不添加任何额外列"""

            if attempt > 0:
                user_prompt += f"\n\n重要：必须是 {expected_column_count} 列，列标题为：{headers_str}"

            # 调用API
            success, content = self._call_api(image_path, user_prompt)

            if not success:
                if attempt == max_retries - 1:
                    print(f"  [ERROR] API调用失败: {content}")
                continue

            # 清理响应
            csv_text = CSVParser.clean_markdown(content)

            # 解析CSV
            headers, rows, parse_error = CSVParser.parse(csv_text)

            if parse_error:
                if attempt == max_retries - 1:
                    print(f"  [ERROR] CSV解析失败: {parse_error}")
                continue

            # 验证列数
            if len(headers) != expected_column_count:
                if attempt < max_retries - 1:
                    print(f"  [RETRY] 列数不匹配，期望{expected_column_count}列，实际{len(headers)}列，重试中...")
                    continue
                else:
                    print(f"  [ERROR] 列数不匹配: 期望{expected_column_count}列，实际{len(headers)}列")
                    print(f"  识别的表头: {headers}")
                    return None

            # 验证列标题是否匹配（可选，宽松匹配）
            # 这里我们只检查列数，不检查标题内容，因为OCR可能有误差

            # 验证所有行列数一致
            valid = True
            for idx, row in enumerate(rows, start=2):
                if len(row) != expected_column_count:
                    if attempt < max_retries - 1:
                        print(f"  [RETRY] 第{idx}行列数不匹配，重试中...")
                        valid = False
                        break
                    else:
                        print(f"  [ERROR] 第{idx}行列数不匹配")
                        return None

            if not valid:
                continue

            # 成功
            return csv_text

        return None
