#!/bin/bash

# -----------------------------------------------------------------------------
# IP 地址处理脚本 (最终版)
#
# 优化点:
# - 最终输出文件直接命名为 ip.txt，以便与 main.py 无缝衔接。
# - 增加了下载验证和文件类型检查，使脚本更健壮。
# - 修正了文件下载地址。
# - ★ 修正：移除了输出文件中的表头，以兼容 iptest.exe。
# -----------------------------------------------------------------------------

set -euo pipefail

# --- 1. 初始化和环境设置 ---
work_dir=$(pwd)
temp_dir=$(mktemp -d)
printf "创建临时工作目录: %s\n" "$temp_dir"

cleanup() {
  printf "正在清理临时目录...\n"
  cd "$work_dir"
  rm -rf "$temp_dir"
  printf "清理完成。\n"
}
trap cleanup EXIT

cd "$temp_dir"

# --- 2. 下载文件 ---
file_url="https://zip.cm.edu.kg"
output_zip="ip.zip"
printf "正在从 %s 下载文件...\n" "$file_url"

if command -v curl &> /dev/null; then
    if ! curl --fail -L -o "$output_zip" "$file_url"; then
        printf "错误：使用 curl 下载文件失败。服务器可能返回了错误（如 404 Not Found）或无法访问。\n" >&2
        exit 1
    fi
elif command -v wget &> /dev/null; then
    if ! wget -q -O "$output_zip" "$file_url"; then
        printf "错误：使用 wget 下载文件失败。\n" >&2
        exit 1
    fi
else
    printf "错误：此脚本需要安装 wget 或 curl 才能下载文件。\n" >&2
    exit 1
fi
printf "下载成功。\n"

# --- 3. 验证并解压数据 ---
printf "正在验证下载的文件类型...\n"
if ! file "$output_zip" | grep -q "Zip archive data"; then
    printf "错误：下载的文件不是一个有效的 ZIP 压缩包。\n" >&2
    printf "请在浏览器中尝试访问 %s 查看实际返回内容。\n" "$file_url" >&2
    exit 1
fi
printf "文件验证成功。\n"

printf "正在解压文件...\n"
unzip -q "$output_zip"
if [ $? -ne 0 ]; then
    printf "错误：文件解压失败，文件可能已损坏。\n" >&2
    exit 1
fi
printf "解压完成。\n"

printf "正在处理数据，合并IP和端口...\n"
> combined.txt

find . -mindepth 2 -name "ALL.txt" | while read -r file; do
    port=$(basename "$(dirname "$file")")
    while IFS= read -r ip; do
        if [[ -n "$ip" ]]; then
            printf "%s %s\n" "$ip" "$port" >> combined.txt
        fi
    done < "$file"
done

# --- 4. 去重并保存最终结果 ---
printf "正在去重并格式化最终结果...\n"
output_file="$work_dir/ip.txt" 

# ★ 修正点：直接输出排序去重后的内容，不再添加表头
sort -u combined.txt > "$output_file"

line_count=$(wc -l < "$output_file")
printf "处理完成！共提取 %d 条唯一的 IP 地址和端口记录。\n" "$line_count"
printf "最终结果已保存至: %s\n" "$output_file"
