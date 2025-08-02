# -*- coding: utf-8 -*-
"""
IP地址提取脚本 (优化版)
- 增加了对命令行参数的支持，以避免在被其他脚本调用时重复提问。
- 保留了独立运行时交互式选择文件的功能。
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Set

try:
    from tqdm import tqdm
except ImportError:
    # 如果没有安装tqdm，提供一个简单的替代品，避免程序崩溃
    def tqdm(iterable, *args, **kwargs):
        print("提示：未安装tqdm库，无进度条显示。可运行 'pip install tqdm' 安装。")
        return iterable

# --- 常量定义 ---
CURRENT_DIR = Path.cwd()
OUTPUT_FILENAME = "ip.txt"

def find_source_files() -> List[Path]:
    """在当前目录下查找所有 .txt 和 .csv 文件（排除输出文件自身）。"""
    print("[*] 正在扫描源文件...")
    source_files = [
        f for f in CURRENT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in ['.txt', '.csv'] and f.name.lower() != OUTPUT_FILENAME.lower()
    ]
    print(f"[+] 扫描完成，找到 {len(source_files)} 个潜在的源文件。")
    return source_files

def select_files_from_list(file_list: List[Path]) -> List[Path]:
    """向用户显示文件列表并让其选择。"""
    if not file_list:
        return []

    print("─" * 40)
    print("检测到以下文件，请选择需要处理的文件：")
    for i, filename in enumerate(file_list):
        print(f"  [{i + 1}] {filename.name}")
    print("─" * 40)

    while True:
        try:
            choice_str = input("请输入文件序号（多个请用空格或逗号隔开），或直接按回车取消: ")
            if not choice_str:
                return []
            
            choices = re.split(r'[\s,]+', choice_str.strip())
            selected_indices = {int(c) - 1 for c in choices if c.isdigit()}
            
            selected_files = [
                file_list[i] for i in selected_indices if 0 <= i < len(file_list)
            ]
            
            if selected_files:
                return selected_files
            else:
                print("[!] 输入无效，请输入列表中的正确序号。")
        except ValueError:
            print("[!] 输入错误，请输入数字。")

def process_files(files_to_process: List[Path], output_file: Path) -> None:
    """从指定的文件列表中提取IP和端口。"""
    unique_ips: Set[str] = set()
    # 正则表达式，用于匹配 IP地址:端口 或 IP地址 端口 格式
    ip_port_pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s]+(\d{1,5})")

    print(f"\n[*] 开始处理 {len(files_to_process)} 个文件...")
    for file_path in tqdm(files_to_process, desc="提取IP进度", unit="个文件"):
        try:
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    for match in ip_port_pattern.finditer(line):
                        ip_address = match.group(1)
                        port = match.group(2)
                        # 统一输出格式为 "IP地址 端口" 以兼容iptest.exe
                        unique_ips.add(f"{ip_address} {port}")
        except Exception as e:
            tqdm.write(f"[-] 读取文件 '{file_path.name}' 时发生错误: {e}")

    if not unique_ips:
        print("\n[i] 在所选文件中未能提取到任何有效的 IP 地址和端口。")
        return

    # 按IP地址排序
    sorted_ips = sorted(list(unique_ips), key=lambda x: [int(part) for part in x.split(' ')[0].split('.')])
    
    try:
        with output_file.open('w', encoding='utf-8') as f_out:
            # 写入表头以明确列名，iptest.exe可以处理带表头的文件
            f_out.write("IP地址 端口\n")
            for item in sorted_ips:
                f_out.write(item + '\n')
        print("\n" + "[SUCCESS]" * 5)
        print(f"[+] 处理完成！共提取并保存了 {len(sorted_ips)} 条唯一的 IP 地址和端口记录。")
        print(f"    结果已保存至: '{output_file}'")
        print("[SUCCESS]" * 5)
    except Exception as e:
        print(f"\n[-] [致命错误] 保存结果到文件 '{output_file}' 时发生严重错误: {e}")

def main() -> None:
    """程序主入口。"""
    output_path = CURRENT_DIR / OUTPUT_FILENAME
    files_to_run: List[Path] = []

    # [修复] 检查命令行参数
    try:
        # 如果通过 -i 或 --input 提供了文件名
        if "-i" in sys.argv and len(sys.argv) > sys.argv.index("-i") + 1:
            file_index = sys.argv.index("-i") + 1
            input_file = Path(sys.argv[file_index])
            if input_file.exists():
                print(f"[*] 已通过命令行参数接收到文件: {input_file.name}")
                files_to_run.append(input_file)
            else:
                print(f"[!] 错误：通过命令行指定的文件不存在: {input_file}")
                sys.exit(1)
        elif "--input" in sys.argv and len(sys.argv) > sys.argv.index("--input") + 1:
            file_index = sys.argv.index("--input") + 1
            input_file = Path(sys.argv[file_index])
            if input_file.exists():
                print(f"[*] 已通过命令行参数接收到文件: {input_file.name}")
                files_to_run.append(input_file)
            else:
                print(f"[!] 错误：通过命令行指定的文件不存在: {input_file}")
                sys.exit(1)
    except Exception as e:
        print(f"[!] 解析命令行参数时出错: {e}")
        sys.exit(1)

    # 如果没有通过命令行指定文件，则进入交互模式
    if not files_to_run:
        print("[*] 未通过命令行指定文件，进入交互选择模式。")
        all_files = find_source_files()
        if not all_files:
            print("[i] 当前目录未找到任何 .txt 或 .csv 文件。")
            return
        files_to_run = select_files_from_list(all_files)

    # 如果最终有文件需要处理，则执行处理
    if files_to_run:
        process_files(files_to_run, output_path)
    else:
        print("[i] 没有选择任何文件，程序退出。")

if __name__ == "__main__":
    main()
