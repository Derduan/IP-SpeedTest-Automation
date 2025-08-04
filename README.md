# IP-Pro-Tool: 智能IP优选与自动化处理工具
IP-Pro-Tool 是一个功能强大的自动化IP处理工作流，专为高效筛选和管理IP地址而设计。它能智能地从本地或网络获取IP，通过并行测速筛选出高质量节点，并将结果自动同步到您选择的后端（自定义API或GitHub Gist），同时通过Telegram机器人实现完整的远程监控与操作。

✨ 核心功能
🚀 双模IP源获取:

模式一 (本地文件): 智能扫描并解析本地 .txt / .csv 文件，自动识别IP与端口列。

模式二 (远程下载): 从 .env 文件配置的URL下载ZIP压缩包，自动解压并智能提取IP。它会优先尝试从目录名解析端口，若失败则回退至文件内容正则匹配。

⚡️ 高效并行测速: 利用多线程同时对新获取的IP和历史有效的IP进行测速，极大缩短了处理耗时，提高了筛选效率。

💾 灵活数据后端:

支持将优选后的IP列表上传至您私有的自定义API。

支持将结果自动更新到指定的 GitHub Gist。

当两种后端都配置时，程序会人性化地让您在运行时选择其一。

🤖 全程机器人遥控:

集成Telegram机器人，可通过发送简单指令 (1 或 2) 远程启动IP处理任务。

任务的开始、结束以及最终结果，机器人都会自动推送通知和文件到您的Telegram，实现“无人值守”。

⚙️ 清晰的模块化设计:

项目代码结构清晰，将主逻辑、机器人控制、IP提取等功能解耦到不同脚本中，易于理解和二次开发。

🛠️ 完善的配置与容错:

所有配置项均通过 .env 文件管理，安全便捷。

脚本包含完整的进度条、日志输出和错误处理机制，运行稳定可靠。

📊 工作流程
graph TD
    A[开始] --> B{选择运行方式};
    B --> C[1. 命令行运行 main.py];
    B --> D[2. 启动 bot.py 机器人];
    
    subgraph 机器人控制
        D --> E{接收TG指令 '1' 或 '2'};
        E --> F[调用 main.py];
    end

    subgraph 主流程 main.py
        C --> G{选择数据后端: API/Gist};
        F --> G;
        G --> H{选择IP源模式: 1/2};
        H -- 模式1 --> I[运行 ipccc.py 处理本地文件];
        H -- 模式2 --> J[运行 cmip_downloader.py 下载并处理];
        I --> K[生成 ip.txt];
        J --> K;
        
        K --> L{并行测速};
        subgraph 并行测速
            L --> M[测速新IP (ip.txt)];
            L --> N[下载并测速历史IP];
        end

        M --> O[生成 new_ip_test_result.csv];
        N --> P[生成 old_ip_test_result.csv];

        O --> Q{合并与去重};
        P --> Q;
        
        Q --> R[生成 final_ip_list.txt];
        R --> S{上传结果};
        S -- Gist --> T[更新到GitHub Gist];
        S -- API --> U[推送到自定义API];
        
        T --> V[发送TG通知和文件];
        U --> V;
    end
    
    V --> W[结束];

(注意: 上方的流程图使用了 Mermaid 语法，在GitHub等平台上会自动渲染成图表。)

📁 项目结构
.
├── .env.example          # 配置文件模板
├── bot.py                # Telegram 机器人入口脚本
├── cmip_downloader.py    # 模式二：远程IP下载与解析逻辑
├── ipccc.py              # 模式一：本地IP文件提取逻辑
├── iptest.exe            # IP测速核心程序 (需自行准备)
├── main.py               # 主流程控制脚本
├── README.md             # 本说明文档
└── requirements.txt      # Python 依赖库

🚀 快速开始
1. 环境准备
Python: 确保已安装 Python 3.8 或更高版本。

Git: 确保已安装 Git。

iptest.exe: 请自行获取 iptest.exe 文件，并将其放置在项目根目录。

2. 安装步骤
克隆项目代码:

git clone <你的仓库URL>
cd <你的仓库目录>

创建并激活Python虚拟环境 (强烈推荐):

# 创建
python -m venv .venv

# 激活 (Windows)
.venv\Scripts\activate

# 激活 (macOS/Linux)
# source .venv/bin/activate

安装依赖库:

pip install -r requirements.txt

3. 项目配置
将 .env.example 复制一份并重命名为 .env，然后根据以下说明填写您自己的信息。

CUSTOM_API_URL

是否必须: 二选一

说明: 您的自定义API地址。用于接收POST请求，请求体为最终的IP列表文本。

GIST_ID

是否必须: 二选一

说明: 您的GitHub Gist ID。

GITHUB_TOKEN

是否必须: 二选一

说明: 拥有 gist 权限的GitHub个人访问令牌。

GIST_FILENAME

是否必须: 否

说明: 在Gist中保存IP列表的文件名，默认为 ip_list.txt。

CMIP_ZIP_URL

是否必须: 是

说明: 模式二使用的远程IP压缩包下载地址。

SPEED_TEST_URL

是否必须: 是

说明: iptest.exe 用于测速的下载文件URL (例如 .../50mb.bin)。

IPTEST_MAX

是否必须: 否

说明: iptest.exe 并发测速的最大线程数，默认为 200。

IPTEST_SPEEDTEST

是否必须: 否

说明: iptest.exe 测速模式，默认为 3 (下载+上传)。

IPTEST_SPEEDLIMIT

是否必须: 否

说明: iptest.exe 速度下限 (MB/s)，低于此速度的IP将被丢弃，默认为 6。

IPTEST_DELAY

是否必须: 否

说明: iptest.exe 延迟上限 (ms)，高于此延迟的IP将被丢弃，默认为 260。

TG_BOT_TOKEN

是否必须: 是

说明: 您的Telegram机器人Token。

TG_CHAT_ID

是否必须: 是

说明: 用于接收通知和文件的Telegram聊天ID (可以是您自己或频道ID)。

如何配置GitHub Gist？
1. 获取GitHub Token:

前往 GitHub 的 个人访问令牌设置页面。

点击 Generate new token -> Generate new token (classic)。

在 Note (备注) 中填写一个描述性名称，如 “IP-Pro-Tool-Token”。

在 Select scopes 中，仅需勾选 gist 权限。

点击 Generate token，立即复制生成的令牌并妥善保管，此令牌仅显示一次。

2. 创建Gist并获取ID:

访问 GitHub Gist。

创建一个新的Gist，文件名和内容可随意填写。

创建成功后，查看浏览器地址栏。URL的最后一部分即为Gist ID (例如 https://gist.github.com/username/THIS_IS_THE_GIST_ID)，复制此ID。

🛠️ 使用指南
方法一：通过命令行运行
此方法适用于在本地直接执行或进行调试。

python main.py

程序将自动检测您的配置，并根据提示引导您选择数据后端和运行模式。

方法二：通过Telegram机器人
此方法可实现远程“无人值守”操作。

启动机器人后台服务:

python bot.py

终端会显示 "机器人已上线，正在监听消息..."。

与机器人交互:

在Telegram中找到您的机器人，发送 /start 命令，机器人会返回欢迎语和模式选项。

直接发送数字 1 或 2 给机器人，即可启动对应模式的IP处理任务。

任务完成后，机器人会将结果报告和 final_ip_list.txt 文件发送给您。

🔗 与 edgetunnel 项目联动
本工具生成的IP列表URL可无缝对接到 cmliu 的 edgetunnel 项目中作为优选IP源。

若使用API: 源URL即为您在 .env 中配置的 CUSTOM_API_URL。

若使用Gist: 前往您的Gist页面，点击 Raw 按钮，浏览器地址栏中显示的链接即为源URL。

将此URL用于 edgetunnel 项目的 ADDAPI 变量或相关配置中即可。更多详情请参考 edgetunnel 官方文档：https://github.com/cmliu/edgetunnel

🙏 致谢
yutian: 感谢其开发的 IP-SpeedTest (iptest.exe) 工具。

GitHub: https://github.com/yutian81

cmliu: 感谢其 edgetunnel 项目以及在IP处理方面分享的经验。

GitHub: https://github.com/cmliu

Telegram: https://t.me/zip_cm_edu_kg