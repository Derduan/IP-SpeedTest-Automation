# IP-Pro-Tool：智能IP优选与自动化处理工具

**IP-Pro-Tool** 是一个为高效筛选和管理IP地址而设计的功能强大的自动化工作流。它能够智能地从本地或网络源获取IP地址，通过高并发测速筛选出最优质的节点，并将结果无缝同步到您选择的后端服务（如自定义API或GitHub Gist）。同时，集成的Telegram机器人让您能够完全远程监控和操作，实现真正的“无人值守”自动化。

---

### ✨ 核心功能

* **🚀 双模IP源获取**
    * **本地文件模式**: 智能扫描并解析本地的 `.txt` 或 `.csv` 文件，自动识别并提取IP与端口。
    * **远程下载模式**: 从指定URL下载ZIP压缩包，自动解压并智能提取IP。程序会优先从目录名解析端口，若失败则回退至文件内容进行正则匹配。

* **⚡️ 高效并行测速**
    * 利用多线程技术，同时对新获取的IP和历史有效IP进行速度测试，极大地缩短了处理时间，显著提升筛选效率。

* **💾 灵活的数据后端**
    * **自定义API**: 支持将优选后的IP列表通过POST请求上传至您自己的API端点。
    * **GitHub Gist**: 支持将结果自动更新到指定的GitHub Gist，方便版本管理和分享。
    * 当两种后端都配置时，程序会在运行时人性化地提示您进行选择。

* **🤖 全程机器人遥控**
    * 通过集成的Telegram机器人，您只需发送简单的指令（`1` 或 `2`）即可远程启动IP处理任务。
    * 任务的启动、完成以及最终结果，机器人都会自动推送通知和文件到您的Telegram，实现完全的自动化监控。

* **⚙️ 清晰的模块化设计**
    * 项目代码结构清晰，将主逻辑、机器人控制、IP提取等核心功能解耦到独立的脚本中，便于理解、维护和二次开发。

* **🛠️ 完善的配置与容错**
    * 所有配置项均通过 `.env` 文件进行管理，既安全又便捷。
    * 脚本内置了完整的进度条、日志输出和错误处理机制，确保运行过程稳定可靠。

---

### 📊 工作流程

```mermaid
graph TD
    A[开始] --> B{选择运行方式};
    B --> C[1. 命令行直接运行];
    B --> D[2. 启动Telegram机器人];

    subgraph 机器人控制
        D --> E{接收TG指令 '1' 或 '2'};
        E --> F[调用主流程];
    end

    subgraph 主流程 main.py
        C --> G{选择数据后端: API/Gist};
        F --> G;
        G --> H{选择IP源模式: 1-本地 / 2-远程};
        H -- 模式1 --> I[ipccc.py: 处理本地文件];
        H -- 模式2 --> J[cmip_downloader.py: 下载并处理远程文件];
        I --> K[生成 ip.txt];
        J --> K;

        K --> L{并行测速};
        subgraph 并行测速
            L --> M[测速新IP (ip.txt)];
            L --> N[下载并测速历史有效IP];
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
```

---

### 📁 项目结构

```
.
├── .env.example          # 配置文件模板
├── bot.py                # Telegram 机器人入口脚本
├── cmip_downloader.py    # 模式二：远程IP下载与解析逻辑
├── ipccc.py              # 模式一：本地IP文件提取逻辑
├── iptest.exe            # IP测速核心程序 (需自行准备)
├── main.py               # 主流程控制脚本
├── README.md             # 本说明文档
└── requirements.txt      # Python 依赖库
```

---

### 🚀 快速开始

#### 1. 环境准备

* **Python**: 确保已安装 Python 3.8 或更高版本。
* **Git**: 确保已安装 Git。
* **iptest.exe**: 请自行获取 `iptest.exe` 文件，并将其放置在项目根目录。

#### 2. 安装步骤

git clone <你的仓库URL>
cd <你的仓库目录>

创建并激活Python虚拟环境 (强烈推荐):

# 创建
python -m venv .venv

# 激活 (Windows)
.venv\Scripts\activate

# 激活 (macOS/Linux)
# source .venv/bin/activate

3.  **安装依赖库**:
    ```bash
    pip install -r requirements.txt
    ```

#### 3. 项目配置

将 `.env.example` 文件复制一份并重命名为 `.env`，然后根据以下说明填写您的配置信息。

| 变量                | 是否必须 | 说明                                                                 |
| :------------------ | :------: | :------------------------------------------------------------------- |
| `CUSTOM_API_URL`    |  二选一  | 您的自定义API地址，用于接收最终的IP列表文本。                          |
| `GIST_ID`           |  二选一  | 您的GitHub Gist ID。                                                 |
| `GITHUB_TOKEN`      |  二选一  | 拥有 `gist` 权限的GitHub个人访问令牌。                               |
| `GIST_FILENAME`     |    否    | 在Gist中保存IP列表的文件名，默认为 `ip_list.txt`。                   |
| `CMIP_ZIP_URL`      |  **是** | 模式二使用的远程IP压缩包下载地址。                                   |
| `SPEED_TEST_URL`    |  **是** | `iptest.exe` 用于测速的下载文件URL (例如 `.../50mb.bin`)。           |
| `IPTEST_MAX`        |    否    | `iptest.exe` 并发测速的最大线程数，默认为 `200`。                      |
| `IPTEST_SPEEDTEST`  |    否    | `iptest.exe` 测速模式，默认为 `3` (下载+上传)。                      |
| `IPTEST_SPEEDLIMIT` |    否    | `iptest.exe` 速度下限 (MB/s)，低于此速度的IP将被丢弃，默认为 `6`。    |
| `IPTEST_DELAY`      |    否    | `iptest.exe` 延迟上限 (ms)，高于此延迟的IP将被丢弃，默认为 `260`。    |
| `TG_BOT_TOKEN`      |  **是** | 您的Telegram机器人Token。                                            |
| `TG_CHAT_ID`        |  **是** | 用于接收通知和文件的Telegram聊天ID。                                 |

---

### 🛠️ 使用指南

#### 方法一：通过命令行运行

此方法适用于在本地直接执行或进行调试。

```bash
python main.py
```
程序将自动检测您的配置，并根据提示引导您选择数据后端和运行模式。

#### 方法二：通过Telegram机器人

此方法可实现远程“无人值守”操作。

1.  **启动机器人后台服务**:
    ```bash
    python bot.py
    ```
    终端将显示 `机器人已上线，正在监听消息...`。

2.  **与机器人交互**:
    * 在Telegram中找到您的机器人，发送 `/start` 命令，机器人会返回欢迎语和模式选项。
    * 直接向机器人发送数字 `1` 或 `2`，即可启动对应模式的IP处理任务。
    * 任务完成后，机器人会将结果报告和 `final_ip_list.txt` 文件发送给您。

---

### 🔗 与 edgetunnel 项目联动

本工具生成的IP列表URL可无缝对接到 [cmliu/edgetunnel](https://github.com/cmliu/edgetunnel) 项目中作为优选IP源。

* **若使用API**: 源URL即为您在 `.env` 中配置的 `CUSTOM_API_URL`。
* **若使用Gist**: 前往您的Gist页面，点击 **Raw** 按钮，浏览器地址栏中显示的链接即为源URL。

将此URL用于 edgetunnel 项目的 ADDAPI 变量或相关配置中即可。更多详情请参考 edgetunnel 官方文档：https://github.com/cmliu/edgetunnel

🙏 致谢
yutian: 感谢其开发的 IP-SpeedTest (iptest.exe) 工具。

GitHub: https://github.com/yutian81

cmliu: 感谢其 edgetunnel 项目以及在IP处理方面分享的经验。

GitHub: https://github.com/cmliu

Telegram: https://t.me/zip_cm_edu_kg