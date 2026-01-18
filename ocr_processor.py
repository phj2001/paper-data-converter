"""
OCR处理器 - 负责与大模型API交互
支持多种主流大模型的统一调用接口
提供增强的识别能力和多重重试机制
"""

import os
import json
import base64
import requests
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, List
from table_processor import TableData, CSVParser, TableStructureAnalyzer


@dataclass
class PromptProfile:
    """Prompt profile derived from a trial image."""
    headers: List[str]
    column_count: int
    column_notes: List[str]
    row_rules: List[str]
    output_rules: List[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptProfile":
        return cls(
            headers=data.get("headers", []),
            column_count=int(data.get("column_count", 0)),
            column_notes=data.get("column_notes", []),
            row_rules=data.get("row_rules", []),
            output_rules=data.get("output_rules", []),
        )


PROFILE_SYSTEM_PROMPT = """ä½ æ˜¯ä¸“ä¸šçš„çº¸è´¨è¡¨æ ¼ç»“æž„åˆ†æžä¸“å®¶ã€?
ä»»åŠ¡ï¼šåˆ†æžå›¾ç‰‡ä¸­çš„ä¸»è¡¨æ ¼ç»“æž„ï¼Œè¿”å›žä¸¥æ ¼JSONã€‚
è¦æ±‚ï¼š
1. åªè¿”å›žJSONï¼Œä¸è¦Markdownï¼Œä¸è¦è§£é‡Šå­—ç¬¦ä¸²ã€‚
2. JSONå¿…é¡»åŒ…å« keys: headers, column_count, column_notes, row_rules, output_rulesã€‚
3. headersä¸ºä»Žå·¦åˆ°å³çš„åˆ—æ ‡é¢˜æ•°ç»„ï¼Œcolumn_countç­‰äºŽheadersé•¿åº¦ã€‚
4. column_notesä¸ºæ•°ç»„ï¼Œæ ¼å¼ï¼š\"åˆ—å: è¯´æ˜Ž\"ã€‚
5. row_rules/ output_rulesä¸ºæ•°ç»„ï¼Œç®€æ´ç›´è§‚ï¼Œä¸åšæŽ¨æ–­ã€‚"""


PROFILE_SYSTEM_PROMPT = """你是专业的纸质表格结构分析专家。
你的任务是从图片中抽取表格结构，并输出严格的 JSON。
要求：
1) 只输出 JSON，不要包含 Markdown 或任何额外文字。
2) JSON 必须包含键：headers, column_count, column_notes, row_rules, output_rules。
3) headers 按从左到右顺序列出表头。
4) column_count 必须等于 headers 的长度。
5) column_notes 用于描述每列的内容和格式要点，简洁即可。
6) row_rules 描述行级规则（如合并单元格、空行、序号、日期格式等）。
7) output_rules 描述 CSV 输出规则（如英文逗号分隔、双引号包裹、禁止 Markdown 等）。"""

PROFILE_FEEDBACK_SYSTEM_PROMPT = """你是表格识别提示词的优化专家。
你将收到表格图片、现有的提示词画像 JSON，以及用户的自然语言反馈。
请在保证贴合图片内容的前提下，调整提示词画像以满足用户意图。
规则：
1) 只输出 JSON，不要附加其他文字。
2) 键必须是：headers, column_count, column_notes, row_rules, output_rules。
3) column_count 必须等于 headers 的长度。
4) 如反馈明确指定列数或列名，优先遵循。
5) 规则要简洁、可执行，便于输出 CSV。"""

class OCRProcessor:
    """OCR处理器 - 统一的大模型调用接口"""

    # 系统提示词 - 专业的表格识别指令
    SYSTEM_PROMPT = """你是专业的纸质表格识别专家。

核心任务：将图片中的表格转换为准确的CSV格式。

严格规则：
1. 只识别图片中的主数据表格，完全忽略标题、页眉、页脚、页码、说明文字
2. 第一行必须是表格的表头（列标题），从第二行开始是数据
3. 表格有多少列，输出的CSV就必须有多少列，所有行列数必须完全一致
4. 绝对禁止添加任何额外的列（如序号、行号、来源等）
5. 不做任何翻译、解释、注释
6. 不输出Markdown代码块标记，只输出纯CSV文本
7. 使用英文逗号(,)作为分隔符
8. 如果单元格内容包含逗号、引号或换行，用双引号包裹该单元格

**重要 - 空白单元格处理：**
- 只有单元格确实完全空白、没有任何内容时，才留空
- 如果有任何文字、数字、符号，都必须识别出来
- 即使内容模糊、字迹较轻，也要尽可能识别
- 对数字和符号要特别仔细，不要遗漏
- 表格边框、分隔线不能算作单元格内容
- 空白单元格直接用逗号跳过（如：列1,,列3）

**识别精度要求：**
- 逐个单元格仔细识别，不要遗漏任何内容
- 注意数字中的小数点、负号等
- 注意表格中的符号、单位、标记
- 保持原始格式，不要删除或修改内容

输出格式要求：
- 第一行：表头（列标题）
- 后续行：数据行
- 所有行必须有相同的列数
- 纯CSV文本，无其他内容"""

    def __init__(self, config):
        """
        初始化OCR处理器

        Args:
            config: LLMConfig配置对象（来自llm_config模块）
        """
        self.config = config
        self.api_key = config.api_key
        self.model = config.model
        self.api_url = config.get_api_url()
        self.provider = config.provider
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout

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

    def _build_payload_openai(self, user_prompt: str, base64_image: str, mime_type: str,
                              system_prompt: Optional[str] = None) -> dict:
        """构建OpenAI兼容格式的payload"""
        active_system_prompt = system_prompt or self.SYSTEM_PROMPT
        return {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": active_system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": self.max_tokens
        }

    def _build_payload_anthropic(self, user_prompt: str, base64_image: str, mime_type: str,
                                 system_prompt: Optional[str] = None) -> dict:
        """构建Anthropic格式的payload"""
        active_system_prompt = system_prompt or self.SYSTEM_PROMPT
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system": active_system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }

    def _get_headers(self) -> dict:
        """根据不同提供商获取请求头"""
        headers = {"Content-Type": "application/json"}

        if self.provider == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            # OpenAI兼容格式（豆包、通义千问、智谱等）
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _parse_response(self, response_data: dict) -> Tuple[bool, str]:
        """根据不同提供商解析响应"""
        try:
            if self.provider == "anthropic":
                # Anthropic格式
                if 'content' in response_data and len(response_data['content']) > 0:
                    content = response_data['content'][0].get('text', '')
                    return True, content
                else:
                    return False, f"API返回结构异常: {response_data}"
            else:
                # OpenAI兼容格式
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content']
                    return True, content
                else:
                    return False, f"API返回结构异常: {response_data}"
        except Exception as e:
            return False, f"解析响应失败: {str(e)}"

    def _call_api(self, image_path: str, user_prompt: str,
                  system_prompt: Optional[str] = None) -> Tuple[bool, str]:
        """
        调用大模型API（支持多种提供商）

        返回: (success, response_content)
        """
        try:
            base64_image = self._encode_image(image_path)
            mime_type = self._get_mime_type(image_path)

            headers = self._get_headers()

            # 根据提供商构建不同的payload
            if self.provider == "anthropic":
                payload = self._build_payload_anthropic(
                    user_prompt,
                    base64_image,
                    mime_type,
                    system_prompt=system_prompt
                )
            else:
                # OpenAI兼容格式
                payload = self._build_payload_openai(
                    user_prompt,
                    base64_image,
                    mime_type,
                    system_prompt=system_prompt
                )

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return self._parse_response(result)
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return False, f"请求超时（{self.timeout}秒）"
        except Exception as e:
            return False, f"异常: {str(e)}"

    def _build_profile_user_prompt(self) -> str:
        """构建试运行结构分析的提示词"""
        return """请分析图片中的主表格结构，并仅返回严格JSON：
{
  "headers": ["列1", "列2"],
  "column_count": 2,
  "column_notes": ["列1: 说明", "列2: 说明"],
  "row_rules": ["规则1", "规则2"],
  "output_rules": ["规则1", "规则2"]
}
要求：
1. headers按从左到右顺序，column_count必须等于headers长度。
2. column_notes用于描述该列的格式或内容要点，不要过长。
3. row_rules描述行/记录的组织规律（如合并单元格、空行、序号、日期格式等）。
4. output_rules描述CSV输出规则（例如用英文逗号分隔、双引号包裹、禁止Markdown等）。
5. 不要输出除JSON以外的任何内容。"""

    def _build_feedback_profile_prompt(self, base_profile: PromptProfile, feedback_text: str) -> str:
        """Build a prompt to refine a profile based on user feedback."""
        base_json = json.dumps(base_profile.to_dict(), ensure_ascii=False, indent=2)
        feedback = feedback_text.strip()
        return f"""Current prompt profile JSON:
{base_json}

User feedback (natural language):
{feedback}

Please revise the JSON profile to satisfy the feedback while matching the image."""

    def _parse_profile_response(self, content: str) -> Optional[PromptProfile]:
        """解析试运行返回的JSON结构"""
        cleaned = CSVParser.clean_markdown(content).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        json_text = cleaned[start:end + 1]
        try:
            data = json.loads(json_text)
        except Exception:
            return None

        headers = data.get("headers") or []
        if not isinstance(headers, list) or not headers:
            return None

        column_count = int(data.get("column_count") or len(headers))
        if column_count != len(headers):
            return None

        column_notes = data.get("column_notes") or []
        row_rules = data.get("row_rules") or []
        output_rules = data.get("output_rules") or []

        return PromptProfile(
            headers=headers,
            column_count=column_count,
            column_notes=column_notes,
            row_rules=row_rules,
            output_rules=output_rules
        )

    def _build_user_prompt_from_profile(self, profile: PromptProfile, retry_note: str = "") -> str:
        """根据试运行结构生成动态提示词"""
        headers_str = " | ".join(profile.headers)
        notes_str = "\n".join(profile.column_notes) if profile.column_notes else "（无）"
        row_rules = "\n".join(profile.row_rules) if profile.row_rules else "（无）"
        output_rules = "\n".join(profile.output_rules) if profile.output_rules else "（无）"

        prompt = f"""请严格识别图片中的主表格数据，并输出CSV文本。
列数：{profile.column_count} 列
列标题（第一行必须严格一致）：{headers_str}

列说明：
{notes_str}

行/记录规则：
{row_rules}

输出规则：
{output_rules}

强制要求：
1. 只输出CSV文本，不要Markdown，不要解释。
2. 使用英文逗号分隔；如单元格含逗号/引号/换行，用双引号包裹。
3. 所有行列数必须与表头一致，不得增删列。
4. 保持原始内容，不翻译、不推断。"""

        if retry_note:
            prompt += f"\n\n重试要求：{retry_note}"

        return prompt

    def generate_prompt_profile(self, image_path: str, max_retries: int = 2) -> Optional[PromptProfile]:
        """基于试运行图片生成结构化PromptProfile"""
        user_prompt = self._build_profile_user_prompt()

        for attempt in range(max_retries):
            success, content = self._call_api(
                image_path,
                user_prompt,
                system_prompt=PROFILE_SYSTEM_PROMPT
            )
            if not success:
                if attempt == max_retries - 1:
                    print(f"[ERROR] Profile generation failed: {content}")
                continue

            profile = self._parse_profile_response(content)
            if profile:
                return profile

        return None

    def refine_prompt_profile(
        self,
        image_path: str,
        base_profile: PromptProfile,
        feedback_text: str,
        max_retries: int = 2
    ) -> Optional[PromptProfile]:
        """Refine an existing prompt profile using user feedback."""
        if not feedback_text or not feedback_text.strip():
            return base_profile

        user_prompt = self._build_feedback_profile_prompt(base_profile, feedback_text)
        for attempt in range(max_retries):
            success, content = self._call_api(
                image_path,
                user_prompt,
                system_prompt=PROFILE_FEEDBACK_SYSTEM_PROMPT
            )
            if not success:
                if attempt == max_retries - 1:
                    print(f"[ERROR] Profile refine failed: {content}")
                continue

            profile = self._parse_profile_response(content)
            if profile:
                return profile

        return None

    def process_image_with_profile(self, image_path: str, profile: PromptProfile,
                                   max_retries: int = 3) -> Optional[str]:
        """
        使用试运行生成的结构化提示词识别图片
        Returns:
            CSV文本或None
        """
        for attempt in range(max_retries):
            retry_note = ""
            if attempt > 0:
                retry_note = "请严格按照列数与列标题输出，保持每行列数一致。"

            user_prompt = self._build_user_prompt_from_profile(profile, retry_note=retry_note)
            success, content = self._call_api(image_path, user_prompt)

            if not success:
                if attempt == max_retries - 1:
                    print(f"  [ERROR] API调用失败: {content}")
                continue

            csv_text = CSVParser.clean_markdown(content)
            headers, rows, parse_error = CSVParser.parse(csv_text)

            if parse_error:
                if attempt == max_retries - 1:
                    print(f"  [ERROR] CSV解析失败: {parse_error}")
                continue

            if len(headers) != profile.column_count:
                if attempt < max_retries - 1:
                    print(f"  [RETRY] 列数不匹配，期望{profile.column_count}列，实际{len(headers)}列")
                    continue
                return None

            for idx, row in enumerate(rows, start=2):
                if len(row) != profile.column_count:
                    if attempt < max_retries - 1:
                        print(f"  [RETRY] 第{idx}行列数不匹配，重试中...")
                        break
                    return None

            return csv_text

        return None

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

任务目标：将图片中的数据原封不动地提取为CSV格式。

输出要求：
- 列数：{expected_column_count} 列
- 列标题（第一行）：{headers_str}

数据提取规则：
1. 从左到右扫描图片，识别所有数据列
2. 根据数据之间的视觉间隙划分列（手写数据可能没有网格线）
3. 将识别出的每一列数据，按顺序填入对应的列标题下
4. 第一行输出指定的列标题
5. 从第二行开始，按行输出数据

**提取原则（核心）：**
- 看到什么提取什么，不做任何理解、判断或解释
- 不要猜测或推断数据含义
- 不要修改、翻译或美化原始内容
- 纯粹的数据搬运：图片中的内容 → CSV格式
- 确保每一列都被识别到，按从左到右的顺序

**精度要求：**
- 逐个单元格仔细识别
- 即使内容模糊、字迹较轻，也要尽可能识别
- 数字、符号要特别准确（小数点、负号、%等）
- 只有单元格完全空白时才留空
- 每一行都必须有 {expected_column_count} 列数据

输出格式：纯CSV文本，不添加任何标记或说明"""

            if attempt > 0:
                user_prompt += f"\n\n重试：必须是 {expected_column_count} 列，列标题为：{headers_str}。\n提醒：\n1)从左到右识别所有列\n2)每行必须有 {expected_column_count} 列\n3)不要遗漏任何列的数据"

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
