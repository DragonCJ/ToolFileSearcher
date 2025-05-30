import os
import subprocess
import threading
from datetime import datetime

class SearchLogic:
    def __init__(self):
        self.is_searching = False
        self.stop_search = False
        self.search_results = []
        self.searched_files = 0
        self.total_files = 0

    def perform_search(self, directory, keyword, progress_callback=None, result_callback=None):
        self.is_searching = True
        self.stop_search = False
        self.search_results = []
        self.searched_files = 0
        
        # 预扫描获取总文件数
        all_files = []
        for root, dirs, files in os.walk(directory):
            all_files.extend([os.path.join(root, f) for f in files])
        self.total_files = len(all_files)
        
        # 初始化日志
        log_dir = 'log'
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_scan.log")
        
        for filepath in all_files:
            if self.stop_search:
                break
                
            self.searched_files += 1
            if progress_callback:
                progress_callback(self.searched_files, self.total_files)
            
            # 记录日志
            try:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"正在扫描: {filepath}\n")
            except Exception as e:
                print(f"写入日志失败: {e}")
            
            # 文件名匹配
            filename = os.path.basename(filepath)
            if keyword.lower() in filename.lower():
                self.search_results.append(filepath)
                if result_callback:
                    result_callback(filepath)
            
            # 非class文件内容匹配
            if not filename.endswith('.class'):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if keyword.lower() in content and filepath not in self.search_results:
                            self.search_results.append(filepath)
                            if result_callback:
                                result_callback(filepath)
                except Exception:
                    pass
            
            # class文件内容匹配
            if filename.endswith('.class') and self.search_class_content(filepath, keyword):
                if filepath not in self.search_results:
                    self.search_results.append(filepath)
                    if result_callback:
                        result_callback(filepath)
        
        self.is_searching = False
        return self.search_results
    
    def search_class_content(self, filepath, keyword):
        try:
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_decompiled')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 确保CFR jar文件存在
            if not os.path.exists('libs/cfr.jar'):
                raise FileNotFoundError('cfr.jar not found in libs directory')
            
            # 执行CFR反编译器并检查返回码
            result = subprocess.run(
                ['java', '-jar', 'libs/cfr.jar', '--outputpath', temp_dir, filepath],
                capture_output=True,
                text=True,
                timeout=30  # 增加超时时间
            )
            
            # 检查CFR执行是否成功
            if result.returncode != 0:
                print(f'CFR反编译失败，返回码: {result.returncode}')
                print(f'错误输出: {result.stderr}')
                return False
            
            # 解析输出以查找生成的Java文件路径
            java_file_path = None
            if hasattr(result, 'stdout'):
                output_lines = result.stdout.splitlines() if result.stdout else []
            else:
                output_lines = []
            
            # 从CFR的输出中找到生成的Java文件路径
            for line in output_lines:
                if "Writing" in line and line.endswith(".java"):
                    # 提取CFR输出中的Java文件路径
                    java_file_path = line.split("Writing ")[1].strip()
                    break
            
            # 如果无法从输出中找到路径，尝试递归搜索temp_dir目录
            if not java_file_path:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.java'):
                            java_file_path = os.path.join(root, file)
                            print(f'找到Java文件: {java_file_path}')
                            break
                    if java_file_path:
                        break
            
            # 如果仍未找到，尝试基于类名的直接匹配
            if not java_file_path:
                class_name = os.path.basename(filepath).replace('.class', '')
                # 递归搜索包含该类名的Java文件
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == f"{class_name}.java":
                            java_file_path = os.path.join(root, file)
                            print(f'根据类名找到Java文件: {java_file_path}')
                            break
                    if java_file_path:
                        break
            
            # 如果找到了Java文件，读取并搜索关键词
            if java_file_path and os.path.exists(java_file_path):
                try:
                    with open(java_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return keyword.lower() in content.lower()
                except UnicodeDecodeError:
                    # 尝试不同编码
                    with open(java_file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        return keyword.lower() in content.lower()
            else:
                print(f'未找到反编译后的Java文件')
                return False
        except subprocess.TimeoutExpired:
            print(f'反编译超时: {filepath}')
            return False
        except Exception as e:
            print(f'反编译失败: {str(e)}')
            return False