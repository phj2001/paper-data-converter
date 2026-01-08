"""
纸质数据转换工具 V3.0
统一列结构版本 - 所有图片使用相同的列格式
"""

import os
import sys
import glob
import time
import argparse
from datetime import datetime
from typing import List, Optional

from ocr_processor import OCRProcessor
from table_processor import CSVParser
from excel_writer import ExcelWriter


class UnifiedConverter:
    """统一列结构的转换器"""

    def __init__(self, api_key: str, endpoint_id: str, input_dir: str,
                 column_headers: List[str]):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.input_dir = input_dir
        self.column_headers = column_headers
        self.column_count = len(column_headers)
        self.ocr_processor = OCRProcessor(api_key, endpoint_id)
        self.log_file = "conversion_log.txt"

    def _log(self, message: str, print_to_console: bool = True):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        if print_to_console:
            try:
                print(message)
            except UnicodeEncodeError:
                ascii_message = message.replace('OK', '[OK]').replace('FAIL', '[FAIL]')
                print(ascii_message)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

    def _scan_images(self) -> List[str]:
        """扫描图片目录"""
        if not os.path.exists(self.input_dir):
            self._log(f"错误: 图片目录 '{self.input_dir}' 不存在")
            return []

        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
        image_files = []

        for ext in extensions:
            pattern = os.path.join(self.input_dir, ext)
            image_files.extend(glob.glob(pattern))

        return sorted(image_files)

    def _process_single_image(self, image_path: str, index: int,
                             total: int) -> Optional[List[List[str]]]:
        """处理单张图片，返回数据行"""
        file_name = os.path.basename(image_path)
        self._log(f"[{index}/{total}] 处理: {file_name}", print_to_console=True)

        try:
            # 调用API，使用指定的列标题
            csv_text = self.ocr_processor.process_image_with_headers(
                image_path,
                self.column_headers,
                max_retries=3
            )

            if not csv_text:
                self._log(f"  [FAIL] 识别失败")
                return None

            # 解析CSV
            headers, rows, parse_error = CSVParser.parse(csv_text)

            if parse_error:
                self._log(f"  [FAIL] CSV解析失败: {parse_error}")
                return None

            # 验证列数
            if len(headers) != self.column_count:
                self._log(f"  [FAIL] 列数不匹配: 期望{self.column_count}列，实际{len(headers)}列")
                self._log(f"       识别的表头: {headers}")
                return None

            # 验证所有行列数一致
            for idx, row in enumerate(rows, start=2):
                if len(row) != self.column_count:
                    self._log(f"  [FAIL] 第{idx}行列数不匹配")
                    return None

            self._log(f"  [OK] 成功: {len(rows)} 行")
            return rows

        except Exception as e:
            self._log(f"  [FAIL] 异常: {str(e)}")
            return None

    def convert(self, output_file: str = "output_data.xlsx") -> bool:
        """执行转换"""
        # 清空日志
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"=== 纸质数据转换日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        self._log("=" * 60)
        self._log("纸质数据转换工具 V3.0 - 统一列结构模式")
        self._log("=" * 60)
        self._log(f"输入目录: {self.input_dir}")
        self._log(f"输出文件: {output_file}")
        self._log(f"列数: {self.column_count}")
        self._log(f"列标题: {', '.join(self.column_headers)}")
        self._log("-" * 60)

        # 扫描图片
        image_files = self._scan_images()

        if not image_files:
            self._log(f"未在 '{self.input_dir}' 中找到图片文件")
            return False

        self._log(f"找到 {len(image_files)} 张图片")
        self._log("")

        # 创建Excel写入器
        excel_writer = ExcelWriter(output_file, self.column_headers)

        # 处理图片
        success_count = 0
        fail_count = 0

        for idx, image_path in enumerate(image_files, 1):
            file_name = os.path.basename(image_path)
            rows = self._process_single_image(image_path, idx, len(image_files))

            if rows:
                excel_writer.add_data(rows, file_name)
                success_count += 1
            else:
                fail_count += 1

            time.sleep(0.5)  # 限流

        # 保存Excel
        self._log("")
        self._log("=" * 60)
        self._log("处理完成")
        self._log("=" * 60)
        self._log(f"成功: {success_count} 张")
        self._log(f"失败: {fail_count} 张")
        self._log(f"总计: {len(image_files)} 张")
        self._log("")

        if success_count > 0:
            self._log("正在保存Excel文件...")
            try:
                excel_writer.save()
                self._log(f"[OK] 成功保存到: {output_file}")
                return True
            except Exception as e:
                self._log(f"[FAIL] 保存失败: {e}")
                return False
        else:
            self._log("没有成功识别的数据")
            return False


def get_column_config_from_user():
    """交互式获取列配置"""
    print("\n" + "=" * 60)
    print(" 列结构配置")
    print("=" * 60)

    while True:
        col_count_input = input("\n请输入表格的总列数: ").strip()

        try:
            col_count = int(col_count_input)
            if col_count <= 0:
                print("列数必须大于0")
                continue
            if col_count > 20:
                print("警告: 列数过多({})，请确认是否正确".format(col_count))
                confirm = input("确认继续? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            break
        except ValueError:
            print("请输入有效的数字")
            continue

    print(f"\n请为 {col_count} 列分别输入列标题（按回车确认每一个）:")
    print("-" * 60)

    headers = []
    for i in range(col_count):
        while True:
            header = input(f"第 {i+1} 列标题: ").strip()

            if not header:
                print("列标题不能为空，请重新输入")
                continue

            headers.append(header)
            break

    # 显示配置摘要
    print("\n" + "=" * 60)
    print(" 配置确认")
    print("=" * 60)
    print(f"总列数: {col_count}")
    print("列标题:")
    for i, header in enumerate(headers, 1):
        print(f"  {i}. {header}")
    print("=" * 60)

    confirm = input("\n确认以上配置正确? (y/n，默认y): ").strip().lower()
    if confirm == 'n':
        return get_column_config_from_user()  # 重新配置

    return headers


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='纸质数据转换工具 V3.0')
    parser.add_argument('--input', '-i', default='images', help='输入目录（默认: images）')
    parser.add_argument('--output', '-o', default='output_data.xlsx', help='输出文件名（默认: output_data.xlsx）')
    parser.add_argument('--no-interactive', action='store_true', help='非交互模式（需要预先配置）')
    parser.add_argument('--headers', '-H', nargs='+', help='预定义的列标题（非交互模式）')

    args = parser.parse_args()

    print("=" * 60)
    print(" 纸质数据转换工具 V3.0")
    print(" 统一列结构 · 一致性输出 · 高精度识别")
    print("=" * 60)

    # 配置参数
    API_KEY_DEFAULT = "f56d7c74-5e13-4a71-8973-d4cebd7aece1"
    ENDPOINT_ID_DEFAULT = "ep-20260104183112-7c7dt"
    INPUT_DIR = args.input

    # 获取API配置
    api_key = API_KEY_DEFAULT or os.environ.get("ARK_API_KEY")
    endpoint_id = ENDPOINT_ID_DEFAULT or os.environ.get("ARK_ENDPOINT_ID")

    # 获取列配置
    if args.no_interactive and args.headers:
        column_headers = args.headers
    else:
        column_headers = get_column_config_from_user()

    print()
    print("-" * 60)
    print("开始处理...")
    print()

    # 执行转换
    converter = UnifiedConverter(api_key, endpoint_id, INPUT_DIR, column_headers)
    success = converter.convert(output_file=args.output)

    print()
    if success:
        print("[OK] 转换完成！")
        print()
        print("输出说明:")
        print("  - 所有数据在同一工作表中")
        print("  - 最后一列为'图片名称'，标识数据来源")
        print(f"  - 共 {len(column_headers)} 个数据列 + 1 个图片名称列")
    else:
        print("[FAIL] 转换失败，请查看 conversion_log.txt 了解详情")

    print()


if __name__ == "__main__":
    main()
