# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 安装 Node.js 20.11.1
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 验证 Node.js 和 Python 版本
RUN node --version | grep "v20.11.1" \
    && python --version | grep "3.12"

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装 uv
RUN pip install uv

# 使用 uv 安装项目依赖
RUN uv sync

# 设置环境变量
ENV PYTHONUNBUFFERED=1



# 启动命令
CMD ["uv", "--directory","/app/xhs-mcp","run","main.py"]