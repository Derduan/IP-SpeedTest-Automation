# bot.py
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 配置加载 ---
load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")

# 定义主脚本路径
BASE_DIR = Path(__file__).parent.resolve()
MAIN_PY_SCRIPT = BASE_DIR / "main.py"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送欢迎信息和菜单"""
    # [文本优化] 更新了模式描述以匹配新功能
    welcome_message = (
        "👋 您好！欢迎使用IP智能处理机器人。\n\n"
        "请选择一个操作模式：\n"
        "1. **模式一**: 自动扫描并处理目录下所有txt/csv源文件。\n"
        "2. **模式二**: 从配置的URL智能下载并解析IP数据。\n\n"
        "👉 直接发送数字 `1` 或 `2` 即可开始任务。"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理用户的模式选择"""
    user_input = update.message.text.strip()
    
    if user_input in ("1", "2"):
        await update.message.reply_text(f"✅ 已收到指令！正在以 **模式 {user_input}** 启动IP处理任务...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(MAIN_PY_SCRIPT)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            process.communicate(input=user_input + '\n', timeout=3600) # 设置1小时超时
            
            print(f"机器人成功启动了模式 {user_input} 的任务。")
            
        except FileNotFoundError:
            await update.message.reply_text(f"❌ 错误：无法找到主脚本 {MAIN_PY_SCRIPT.name}。")
        except Exception as e:
            await update.message.reply_text(f"❌ 启动任务时发生未知错误: {e}")
    else:
        await update.message.reply_text(
            "🙁 无效的指令。请输入 `1` 或 `2` 来选择运行模式。"
        )

def main() -> None:
    """启动机器人"""
    if not TOKEN:
        print("❌ 错误: .env 文件中未找到 TG_BOT_TOKEN。机器人无法启动。")
        sys.exit(1)
        
    print("🚀 机器人正在启动...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ 机器人已上线，正在监听消息...")
    application.run_polling()

if __name__ == '__main__':
    main()
