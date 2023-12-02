# 使用Ubuntu 20.04作为基础镜像
FROM ubuntu:20.04

ADD sources.list /etc/apt

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip
# 设置工作目录
WORKDIR /app

# 复制应用程序代码到容器
COPY wangyang.py /app
COPY requirements.txt /app

RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install --upgrade pip

# 安装Python依赖
RUN pip3 install -r requirements.txt


# 暴露端口
EXPOSE 9527
EXPOSE 9528
EXPOSE 9529
EXPOSE 80
EXPOSE $port
EXPOSE $id

CMD ["python3", "wangyang.py"]
