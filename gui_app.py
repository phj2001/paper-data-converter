"""
纸质数据转换工具 - 图形界面版本
使用CustomTkinter创建现代化UI
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import queue
from pathlib import Path
from typing import List, Optional

# 导入后端处理模块
from ocr_processor import OCRProcessor
from table_processor import CSVParser
from excel_writer import ExcelWriter


# 配置CustomTkinter外观
ctk.set_appearance_mode("light")  # 可选: "light", "dark", "system"
ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"


class ExcelWriterGUI(ExcelWriter):
    """Excel写入器（GUI版本）- 继承自共享的ExcelWriter"""

    def __init__(self, output_file: str, headers: List[str], progress_callback=None):
        super().__init__(output_file, headers, progress_callback)


class PaperConverterGUI:
    """纸质数据转换工具 - 主界面"""

    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("纸质数据转换工具 V3.0")
        self.app.geometry("1000x700")

        # 配置参数
        self.api_key = "f56d7c74-5e13-4a71-8973-d4cebd7aece1"
        self.endpoint_id = "ep-20260104183112-7c7dt"

        # 数据
        self.image_folder = ctk.StringVar(value="")
        self.output_file = ctk.StringVar(value="output_data.xlsx")
        self.column_count = ctk.StringVar(value="4")
        self.column_headers = []
        self.is_processing = False

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_container = ctk.CTkFrame(self.app, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题
        title_label = ctk.CTkLabel(
            main_container,
            text="纸质数据转换工具",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = ctk.CTkLabel(
            main_container,
            text="V3.0 - 智能OCR识别 · 统一列结构 · 高精度提取",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 20))

        # 左右分栏
        content_frame = ctk.CTkFrame(main_container, fg_color=("gray95", "gray25"))
        content_frame.pack(fill="both", expand=True)

        # 左侧：配置区域
        left_frame = ctk.CTkFrame(content_frame, width=450)
        left_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        left_frame.pack_propagate(False)

        # 右侧：日志区域
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        self.create_config_panel(left_frame)
        self.create_log_panel(right_frame)

        # 底部按钮区域
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=(20, 0))

        self.start_button = ctk.CTkButton(
            button_frame,
            text="开始转换",
            command=self.start_conversion,
            width=200,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.start_button.pack()

    def create_config_panel(self, parent):
        """创建配置面板"""
        # 标题
        config_title = ctk.CTkLabel(
            parent,
            text="配置选项",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        config_title.pack(pady=(20, 15))

        # 1. 文件夹选择
        folder_frame = ctk.CTkFrame(parent, fg_color="transparent")
        folder_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            folder_frame,
            text="图片文件夹：",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        folder_input = ctk.CTkFrame(folder_frame)
        folder_input.pack(fill="x", pady=(5, 0))

        folder_entry = ctk.CTkEntry(
            folder_input,
            textvariable=self.image_folder,
            placeholder_text="选择包含图片的文件夹..."
        )
        folder_entry.pack(side="left", fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            folder_input,
            text="浏览",
            command=self.browse_folder,
            width=80
        )
        browse_btn.pack(side="left", padx=(10, 0))

        # 2. 输出文件名
        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            output_frame,
            text="输出文件名：",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        output_entry = ctk.CTkEntry(
            output_frame,
            textvariable=self.output_file,
            placeholder_text="output_data.xlsx"
        )
        output_entry.pack(fill="x", pady=(5, 0))

        # 3. 列数配置
        column_frame = ctk.CTkFrame(parent, fg_color="transparent")
        column_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            column_frame,
            text="数据列数：",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        column_entry = ctk.CTkEntry(
            column_frame,
            textvariable=self.column_count,
            placeholder_text="4"
        )
        column_entry.pack(fill="x", pady=(5, 0))

        # 配置列标题按钮
        config_headers_btn = ctk.CTkButton(
            parent,
            text="配置列标题",
            command=self.configure_headers,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        config_headers_btn.pack(fill="x", padx=15, pady=15)

        # 列标题预览
        self.headers_preview = ctk.CTkTextbox(
            parent,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.headers_preview.pack(fill="x", padx=15, pady=(0, 15))
        self.headers_preview.insert("1.0", "列标题预览：\n尚未配置")
        self.headers_preview.configure(state="disabled")

        # 文件信息
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 20))

        self.file_count_label = ctk.CTkLabel(
            info_frame,
            text="待处理文件：0 张",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_count_label.pack(anchor="w")

    def create_log_panel(self, parent):
        """创建日志面板"""
        # 标题
        log_title = ctk.CTkLabel(
            parent,
            text="处理日志",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.pack(pady=(15, 10))

        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(parent)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

        # 状态标签
        self.status_label = ctk.CTkLabel(
            parent,
            text="就绪",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=(0, 15))

    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_folder.set(folder)
            # 统计图片数量
            image_count = self.count_images(folder)
            self.file_count_label.configure(text=f"待处理文件：{image_count} 张")
            self.log(f"已选择文件夹: {folder}")
            self.log(f"找到 {image_count} 张图片")

    def count_images(self, folder: str) -> int:
        """统计图片数量"""
        if not os.path.exists(folder):
            return 0

        import glob as glob_module
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
        count = 0

        for ext in extensions:
            pattern = os.path.join(folder, ext)
            count += len(glob_module.glob(pattern))

        return count

    def configure_headers(self):
        """配置列标题对话框"""
        try:
            col_count = int(self.column_count.get())
            if col_count <= 0 or col_count > 20:
                messagebox.showerror("错误", "列数必须在1-20之间")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的列数")
            return

        # 创建配置对话框
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("配置列标题")
        dialog.geometry("500x600")
        dialog.transient(self.app)
        dialog.grab_set()

        # 标题
        title = ctk.CTkLabel(
            dialog,
            text=f"配置 {col_count} 列的标题",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)

        # 滚动框架
        scroll_frame = ctk.CTkScrollableFrame(dialog, label_text="列标题")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        entries = []
        for i in range(col_count):
            row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)

            label = ctk.CTkLabel(row, text=f"第 {i+1} 列：", width=80, anchor="w")
            label.pack(side="left")

            entry = ctk.CTkEntry(row, placeholder_text=f"输入第{i+1}列的标题")
            if i < len(self.column_headers):
                entry.insert(0, self.column_headers[i])
            entry.pack(side="left", fill="x", expand=True)
            entries.append(entry)

        # 按钮区域
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        def save_headers():
            headers = []
            for entry in entries:
                value = entry.get().strip()
                if not value:
                    messagebox.showerror("错误", "所有列标题都不能为空")
                    return
                headers.append(value)

            self.column_headers = headers
            self.update_headers_preview()
            dialog.destroy()

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=100,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="left", padx=10)

        save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            command=save_headers,
            width=100
        )
        save_btn.pack(side="left", padx=10)

    def update_headers_preview(self):
        """更新列标题预览"""
        self.headers_preview.configure(state="normal")
        self.headers_preview.delete("1.0", "end")

        preview = "列标题预览：\n\n"
        for i, header in enumerate(self.column_headers, 1):
            preview += f"列 {i}: {header}\n"

        self.headers_preview.insert("1.0", preview)
        self.headers_preview.configure(state="disabled")

    def log(self, message: str):
        """添加日志"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.app.update_idletasks()

    def update_progress(self, value: float, status: str = ""):
        """更新进度"""
        self.progress_bar.set(value)
        if status:
            self.status_label.configure(text=status)
        self.app.update_idletasks()

    def start_conversion(self):
        """开始转换"""
        # 验证配置
        if not self.image_folder.get():
            messagebox.showerror("错误", "请先选择图片文件夹")
            return

        if not os.path.exists(self.image_folder.get()):
            messagebox.showerror("错误", "选择的文件夹不存在")
            return

        try:
            col_count = int(self.column_count.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的列数")
            return

        if len(self.column_headers) != col_count:
            messagebox.showerror("错误", f"列标题数量不匹配！\n需要配置 {col_count} 列标题")
            return

        if not self.output_file.get():
            messagebox.showerror("错误", "请输入输出文件名")
            return

        # 禁用开始按钮
        self.start_button.configure(state="disabled", text="处理中...")
        self.is_processing = True

        # 清空日志
        self.log_text.delete("1.0", "end")
        self.log("=" * 50)
        self.log("开始处理...")
        self.log("=" * 50)

        # 在后台线程中处理
        thread = threading.Thread(
            target=self.process_images,
            daemon=True
        )
        thread.start()

    def process_images(self):
        """处理图片（后台线程）"""
        try:
            import glob
            import time

            folder = self.image_folder.get()
            col_headers = self.column_headers
            api_key = self.api_key
            endpoint_id = self.endpoint_id
            output_file = self.output_file.get()

            # 扫描图片
            extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
            image_files = []

            for ext in extensions:
                pattern = os.path.join(folder, ext)
                image_files.extend(glob.glob(pattern))

            image_files = sorted(image_files)

            if not image_files:
                self.app.after(0, lambda: messagebox.showerror("错误", "未找到图片文件"))
                self.reset_ui()
                return

            total = len(image_files)
            self.log(f"找到 {total} 张图片")
            self.log(f"列数: {len(col_headers)}")
            self.log(f"列标题: {', '.join(col_headers)}")
            self.log("-" * 50)

            # 创建OCR处理器
            ocr_processor = OCRProcessor(api_key, endpoint_id)

            # 创建Excel写入器
            excel_writer = ExcelWriterGUI(output_file, col_headers)

            # 处理每张图片
            success_count = 0
            fail_count = 0

            for idx, image_path in enumerate(image_files, 1):
                file_name = os.path.basename(image_path)
                self.log(f"[{idx}/{total}] 处理: {file_name}")

                try:
                    # 调用OCR
                    csv_text = ocr_processor.process_image_with_headers(
                        image_path,
                        col_headers,
                        max_retries=3
                    )

                    if not csv_text:
                        self.log(f"  [FAIL] 识别失败")
                        fail_count += 1
                    else:
                        # 解析CSV
                        headers, rows, parse_error = CSVParser.parse(csv_text)

                        if parse_error:
                            self.log(f"  [FAIL] CSV解析失败: {parse_error}")
                            fail_count += 1
                        else:
                            # 验证列数
                            if len(headers) != len(col_headers):
                                self.log(f"  [FAIL] 列数不匹配")
                                fail_count += 1
                            else:
                                excel_writer.add_data(rows, file_name)
                                self.log(f"  [OK] 成功: {len(rows)} 行")
                                success_count += 1

                except Exception as e:
                    self.log(f"  [FAIL] 异常: {str(e)}")
                    fail_count += 1

                # 更新进度
                progress = idx / total
                self.app.after(0, lambda p=progress, s=f"处理中... {idx}/{total}":
                              self.update_progress(p, s))

                time.sleep(0.5)  # 限流

            # 保存Excel
            self.log("")
            self.log("=" * 50)
            self.log("处理完成")
            self.log("=" * 50)
            self.log(f"成功: {success_count} 张")
            self.log(f"失败: {fail_count} 张")
            self.log(f"总计: {total} 张")
            self.log("")

            if success_count > 0:
                self.log("正在保存Excel文件...")
                excel_writer.save()
                self.log(f"[OK] 已保存到: {output_file}")

                # 在主线程中显示成功消息
                self.app.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"转换完成！\n\n成功: {success_count} 张\n失败: {fail_count} 张\n\n文件已保存到:\n{output_file}"
                ))
            else:
                self.app.after(0, lambda: messagebox.showerror(
                    "失败",
                    "没有成功识别的数据，请查看日志了解详情"
                ))

        except Exception as e:
            self.log(f"[ERROR] 处理异常: {str(e)}")
            self.app.after(0, lambda: messagebox.showerror("错误", f"处理过程中发生错误:\n{str(e)}"))

        finally:
            # 重置UI
            self.app.after(0, self.reset_ui)

    def reset_ui(self):
        """重置UI状态"""
        self.start_button.configure(state="normal", text="开始转换")
        self.is_processing = False
        self.update_progress(0, "就绪")

    def run(self):
        """运行应用"""
        self.app.mainloop()


def main():
    """主入口"""
    app = PaperConverterGUI()
    app.run()


if __name__ == "__main__":
    main()
