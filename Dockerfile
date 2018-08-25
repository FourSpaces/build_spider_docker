FROM troycube/scrapyd-alpine:py3.6

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
# add the required dependencies
RUN apk add --no-cache build-base

# cache pip install
COPY ./requirements.txt /root/app/requirements.txt

RUN pip3 install --no-cache-dir -r /root/app/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY . /root/app/live_spider
WORKDIR /root/app/live_spider
RUN bash .tools/build_egg.sh /root/scrapyd/eggs

CMD ["bash", ".tools/start.sh"]
        