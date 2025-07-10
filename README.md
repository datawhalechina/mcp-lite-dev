# 《MCP极简开发》项目代码

本项目主要包括《MCP极简开发》的第6章代码。

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
MODEL=Pro/deepseek-ai/DeepSeek-V3
API_KEY=YOUR_API_KEY
```
