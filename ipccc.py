# -*- coding: utf-8 -*-
"""
IP地址提取脚本 (最终智能版)
- [最终优化] 增加环境检测。在非交互模式下（如机器人调用），自动处理所有找到的源文件。
- [重构] 脚本独立处理文件选择，支持选择一个或多个文件。
- [新增] 增加了忽略列表，在扫描时自动排除过程/结果文件。
- [升级] 核心提取逻辑智能化，可自动识别CSV格式并查找对应列。
"""
import re
import sys
import csv
from pathlib import Path
from typing import List, Set

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        print("提示：未安装tqdm库，无进度条显示。可运行 'pip install tqdm' 安装。")
        return iterable

# --- 常量定义 ---
CURRENT_DIR = Path.cwd()
OUTPUT_FILENAME = "ip.txt"
IGNORED_FILENAMES = {
    "new_ip_test_result.csv", "old_ip_test_result.csv", "ip.txt",
    "api_temp.txt", "final_ip_list.txt", "requirements.txt"
}

def find_source_files() -> List[Path]:
    """在当前目录下查找所有 .txt 和 .csv 文件，并排除忽略列表中的文件。"""
    print("[*] 正在扫描源文件...")
    source_files = [
        f for f in CURRENT_DIR.iterdir()
        if f.is_file() 
        and f.suffix.lower() in ['.txt', '.csv'] 
        and f.name.lower() not in IGNORED_FILENAMES
    ]
    print(f"[+] 扫描完成，找到 {len(source_files)} 个可处理的源文件。")
    return source_files

def select_files_from_list(file_list: List[Path]) -> List[Path]:
    """向用户显示文件列表并让其选择一个或多个文件。"""
    if not file_list: return []
    print("─" * 50)
    print("请选择需要处理的文件 (可以选择多个):")
    for i, filename in enumerate(file_list):
        print(f"  [{i + 1}] {filename.name}")
    print("─" * 50)
    print("提示: 输入文件序号，多个请用空格或逗号隔开 (例如: 1 3 4)。")
    print("      直接按 Enter 键取消操作。")
    while True:
        try:
            choice_str = input("请输入您的选择: ")
            if not choice_str.strip(): return []
            choices = re.split(r'[\s,]+', choice_str.strip())
            selected_indices = {int(c) - 1 for c in choices if c.isdigit()}
            if not all(0 <= i < len(file_list) for i in selected_indices):
                 print("[!] 输入包含无效的序号，请只选择列表中的数字。")
                 continue
            selected_files = [file_list[i] for i in sorted(list(selected_indices))]
            if selected_files:
                print("\n[*] 您已选择以下文件进行处理:")
                for f in selected_files: print(f"    - {f.name}")
                return selected_files
            else:
                print("[!] 输入无效，请输入列表中的正确序号。")
        except ValueError:
            print("[!] 输入错误，请输入数字。")

def process_files(files_to_process: List[Path], output_file: Path) -> None:
    """[核心升级] 从指定的文件列表中提取IP和端口，智能处理多种格式。"""
    unique_ips: Set[str] = set()

    # 更宽容的匹配：优先匹配 ip:port，然后 ip sep port；如果没有端口则尝试行内推断最近的数字作为端口
    ip_colon_port = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\s*[:#]\s*(?P<port>\d{1,5})")
    ip_space_comma_port = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})[\s,;]+(?P<port>\d{1,5})")
    ip_only = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")

    IP_ALIASES = {"ip地址", "ip address", "ip"}
    PORT_ALIASES = {"端口", "port"}

    def is_valid_ip(ip: str) -> bool:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False

    def is_valid_port(p: str) -> bool:
        try:
            v = int(p)
            return 1 <= v <= 65535
        except Exception:
            return False

    def parse_line_add_unique(line: str, store: Set[str]):
        # 尝试多种模式
        m = ip_colon_port.search(line) or ip_space_comma_port.search(line)
        ip = port = None
        if m:
            ip = m.group('ip')
            port = m.group('port')
        else:
            m_ip = ip_only.search(line)
            if m_ip:
                ip = m_ip.group('ip')
                # 尝试找到 ip 后最近的数字作为端口
                rest = line[m_ip.end():]
                m_num = re.search(r"\d{1,5}", rest)
                if m_num:
                    port = m_num.group(0)
        if ip and port and is_valid_ip(ip) and is_valid_port(port):
            store.add(f"{ip} {port}")

    print(f"\n[*] 开始从 {len(files_to_process)} 个文件中智能提取IP...")
    for file_path in tqdm(files_to_process, desc="提取进度", unit="个文件"):
        try:
            if file_path.suffix.lower() == '.csv':
                with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                    # 读取首行并尝试判断表头
                    sample = f.read(4096)
                    f.seek(0)
                    header_line = sample.splitlines()[0] if sample else ''
                    if not any(alias in header_line.lower() for alias in IP_ALIASES):
                        tqdm.write(f"[i] CSV '{file_path.name}' 表头不规范或未包含 IP 列，按逐行扫描。")
                        for line in f:
                            parse_line_add_unique(line, unique_ips)
                        continue

                    # 尝试用 DictReader 读取（兼容有表头的 CSV）
                    try:
                        f.seek(0)
                        sample2 = f.read(8192)
                        f.seek(0)
                        has_header = False
                        try:
                            has_header = csv.Sniffer().has_header(sample2)
                        except Exception:
                            has_header = True
                        if has_header:
                            reader = csv.DictReader(f)
                            ip_col = next((fld for fld in (reader.fieldnames or []) if fld and fld.lower().strip() in IP_ALIASES), None)
                            port_col = next((fld for fld in (reader.fieldnames or []) if fld and fld.lower().strip() in PORT_ALIASES), None)
                            if ip_col and port_col:
                                for row in reader:
                                    raw_ip = (row.get(ip_col) or '').strip()
                                    raw_port = (row.get(port_col) or '').strip()
                                    # 兼容 ip:port 写在同一字段
                                    if raw_ip and ':' in raw_ip and not raw_port:
                                        m = ip_colon_port.search(raw_ip)
                                        if m:
                                            raw_ip = m.group('ip')
                                            raw_port = m.group('port')
                                    if raw_ip and raw_port and is_valid_ip(raw_ip) and is_valid_port(raw_port):
                                        unique_ips.add(f"{raw_ip} {raw_port}")
                                    else:
                                        # 若列识别失败，尝试逐行解析该 CSV 的行文本
                                        parse_line_add_unique(','.join(row.values()), unique_ips)
                                continue
                    except Exception:
                        f.seek(0)
                        for line in f:
                            parse_line_add_unique(line, unique_ips)
            else:
                with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        parse_line_add_unique(line, unique_ips)
        except Exception as e:
            tqdm.write(f"[-] 处理文件 '{file_path.name}' 时出错: {e}")

    if not unique_ips:
        print("\n[!] 在所选文件中未能提取到任何有效的 IP 地址和端口。")
        return
    
    sorted_ips = sorted(list(unique_ips), key=lambda x: [int(part) for part in x.split(' ')[0].split('.')])
    try:
        with output_file.open('w', encoding='utf-8') as f_out:
            for item in sorted_ips:
                f_out.write(item + '\n')
        print("\n" + "[SUCCESS]" * 5)
        print(f"[+] 处理完成！共提取并保存了 {len(sorted_ips)} 条唯一的 IP 地址和端口记录。")
        print(f"    结果已保存至: '{output_file}'")
        print("[SUCCESS]" * 5)
    except Exception as e:
        print(f"\n[-] [致命错误] 保存结果到文件 '{output_file}' 时发生严重错误: {e}")
        sys.exit(1)

def main() -> None:
    """程序主入口。"""
    output_path = CURRENT_DIR / OUTPUT_FILENAME
    all_files = find_source_files()

    if not all_files:
        print("\n[!] 当前目录未找到任何可供处理的 .txt 或 .csv 文件。")
        output_path.touch()
        print(f"[i] 已创建空的 '{output_path.name}' 文件。")
        return

    files_to_run = []
    # [关键优化] 检测是否在交互式终端中运行
    if sys.stdin.isatty():
        # 手动执行，显示菜单
        files_to_run = select_files_from_list(all_files)
    else:
        # 机器人调用，自动处理所有文件
        print("[*] 在非交互模式下运行，将自动处理所有找到的源文件。")
        files_to_run = all_files

    if files_to_run:
        process_files(files_to_run, output_path)
    else:
        print("[i] 没有选择任何文件或未找到文件，操作结束。")
        output_path.touch()
        print(f"[i] 已创建空的 '{output_path.name}' 文件。")

if __name__ == "__main__":
    main()
