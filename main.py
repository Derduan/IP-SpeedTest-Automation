# main.py
# -*- coding: utf-8 -*-
"""
IP处理主脚本 (智能检测最终版):
- [升级] 自动检测API和Gist配置，如果两者都存在则让用户交互式选择。
- 并行执行新旧IP的测速任务以缩短总耗时。
- [重构] 模式一和模式二现在都由独立的、更智能的Python脚本处理。
"""
import subprocess
import sys
import csv
import re
import time
import shutil
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# 导入dotenv用于加载配置文件
from dotenv import load_dotenv
import requests

# ==============================================================================
# --- 配置加载部分 ---
# ==============================================================================
load_dotenv()

# API 配置
CUSTOM_API_URL = os.getenv("CUSTOM_API_URL")

# iptest.exe 配置
SPEED_TEST_URL = os.getenv("SPEED_TEST_URL")
IPTEST_MAX = os.getenv("IPTEST_MAX", "200")
IPTEST_SPEEDTEST = os.getenv("IPTEST_SPEEDTEST", "3")
IPTEST_SPEEDLIMIT = os.getenv("IPTEST_SPEEDLIMIT", "6")
IPTEST_DELAY = os.getenv("IPTEST_DELAY", "260")

# Telegram Bot 配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# GitHub Gist 配置
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_FILENAME = os.getenv("GIST_FILENAME", "ip_list.txt")


# ==============================================================================
# --- 脚本内部路径与常量定义 ---
# ==============================================================================
BASE_DIR = Path(__file__).parent.resolve()
IPCCC_PY = BASE_DIR / "ipccc.py"
# [修改] 指向新的Python脚本
CMIP_PY = BASE_DIR / "cmip_downloader.py" 
IPTEST_EXE = BASE_DIR / "iptest.exe"
IP_TXT = BASE_DIR / "ip.txt"
NEW_IP_TEST_RESULT_CSV = BASE_DIR / "new_ip_test_result.csv"
OLD_IP_TEST_RESULT_CSV = BASE_DIR / "old_ip_test_result.csv"
API_TEMP_TXT = BASE_DIR / "api_temp.txt"
FINAL_IP_LIST_TXT = BASE_DIR / "final_ip_list.txt"

# ==============================================================================
# --- 上传与通知功能 (无变动) ---
# ==============================================================================
def send_tg_notification(message: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID: return
    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TG_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(api_url, data=payload, timeout=15).raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ 发送TG通知时发生网络错误: {e}")

def send_tg_document(file_path: Path, caption: str) -> None:
    if not all([TG_BOT_TOKEN, TG_CHAT_ID, file_path.exists()]): return
    print(f"🚀 正在发送结果文件 '{file_path.name}' 到 Telegram...")
    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendDocument"
    payload = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    try:
        with file_path.open('rb') as f:
            files = {'document': (file_path.name, f)}
            requests.post(api_url, data=payload, files=files, timeout=60).raise_for_status()
        print("✅ 文件成功发送到 Telegram！")
    except requests.exceptions.RequestException as e:
        print(f"❌ 发送文件到TG失败: {e}")

def upload_to_custom_api(content: str) -> None:
    if not content.strip():
        print("❌ 错误：最终内容为空，已中止上传以防止覆盖有效数据。")
        send_tg_notification("❌ *IP处理失败*\n\n原因: 最终内容为空，已中止上传。")
        sys.exit(1)
    print(f"📡 正在上传到自定义 API: {CUSTOM_API_URL}...")
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    try:
        requests.post(CUSTOM_API_URL, data=content.encode('utf-8'), headers=headers, timeout=30).raise_for_status()
        print(f"✅ 自定义 API 上传成功！")
    except requests.exceptions.RequestException as e:
        print(f"❌ 自定义 API 上传过程中发生网络错误: {e}")

def download_from_custom_api() -> Optional[str]:
    print(f"📥 正在从自定义 API 下载旧内容: {CUSTOM_API_URL}...")
    try:
        response = requests.get(CUSTOM_API_URL, timeout=30)
        if response.status_code == 404:
            print("ℹ️ API中没有找到旧内容 (404)，将只处理新IP。")
            return None
        response.raise_for_status()
        print("✅ 从自定义 API 下载成功！")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ 从自定义 API 下载过程中发生网络错误: {e}")
        return None

def upload_to_gist(content: str) -> None:
    print(f"📡 正在上传到 GitHub Gist (ID: {GIST_ID})...")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "description": f"IP优选列表 - 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "files": { GIST_FILENAME: { "content": content } }
    }
    try:
        response = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        print(f"✅ Gist 更新成功！")
    except requests.exceptions.RequestException as e:
        print(f"❌ Gist 更新失败: {e}")
        if e.response is not None: print(f"   服务器响应: {e.response.text}")

def download_from_gist() -> Optional[str]:
    print(f"📥 正在从 GitHub Gist 下载旧内容 (ID: {GIST_ID})...")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        response = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers, timeout=30)
        response.raise_for_status()
        gist_data = response.json()
        if GIST_FILENAME in gist_data.get("files", {}):
            print(f"✅ 从 Gist 文件 '{GIST_FILENAME}' 下载成功！")
            return gist_data["files"][GIST_FILENAME]["content"]
        else:
            print(f"ℹ️ Gist 中没有找到文件 '{GIST_FILENAME}'，将只处理新IP。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 从 Gist 下载过程中发生网络错误: {e}")
        if e.response is not None: print(f"   服务器响应: {e.response.text}")
        return None

# ==============================================================================
# --- 核心逻辑函数 ---
# ==============================================================================
def determine_data_source() -> str:
    api_configured = bool(CUSTOM_API_URL)
    gist_configured = bool(GIST_ID and GITHUB_TOKEN)

    if api_configured and gist_configured:
        if not sys.stdin.isatty():
            print("ℹ️ 在非交互模式下检测到多种配置，默认使用 [自定义 API]。")
            return 'api'
        
        print("\n--- [数据源选择] ---")
        print("检测到您同时配置了 API 和 Gist 作为数据源。")
        print("请选择本次运行使用哪一个：")
        print("  1: 自定义 API")
        print("  2: GitHub Gist")
        while True:
            choice = input("请输入选择 (1 或 2): ").strip()
            if choice == '1':
                print("✅ 您已选择使用 [自定义 API] 作为数据源。")
                return 'api'
            elif choice == '2':
                print("✅ 您已选择使用 [GitHub Gist] 作为数据源。")
                return 'gist'
            else:
                print("❌ 输入无效，请重新输入。")
    elif api_configured:
        print("ℹ️ 自动检测到 [自定义 API] 配置，将作为数据源。")
        return 'api'
    elif gist_configured:
        print("ℹ️ 自动检测到 [GitHub Gist] 配置，将作为数据源。")
        return 'gist'
    else:
        print("❌ 致命错误：您必须在 .env 文件中至少配置一种数据源 (API 或 Gist)。")
        sys.exit(1)

def choose_mode() -> str:
    if not sys.stdin.isatty():
        mode = sys.stdin.readline().strip()
        if mode in ("1", "2"): return mode
        return "1"
    print("\n--- [模式选择] ---")
    print("1. [本地文件提取] 扫描并从多个txt/csv文件提取IP")
    print("2. [网络智能下载] 从.env配置的URL下载并智能解析IP")
    while True:
        mode = input("请输入模式 (1 或 2): ").strip()
        if mode in ("1", "2"): return mode
        print("输入无效，请重新输入。")

def run_script(mode: str) -> None:
    """
    [重构] 模式二现在调用新的Python脚本 cmip_downloader.py。
    """
    script_path = IPCCC_PY if mode == "1" else CMIP_PY
    script_name = script_path.name
    
    print(f"\n--- [步骤1: 生成IP源文件] 正在运行 {script_name} ---")
    try:
        cmd = [sys.executable, str(script_path)]
        print(f"▶️ 正在执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        if not IP_TXT.exists():
             print(f"⚠️ 警告: {script_name} 运行后未生成 '{IP_TXT.name}' 文件。可能是因为没有选择文件或提取失败。")
             IP_TXT.touch() # 创建一个空文件以防后续步骤出错
        else:
             print(f"✅ {script_name} 运行成功。")

    except FileNotFoundError as e: 
        print(f"❌ 错误: 找不到所需的文件或程序: {e}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} 脚本执行失败，返回码: {e.returncode}")
        if hasattr(e, 'stderr') and e.stderr: 
            print(f"   错误输出:\n{e.stderr}")
        sys.exit(1)

def run_iptest(input_file: Path, output_csv: Path) -> None:
    if not input_file.exists() or input_file.stat().st_size == 0: 
        print(f"ℹ️ 跳过对 '{input_file.name}' 的测速，因为文件不存在或为空。")
        return
    print(f"--- [测速] 正在对 '{input_file.name}' 进行测速 ---")
    cmd = [str(IPTEST_EXE), f"-file={input_file}", f"-outfile={output_csv}", f"-max={IPTEST_MAX}", f"-speedtest={IPTEST_SPEEDTEST}", f"-speedlimit={IPTEST_SPEEDLIMIT}", f"-delay={IPTEST_DELAY}", f"-url={SPEED_TEST_URL}"]
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ 测速完成，结果已保存到 '{output_csv.name}'。")
    except FileNotFoundError: 
        print(f"❌ 错误: 未找到 'iptest.exe'。请确保它位于脚本同目录下。")
        sys.exit(1)
    except subprocess.CalledProcessError as e: 
        print(f"❌ iptest.exe 运行失败，返回码: {e.returncode}")

def process_ip_csv(input_csv: Path) -> List[str]:
    if not input_csv.exists(): return []
    print(f"--- [解析] 正在解析测速结果 '{input_csv.name}' ---")
    result_lines: List[str] = []
    HEADER_ALIASES = {"ip": ["IP地址", "IP Address"], "port": ["端口", "Port"], "code": ["国际代码", "Country Code", "Code"]}
    try:
        with input_csv.open("r", encoding="utf-8-sig", errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip = next((row.get(alias) for alias in HEADER_ALIASES["ip"] if row.get(alias)), None)
                port = next((row.get(alias) for alias in HEADER_ALIASES["port"] if row.get(alias)), None)
                code = next((row.get(alias) for alias in HEADER_ALIASES["code"] if row.get(alias)), None)
                if ip and port and code: 
                    result_lines.append(f"{ip.strip()}:{port.strip()}#{code.strip()}")
    except Exception as e: 
        print(f"❌ 处理CSV文件 '{input_csv.name}' 时发生错误: {e}")
        return []
    print(f"✅ 从 '{input_csv.name}' 中提取到 {len(result_lines)} 条有效记录。")
    return result_lines

def convert_api_content_for_test(api_content: str) -> Optional[Path]:
    print("--- [转换] 正在转换历史IP内容用于复测 ---")
    if not api_content: return None
    api_lines: List[str] = []
    pattern = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)#([A-Z]{2,})$")
    for line in api_content.strip().splitlines():
        match = pattern.match(line.strip())
        if match: 
            api_lines.append(f"{match.group(1)} {match.group(2)}")
    if not api_lines: 
        print("ℹ️ 未能从历史内容中提取到有效的IP地址。")
        return None
    try:
        with API_TEMP_TXT.open("w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in api_lines)
        print(f"✅ 已转换并保存 {len(api_lines)} 条记录到 '{API_TEMP_TXT.name}' 用于复测")
        return API_TEMP_TXT
    except IOError as e: 
        print(f"❌ 写入API临时文件失败: {e}")
        return None

def test_and_process_ips(input_file: Path, output_csv: Path) -> List[str]:
    run_iptest(input_file, output_csv)
    return process_ip_csv(output_csv)

# ==============================================================================
# --- 主流程函数 ---
# ==============================================================================
def main() -> None:
    """主流程函数。"""
    if not all([SPEED_TEST_URL, TG_BOT_TOKEN, TG_CHAT_ID]):
        print("❌ 错误：.env 文件中的基础配置不完整 (SPEED_TEST_URL, TG_BOT_TOKEN, TG_CHAT_ID)。")
        sys.exit(1)
        
    start_time = datetime.now()
    
    try:
        print("=" * 50)
        print(f"==== IP 自动处理系统 (启动于: {start_time.strftime('%Y-%m-%d %H:%M:%S')}) ====")
        print("=" * 50)

        data_source = determine_data_source()
        send_tg_notification(f"🚀 *IP全流程处理任务开始*\n\n*数据源*: `{data_source}`\n*开始时间*: `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`")

        mode = choose_mode()
        run_script(mode)
        
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix='IPTest') as executor:
            print("\n--- [步骤2: 并行测速] 已启动新旧IP并行测速 ---")
            future_new_ips = executor.submit(test_and_process_ips, IP_TXT, NEW_IP_TEST_RESULT_CSV)
            
            future_old_ips = None
            old_content = None
            if data_source == 'api':
                old_content = download_from_custom_api()
            elif data_source == 'gist':
                old_content = download_from_gist()

            if old_content:
                api_test_input_file = convert_api_content_for_test(old_content)
                if api_test_input_file:
                    future_old_ips = executor.submit(test_and_process_ips, api_test_input_file, OLD_IP_TEST_RESULT_CSV)
            
            new_valid_ips = []
            try:
                print("⏳ 正在等待新IP测速任务完成..."); 
                new_valid_ips = future_new_ips.result()
                print("✅ 新IP测速任务完成。")
            except Exception as e: 
                print(f"❌ 处理新IP的线程发生错误: {e}")

            old_valid_ips = []
            if future_old_ips:
                try:
                    print("⏳ 正在等待旧IP测速任务完成..."); 
                    old_valid_ips = future_old_ips.result()
                    print("✅ 旧IP测速任务完成。")
                except Exception as e: 
                    print(f"❌ 处理旧IP的线程发生错误: {e}")

        print("\n--- [步骤3: 合并与保存] ---")
        all_ips = set(new_valid_ips) | set(old_valid_ips)
        unique_ips = sorted(list(all_ips))
        stats = f"   - 新IP有效数: `{len(new_valid_ips)}`\n   - 旧IP有效数: `{len(old_valid_ips)}`\n   - 去重后最终数: `{len(unique_ips)}`"
        print(stats.replace('`', ''))
        
        final_content = "\n".join(unique_ips)
        FINAL_IP_LIST_TXT.write_text(final_content, encoding='utf-8')
        print(f"✅ 最终结果已保存到: '{FINAL_IP_LIST_TXT.name}'")
        
        print("\n--- [步骤4: 上传] ---")
        if data_source == 'api':
            upload_to_custom_api(final_content)
        elif data_source == 'gist':
            upload_to_gist(final_content)
        
        print("\n" + "=" * 50)
        print("🎉 全部流程已完成！")
        duration = (datetime.now() - start_time).total_seconds()
        summary_caption = f"✅ *IP全流程处理任务完成*\n\n*数据源*: `{data_source}`\n*⏱️ 耗时*: `{duration:.2f} 秒`\n\n*📊 处理结果*:\n{stats}\n\n🎉 *任务执行成功！*"
        send_tg_document(FINAL_IP_LIST_TXT, summary_caption)

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ [致命错误] 任务执行期间发生未捕获的异常: {e}")
        fail_message = f"❌ *IP全流程处理任务失败*\n\n*错误信息*: `{e}`\n\n`请检查服务器控制台日志获取详细信息。`"
        send_tg_notification(fail_message)

if __name__ == "__main__":
    main()
