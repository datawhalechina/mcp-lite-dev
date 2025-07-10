<div align=center>
<h1>《MCP极简开发》学习笔记</h1>
</div>

本项目基于Datawhale组队学习的共读《MCP极简开发》课程，主要包括学习笔记和项目代码。

项目地址：https://github.com/datawhalechina/mcp-lite-dev

## 环境安装

1. 基础环境：Python3.10+

2. 安装UV
```shell
pip install uv
set UV_INDEX=https://mirrors.aliyun.com/pypi/simple
```

3. 安装Python依赖包
```shell
uv sync --python 3.10 --all-extras
```

4. 切换到本地环境(.venv)
```shell
cd .venv/Scripts
activate
```

## 配置文件

1. 访问[openweathermap网站](https://openweathermap.org/)，注册账号，获取API KEY

2. 在项目根目录下新建`.env`文件，并添加以下内容
```text
OPENWEATHER_API_KEY=YOUR_API_KEY
```

3. 访问[硅基流动网站]()，注册账号，获取API KEY  
**注：书中使用的是deepseek，我们使用硅基流动的模型，其实效果是一样的。**

4. 在项目根目录下新建`.env`文件，并添加以下内容
```text
BASE_URL=https://api.siliconflow.cn/v1
MODEL=deepseek-ai/DeepSeek-V3
API_KEY=YOUR_API_KEY
```

## 项目协作安排

| 章节号 |           标题           | 进度  |    负责人    |
|:---:| :----------------------: |:---:|:---------:| 
|  1  | 快速了解MCP         | 进行中 |     -     | 
|  2  | MCP核心原理                 | 进行中 |    年轻人    |
|  3  | MCP的安全问题                | 进行中 |    易华挥    | 
|  6  | 动手写一个MCP            | 进行中 | The Flash |
|  7  | MCP开发进阶                 |  进行中   |     -     |

## 致谢

**核心贡献者**
- [胡锐锋-项目负责人](https://github.com/Relph1119) （Datawhale成员-华东交通大学-系统架构设计师）

**其他**
1. 特别感谢 [@Sm1les](https://github.com/Sm1les)、[@LSGOMYP](https://github.com/LSGOMYP) 对本项目的帮助与支持；

## 阅读提示

### 第7.2.2节 MCP Server的上线发布

1. 请登录[PyPI官方网站](https://pypi.org/)注册账号。

2. 访问[PyPI官网-我的账户](https://pypi.org/manage/account/)创建API token。

3. 在项目根目录下执行以下命令，进行项目打包和上传发布，需要使用到API token：
```shell
python -m build
python -m twine upload dist/*
```

## 关注我们

<div align=center>
<p>扫描下方二维码关注公众号：Datawhale</p>
<img src="https://raw.githubusercontent.com/datawhalechina/pumpkin-book/master/res/qrcode.jpeg" width = "180" height = "180">
</div>