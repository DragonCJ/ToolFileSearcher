import tkinter as tk
from tkinter import ttk, filedialog
import os
import subprocess
import shutil
import threading
from tkinter import messagebox

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.directory = ''  # 初始化目录属性
        
        # 初始化UI模块
        from gui.file_search_ui import FileSearchUI
        self.ui = FileSearchUI(self.root, self)
        self.search_results = []
        self.is_searching = False
        self.stop_search = False

    def choose_directory(self):
        directory = os.path.normpath(filedialog.askdirectory())
        if directory:
            self.ui.dir_entry.delete(0, tk.END)
            self.ui.dir_entry.insert(0, directory)

    def select_directory(self):
        selected_dir = filedialog.askdirectory()
        print(f'[DEBUG] 新选择目录: {selected_dir}')
        if selected_dir and os.path.exists(selected_dir):
            self.directory = os.path.normpath(selected_dir)
            self.ui.dir_entry.delete(0, tk.END)
            self.ui.dir_entry.insert(0, self.directory)
        else:
            self.directory = ''
            messagebox.showwarning('路径无效', '所选目录不存在或不可访问')    
    def perform_search(self):
        keyword = self.ui.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入关键字")
            return
                
        directory = self.ui.dir_entry.get().strip()
        if not directory or not os.path.exists(directory):
            messagebox.showwarning("警告", "请选择有效目录")
            return
        # 清空之前的搜索结果
        self.search_results = []
        # 清空临时目录
        self.clear_temp_files()
            
        # 禁用搜索相关按钮
        self.ui.keyword_entry.config(state='disabled')
        self.ui.dir_entry.config(state='disabled')
        self.ui.stop_button.config(state='normal')
        
        # 在后台线程中执行搜索
        search_thread = threading.Thread(
            target=self._perform_search_task,
            args=(directory, keyword),
            daemon=True
        )
        search_thread.start()
    
    def _perform_search_task(self, directory, keyword):
        from biz.search_logic import SearchLogic
        
        self.search_logic = SearchLogic()
        self.search_logic.stop_search = False
        
        def progress_callback(searched, total):
            self.searched_files = searched
            self.total_files = total
            self.root.after(0, self._update_progress_label)
            
        def result_callback(filepath):
            self.search_results.append(filepath)
            self.root.after(0, self._update_ui)
            
        self.search_results = self.search_logic.perform_search(
            directory, 
            keyword,
            progress_callback=progress_callback,
            result_callback=result_callback
        )
        
        self.is_searching = False
        self.root.after(0, self._finish_search)

    def _update_progress_label(self):
        if hasattr(self, 'ui') and hasattr(self.ui, 'progress_label'):
            progress_text = f"已搜索 {self.searched_files}/{self.total_files} 个文件"
            self.ui.progress_label.config(text=progress_text)
    
    def _update_ui(self):
        self.toggle_path_display()
        self.root.update()
    
    def _finish_search(self):
        # 重新启用搜索相关按钮
        self.ui.keyword_entry.config(state='normal')
        self.ui.dir_entry.config(state='normal')
        self.ui.stop_button.config(state='disabled')
        
        if not self.stop_search:
            if not self.search_results:
                messagebox.showwarning("未找到", "未搜索到匹配文件")
            else:
                messagebox.showinfo("搜索完成", f"已找到 {len(self.search_results)} 个文件")
        else:
            messagebox.showinfo("搜索已停止", f"已找到 {len(self.search_results)} 个文件")
        
    def toggle_path_display(self):
        # 安全检查：确保UI组件已初始化
        if hasattr(self, 'ui') and hasattr(self.ui, 'result_tree'):
            self.ui.result_tree.delete(*self.ui.result_tree.get_children())
            for path in self.search_results:
                # 规范化路径分隔符以适配当前系统
                normalized_path = os.path.normpath(path)
                display_name = os.path.basename(normalized_path)
                self.ui.result_tree.insert('', 'end', values=(display_name, normalized_path))

    def start_search(self):
        # 清空之前的搜索结果
        self.search_results = []
        self.result_tree.delete(*self.result_tree.get_children())
        # 启动新搜索（假设原搜索触发逻辑在此处）
        self.is_searching = True
        self.stop_search = False
        threading.Thread(target=self.search_class_content, daemon=True).start()
            
    def stop_searching(self):
        if self.is_searching:
            self.stop_search = True
            # 暂停时立即显示当前结果
            self.toggle_path_display()
            self.root.update()

    def open_selected_file(self, event):
        selected_item = self.ui.result_tree.selection()
        if selected_item:
            file_path = self.ui.result_tree.item(selected_item[0])['values'][1]
            try:
                # 仅class文件需要检查反编译文件
                if file_path.endswith('.class'):
                    # 提取基础类名（去除包路径和.class后缀）
                    class_name = os.path.splitext(os.path.basename(file_path))[0]
                    # 递归搜索temp_decompiled目录下的所有子目录
                    java_file_path = None
                    # 使用与反编译相同的绝对路径搜索temp_decompiled目录
                    temp_decompiled_dir = os.path.join(os.path.dirname(__file__), 'temp_decompiled')
                    java_file_path = None
                    # 先尝试在temp_decompiled目录中查找对应的.java文件
                    for root, dirs, files in os.walk(temp_decompiled_dir):
                        if f'{class_name}.java' in files:
                            java_file_path = os.path.join(root, f'{class_name}.java')
                            break
                    
                    # 如果找到反编译文件，优先打开它
                    if java_file_path and os.path.exists(java_file_path):
                        file_path = java_file_path
                
                # 打开文件（支持不同系统）
                if os.name == 'nt':
                    os.startfile(file_path)
                else:
                    subprocess.run(['xdg-open', file_path])
            except Exception as e:
                tk.messagebox.showerror("错误", f"无法打开文件: {str(e)}")    
    def search_class_content(self, filepath, keyword):
        return self.search_logic.search_class_content(filepath, keyword)
    
    # 开始搜索前先清理临时文件
    def clear_temp_files(self):
        if os.path.exists('temp_decompiled'):
            shutil.rmtree('temp_decompiled')
        if os.path.exists('log'):
            shutil.rmtree('log')
if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = FileSearchApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror('致命错误', f'程序异常: {str(e)}')