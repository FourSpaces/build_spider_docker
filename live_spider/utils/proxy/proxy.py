#!/usr/bin/env python3
# coding:utf-8
import os
import csv
import random
import time
import redis
import logging

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
BASIC_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
chlr = logging.StreamHandler() # 输出到控制台的handler
chlr.setFormatter(formatter)
chlr.setLevel('INFO')  # 也可以不设置，不设置就默认用logger的level
logger.addHandler(chlr)


class ProxyPools(object):

    def __init__(self):
        self.redis_url = ''
        self.up_time = 0
        self.ip_list = []

    def start(self):
        self.pool = redis.ConnectionPool.from_url(self.redis_url)
        self.redis = redis.StrictRedis(connection_pool=self.pool)
        logger.info('ProxyPools start')
        self.get_ip()

    def get_ip(self):
        if time.time() > self.up_time:
            self.ip_list = []
            self.synchronize()
            while not self.ip_list:
                logger.info('IP: %d , Waiting for IP recovery' % len(self.ip_list))
                time.sleep(6)
                self.synchronize()

            logger.info('Update IP: %d' % len(self.ip_list))
        ip = random.choice(self.ip_list)
        logger.info('give ip %s' % ip)
        return ip

    def synchronize(self):
        self.up_time = int(time.time()) + 25
        self.ip_list = [ip.decode() for ip in self.redis.keys()]

    def pop(self):
        return self.get_ip()
