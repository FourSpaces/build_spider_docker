# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import logging
from scrapy.utils.project import get_project_settings
from ..utils.proxy.proxy import ProxyPools
logger = logging.getLogger(__name__)
# # 配置代理池
proxy_pool = ProxyPools()
proxy_pool.redis_url = get_project_settings().get('PROXY_POOL_REDIS_URL')
proxy_pool.start()


class HttpDownloaderMiddleware(object):

    def process_request(self, request,  spider):
        # 配置代理

        proxy_server = proxy_pool.pop()
        request.meta['proxy'] = 'http://{}'.format(proxy_server)

        pass
