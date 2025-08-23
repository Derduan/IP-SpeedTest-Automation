import tkinter as tk
from tkinter import filedialog, messagebox

def process_and_merge_files():
    """
    主函数：引导用户选择文件，处理数据，然后保存结果。
    """
    # 1. 初始化Tkinter并隐藏主窗口
    root = tk.Tk()
    root.withdraw()

    # 2. 弹出对话框，让用户选择多个文件
    # file_paths会是一个包含所有选中文件路径的元组
    file_paths = filedialog.askopenfilenames(
        title="请选择要合并去重的代理文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )

    # 如果用户没有选择任何文件，则退出程序
    if not file_paths:
        print("没有选择任何文件，操作已取消。")
        return

    print(f"已选择 {len(file_paths)} 个文件进行处理...")

    # 3. 读取所有文件内容并进行数据处理
    unique_lines = set() # 使用集合（set）来自动实现去重
    for file_path in file_paths:
        try:
            # 使用'utf-8'编码打开文件，忽略可能出现的编码错误
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    cleaned_line = line.strip() # 去除行首尾的空白
                    if cleaned_line: # 确保不是空行
                        unique_lines.add(cleaned_line)
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
    
    print(f"处理完成，共找到 {len(unique_lines)} 个不重复的条目。")

    # 4. 弹出对话框，让用户选择保存位置
    output_path = filedialog.asksaveasfilename(
        title="请选择合并后文件的保存位置",
        initialfile="merged_proxies.txt", # 默认保存文件名
        defaultextension=".txt",
        filetypes=[("文本文件", "*.txt")]
    )

    # 如果用户没有选择保存路径，则退出程序
    if not output_path:
        print("未选择保存位置，操作已取消。")
        return
        
    # 5. 将处理后的数据写入新文件
    try:
        # 将集合转换为列表并排序，使输出更有序
        sorted_lines = sorted(list(unique_lines))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted_lines))
            
        success_message = (
            f"操作成功！\n\n"
            f"合并了 {len(file_paths)} 个文件。\n"
            f"共得到 {len(sorted_lines)} 条不重复数据。\n\n"
            f"文件已保存至：\n{output_path}"
        )
        print(success_message)
        # 弹出成功提示框
        messagebox.showinfo("成功", success_message)

    except Exception as e:
        error_message = f"保存文件时出错: {e}"
        print(error_message)
        messagebox.showerror("错误", error_message)


# 当直接运行此脚本时，执行主函数
if __name__ == "__main__":
    process_and_merge_files()