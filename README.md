# IP优选小工具 & Telegram机器人

嘿！这是一个超好用的IP地址处理小助手。它能帮你自动抓IP、测速、然后把最好的结果存到你指定的地方（比如你自己的API或者GitHub Gist）。更酷的是，你还能用Telegram机器人随时随地控制它，任务跑得怎么样都会告诉你！

## ✨ 有啥好用的功能?

* **智能二选一**: 你可以把结果存到自己的API或者GitHub Gist。要是两个都配了，它会很聪明地问你这次用哪个！
* **IP来源超多**: 不管你的IP是存在`.txt`、`.csv`文件里，还是需要跑个脚本从网上扒，它都搞得定。
* **测速快得飞起**: 它会同时给新IP和老IP测速，不用一个一个等，省下大把时间！
* **配置超简单**: 所有的设置（API地址、密钥啥的）都放在一个`.env`文件里，改起来方便又安全。
* **懒人必备TG机器人**: 直接在Telegram里发个命令就能让它干活，跑完还会给你发报告，超省心！

## 🚀 怎么开始用？

跟着下面几步走，很快就能跑起来啦！

### 1. 你需要准备啥？

* **Python**: 电脑上得有Python（最好是3.8以上的版本）。
* **Git**: 这个也得装上。
* **`iptest.exe`**: 把这个测速工具放到项目文件夹里。

### 2. 三步安装

1.  **把代码弄下来**
    ```bash
    git clone <你的仓库URL>
    cd <你的仓库目录>
    ```

2.  **搞个虚拟环境** (这是个好习惯，能让项目干干净净)
    ```bash
    # 创建
    python -m venv .venv
    # 激活 (Windows看这里)
    .venv\Scripts\activate
    ```

3.  **装上所有需要的库**
    ```bash
    pip install -r requirements.txt
    ```

### 3. 配置一下

1.  **创建你的配置文件**: 找到 `.env.example` 这个文件，复制一份，然后把名字改成 `.env`。
2.  **填上你的信息**: 打开刚创建的 `.env` 文件，把里面的东西换成你自己的。
    * 想用**API**？那就填 `CUSTOM_API_URL`。
    * 想用**Gist**？那就填 `GIST_ID` 和 `GITHUB_TOKEN`。
    * 要是两个都填了，别担心，脚本跑起来的时候会问你的！

#### Gist怎么配？

* **搞个GitHub Token**:
    1.  去GitHub的[开发者设置](https://github.com/settings/tokens)。
    2.  点 `Generate new token` -> `Generate new token (classic)`。
    3.  随便写个名字，比如 "IP小工具"。
    4.  权限只用勾选 `gist` 就行了。
    5.  点 `Generate token`，然后**马上把那串码复制下来**，因为它只会出现这一次！
* **创建个Gist**:
    1.  去 [GitHub Gist](https://gist.github.com/)。
    2.  新建一个Gist，文件名和内容随便写点啥都行。
    3.  创建好之后，看浏览器地址栏，URL里那段长长的字符串就是Gist的ID，复制它！

## 🛠️ 怎么跑起来？

### 方法一：直接跑脚本

想在自己电脑上测试或者直接用，就打开命令行：
```bash
python main.py
```
然后跟着提示操作就行啦！

### 方法二：用Telegram机器人

想躺着也能用？那就启动机器人：
```bash
python bot.py
```
然后去Telegram里找你的机器人，给它发个 `/start`，它就会告诉你怎么玩了。

## 🔗 和 edgetunnel 项目联动

这个脚本跑完后，会给你一个存着最好IP的URL。这个URL可以直接用在 **cmliu** 大佬的 `edgetunnel` 项目里，简直是天作之合！

**URL在哪？**:
* **用API的话**: 就是你在 `.env` 里填的那个 `CUSTOM_API_URL`。
* **用Gist的话**: 去你的Gist页面，点一下 `Raw` 按钮，这时候浏览器地址栏里的链接就是了。

**怎么用？**:
1.  把这个URL直接填到 `edgetunnel` 的配置里。
2.  或者用 `ADDAPI` 变量的方式导入。

想了解更多细节？快去看看 `edgetunnel` 的官方文档吧：<https://github.com/cmliu/edgetunnel>

## 📖 `iptest.exe` 参数小抄

咱们的测速功能是靠 `iptest.exe` 这个神器。虽然脚本都帮你配好了，但如果你想自己研究下，可以看看这些参数是啥意思。

* `-file`: 告诉它要去测哪个文件里的IP。
* `-outfile`: 测完的结果存到哪里。
* `-max`: 一次同时测多少个IP，数字越大越快，也越吃电脑性能。
* `-speedtest`: 测速模式，`3`就是测下载和上传。
* `-speedlimit`: 速度太慢的IP就不要了，单位是MB/s。
* `-delay`: 延迟太高的IP也扔掉，单位是毫秒。
* `-url`: 用哪个网址来测试下载速度。

## 🙏 特别感谢

这个项目能做出来，离不开下面这些大佬和项目的帮助，真心感谢他们！

* **yutian**: 感谢他开发的超牛的 `IP-SpeedTest` 工具！
    * **GitHub**: <https://github.com/yutian81>
* **cmliu**: 感谢他的各种骚操作和 `edgetunnel` 项目！
    * **GitHub**: <https://github.com/cmliu>
    * **Telegram 频道**: <https://t.me/zip_cm_edu_kg>
