"""
表格数据处理模块
提供CSV解析、数据结构定义和表格结构分析功能
"""

import re
import csv
from io import StringIO
from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TableData:
    """表格数据结构"""
    file_name: str
    headers: List[str]
    rows: List[List[str]]
    column_count: int
    raw_csv: str = ""


class CSVParser:
    """CSV解析器"""

    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        清理Markdown代码块标记
        """
        text = text.strip()

        # 移除 ```csv 和 ``` 标记
        if text.startswith("```"):
            # 找到第一个换行符
            first_newline = text.find("\n")
            if first_newline > 0:
                text = text[first_newline:].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text

    @staticmethod
    def parse(csv_text: str) -> Tuple[List[str], List[List[str]], Optional[str]]:
        """
        解析CSV文本

        返回: (headers, rows, error_message)
        """
        if not csv_text:
            return [], [], "CSV文本为空"

        lines = csv_text.strip().split("\n")

        if not lines:
            return [], [], "CSV没有行"

        # 使用csv模块正确解析（处理引号内的逗号）
        try:
            reader = csv.reader(StringIO(csv_text))
            rows_list = list(reader)
        except Exception as e:
            return [], [], f"CSV解析异常: {str(e)}"

        if not rows_list:
            return [], [], "CSV解析后没有数据"

        headers = rows_list[0]
        data_rows = rows_list[1:]

        # 过滤空行
        data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]

        return headers, data_rows, None


class TableStructureAnalyzer:
    """表格结构分析器"""

    @staticmethod
    def validate_structure(table_data: TableData) -> Tuple[bool, Optional[str]]:
        """
        验证表格结构

        返回: (is_valid, error_message)
        """
        if not table_data.headers:
            return False, "表头为空"

        expected_columns = len(table_data.headers)

        if table_data.column_count != expected_columns:
            return False, f"列数不匹配: headers={expected_columns}, column_count={table_data.column_count}"

        # 验证所有行的列数一致
        for idx, row in enumerate(table_data.rows, start=2):
            if len(row) != expected_columns:
                return False, f"第{idx}行列数({len(row)})与表头({expected_columns})不一致"

        return True, None
