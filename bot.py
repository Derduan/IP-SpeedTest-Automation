# bot.py
import subprocess
import sys
import os
import logging
import requests
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
    user_input = update.message.text.strip()
    
    if user_input in ("1", "2"):
        await update.message.reply_text(
            f"✅ 已收到指令！正在以 **模式 {user_input}** 启动IP处理任务...\n\n"
            "⏳ 任务已启动，请耐心等待结果，处理完成后会自动推送到此对话。", 
            parse_mode='Markdown'
        )
        try:
            # 检查主脚本是否存在
            if not MAIN_PY_SCRIPT.exists():
                await update.message.reply_text(f"❌ 错误：主脚本 {MAIN_PY_SCRIPT.name} 不存在，无法启动任务。")
                return

            # 以命令行参数方式启动主脚本，后台运行且不阻塞机器人
            cmd = [sys.executable, str(MAIN_PY_SCRIPT), user_input]
            popen_kwargs = {
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL,
                'stdin': subprocess.DEVNULL,
                'close_fds': True,
            }
            if os.name == 'nt':
                # 在 Windows 上分离子进程组
                popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

            subprocess.Popen(cmd, **popen_kwargs)
            print(f"机器人已在后台启动任务：{' '.join(cmd)}")
        except Exception as e:
            await update.message.reply_text(f"❌ 启动任务时发生未知错误: {e}")
    else:
        await update.message.reply_text(
            "🙁 无效的指令。请输入 `1` 或 `2` 来选择运行模式。"
        )

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pid_file = BASE_DIR / 'run.pid'
    if not pid_file.exists():
        await update.message.reply_text('ℹ️ 当前没有正在运行的任务 (未找到 run.pid)。')
        return
    try:
        pid = int(pid_file.read_text(encoding='utf-8').strip())
    except Exception:
        await update.message.reply_text('⚠️ 无法读取 run.pid 内容，可能已损坏。')
        return
    # 检查进程是否存在
    if os.name == 'nt':
        # Windows: 使用 tasklist 检查
        import subprocess as _sub
        res = _sub.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
        if str(pid) in res.stdout:
            await update.message.reply_text(f'✅ 任务正在运行 (PID: {pid})')
        else:
            await update.message.reply_text(f'ℹ️ 未找到 PID {pid} 对应的进程，可能已退出。')
    else:
        try:
            os.kill(pid, 0)
            await update.message.reply_text(f'✅ 任务正在运行 (PID: {pid})')
        except OSError:
            await update.message.reply_text(f'ℹ️ 未找到 PID {pid} 对应的进程，可能已退出。')

async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pid_file = BASE_DIR / 'run.pid'
    if not pid_file.exists():
        await update.message.reply_text('ℹ️ 当前没有正在运行的任务 (未找到 run.pid)。')
        return
    try:
        pid = int(pid_file.read_text(encoding='utf-8').strip())
    except Exception:
        await update.message.reply_text('⚠️ 无法读取 run.pid 内容，可能已损坏。')
        return
    try:
        if os.name == 'nt':
            import subprocess as _sub
            _sub.run(['taskkill', '/PID', str(pid), '/F'])
        else:
            os.kill(pid, 15)
        await update.message.reply_text(f'✅ 已尝试停止 PID {pid} 的进程。')
        try:
            pid_file.unlink()
        except Exception:
            pass
    except Exception as e:
        await update.message.reply_text(f'❌ 停止任务时发生错误: {e}')

def main() -> None:
    """启动机器人"""
    if not TOKEN:
        print("❌ 错误: .env 文件中未找到 TG_BOT_TOKEN。机器人无法启动。")
        sys.exit(1)
    # 启用基础日志，便于诊断
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 在启动前校验 token 可访问性，帮助判断是否为网络/凭证问题
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10)
        if r.ok:
            info = r.json()
            logger.info("Telegram getMe OK: %s", info.get('result', {}))
        else:
            logger.warning("Telegram getMe returned non-OK status: %s %s", r.status_code, r.text)
    except Exception as e:
        logger.exception("调用 Telegram getMe 时发生异常（这可能导致机器人无法接收消息）: %s", e)

    print("🚀 机器人正在启动...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("stop", stop_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 全局错误处理器，记录并回复（用于诊断）
    async def _error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger = logging.getLogger('telegram_error')
        logger.exception('处理更新时发生异常: %s', context.error)
        try:
            if update and getattr(update, 'message', None):
                await update.message.reply_text('⚠️ 机器人内部发生错误，已记录。')
        except Exception:
            pass

    application.add_error_handler(_error_handler)

    print("✅ 机器人已上线，正在监听消息...")
    application.run_polling()

if __name__ == '__main__':
    main()
