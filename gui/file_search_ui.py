import tkinter as tk
from tkinter import ttk, filedialog

class FileSearchUI:
    def __init__(self, root, app):
        self.app = app
        self.root = root
        self.root.title("文件搜索工具")
        self.create_widgets()

    def create_widgets(self):
        # 顶部控制栏
        self.control_frame = ttk.Frame(self.root, padding=10)
        self.control_frame.grid(row=0, column=0, sticky='nsew')
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.columnconfigure(1, weight=1)
        self.control_frame.columnconfigure(2, weight=1)

        # 目录选择
        ttk.Label(self.control_frame, text="搜索目录:").grid(row=0, column=0, sticky='w')
        self.dir_entry = ttk.Entry(self.control_frame, width=40)
        self.dir_entry.grid(row=0, column=1, padx=5)
        self.choose_btn = ttk.Button(self.control_frame, text="选择", command=lambda: self.app.choose_directory())
        self.choose_btn.grid(row=0, column=2)

        # 关键字输入
        ttk.Label(self.control_frame, text="关键字:").grid(row=1, column=0, sticky='w', pady=5)
        self.keyword_entry = ttk.Entry(self.control_frame, width=40)
        self.keyword_entry.grid(row=1, column=1, padx=5)

        # 搜索按钮
        self.search_btn = ttk.Button(self.control_frame, text="开始搜索", command=lambda: self.app.perform_search())
        self.search_btn.grid(row=1, column=2)

        # 暂停按钮
        self.stop_button = ttk.Button(self.control_frame, text="暂停搜索", command=lambda: self.app.stop_searching())
        self.stop_button.grid(row=1, column=3, padx=5)

        # 结果显示列表
        self.result_tree = ttk.Treeview(self.root, columns=('file', 'path'), show='headings')
        self.result_tree.heading('file', text='文件名')
        self.result_tree.heading('path', text='路径')
        self.result_tree.column('file', width=200)
        self.result_tree.column('path', width=400)
        self.result_tree.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        # 绑定双击事件
        self.result_tree.bind('<Double-1>', lambda event: self.app.open_selected_file(event))

        # 进度显示标签
        self.progress_label = ttk.Label(self.root, text="", padding=5)
        self.progress_label.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        # 布局配置
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)