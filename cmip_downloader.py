# -*- coding: utf-8 -*-
"""
智能IP下载与解析脚本 (模式二重构)
- [重构] 将原 cmip.sh 的功能用Python实现，移除了对bash的依赖。
- [升级] 下载URL从 .env 文件读取，使数据源可配置。
- [智能] 增强了数据提取逻辑：
    1. 优先尝试从目录名解析端口号。
    2. 如果目录名不是端口，则回退到扫描文件内容，查找 IP:端口/IP 端口 格式。
- [健壮] 增加了完整的错误处理、下载进度条和自动清理功能。
"""
import os
import time
import re
import sys
import shutil
import zipfile
from pathlib import Path
from typing import Set

import requests
from dotenv import load_dotenv

try:
    from tqdm import tqdm
except ImportError:
    # 简单的tqdm替代品
    def tqdm(iterable, *args, **kwargs):
        print("提示：未安装tqdm库，无进度条显示。可运行 'pip install tqdm' 安装。")
        return iterable

# --- 配置与常量定义 ---
load_dotenv()
# [新增] 从.env文件读取下载URL
CMIP_ZIP_URL = os.getenv("CMIP_ZIP_URL")

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_FILENAME = "ip.txt"
TEMP_DIR = BASE_DIR / "temp_cmip_download"

def download_file(url: str, dest_path: Path):
    """带进度条的文件下载函数。"""
    print(f"[*] 正在从 {url} 下载文件...")
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                with dest_path.open('wb') as f, tqdm(
                    total=total_size, unit='iB', unit_scale=True, desc=dest_path.name
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        bar.update(len(chunk))
            print(f"[+] 下载成功: {dest_path}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[-] 下载失败(尝试 {attempts}): {e}")
            if attempts < 3:
                time.sleep(2)
            else:
                print(f"[-] [致命错误] 下载文件失败: {e}")
                return False

def extract_zip(zip_path: Path, extract_to: Path):
    """解压ZIP文件。"""
    print(f"[*] 正在解压文件: {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[+] 解压完成，文件已解压至: {extract_to}")
        return True
    except zipfile.BadZipFile:
        print(f"[-] [致命错误] 文件不是一个有效的ZIP压缩包或已损坏。")
        return False
    except Exception as e:
        print(f"[-] [致命错误] 解压时发生未知错误: {e}")
        return False

def process_extracted_files(extract_dir: Path) -> Set[str]:
    """
    [核心智能逻辑] 遍历解压后的目录并提取IP和端口。
    """
    unique_ips: Set[str] = set()
    # 通用扫描正则表达式
    general_pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s,]+(\d{1,5})")

    print("[*] 开始智能扫描解压目录...")
    # 查找所有.txt文件
    txt_files = list(extract_dir.rglob('*.txt'))
    
    if not txt_files:
        print("[!] 在压缩包中未找到任何 .txt 文件。")
        return unique_ips

    for file_path in tqdm(txt_files, desc="处理文件", unit="个"):
        try:
            # 策略一：尝试从父目录名获取端口
            parent_dir_name = file_path.parent.name
            port_from_dir = None
            if parent_dir_name.isdigit() and 1 <= int(parent_dir_name) <= 65535:
                port_from_dir = parent_dir_name
                
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if port_from_dir:
                # 如果目录名是端口，则假定文件内都是IP地址
                # 使用更简单的IP匹配，避免误匹配
                ip_pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
                found_in_dir_mode = False
                for ip_match in ip_pattern.finditer(content):
                    unique_ips.add(f"{ip_match.group(1)} {port_from_dir}")
                    found_in_dir_mode = True
                if found_in_dir_mode:
                    continue # 如果此模式成功，则处理下一个文件

            # 策略二：如果策略一失败或未找到IP，则回退到通用扫描
            for match in general_pattern.finditer(content):
                unique_ips.add(f"{match.group(1)} {match.group(2)}")

        except Exception as e:
            tqdm.write(f"[-] 处理文件 '{file_path}' 时出错: {e}")
            
    return unique_ips

def main():
    """脚本主流程。"""
    if not CMIP_ZIP_URL:
        print("[-] [致命错误] 未在 .env 文件中配置 CMIP_ZIP_URL。")
        sys.exit(1)

    # 1. 清理并创建临时目录
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir()

    zip_file_path = TEMP_DIR / "download.zip"

    try:
        # 2. 下载文件
        if not download_file(CMIP_ZIP_URL, zip_file_path):
            sys.exit(1)

        # 3. 解压文件
        if not extract_zip(zip_file_path, TEMP_DIR):
            sys.exit(1)

        # 4. 智能处理数据
        found_ips = process_extracted_files(TEMP_DIR)

        output_path = BASE_DIR / OUTPUT_FILENAME
        if not found_ips:
            print("\n[i] 未能从下载的文件中提取到任何IP地址。")
            output_path.touch() # 创建空文件以保证主流程继续
            return

        # 5. 排序并保存结果
        sorted_ips = sorted(list(found_ips), key=lambda x: [int(part) for part in x.split(' ')[0].split('.')])
        with output_path.open('w', encoding='utf-8') as f:
            for item in sorted_ips:
                f.write(item + '\n')

        print("\n" + "[SUCCESS]" * 5)
        print(f"[+] 模式二处理完成！共提取 {len(sorted_ips)} 条唯一IP记录。")
        print(f"    结果已保存至: '{output_path.name}'")
        print("[SUCCESS]" * 5)

    finally:
        # 6. 最终清理
        if TEMP_DIR.exists():
            print("[*] 正在清理临时文件...")
            shutil.rmtree(TEMP_DIR)
            print("[+] 清理完成。")

if __name__ == "__main__":
    main()
