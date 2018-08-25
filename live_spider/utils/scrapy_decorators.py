# -*- coding: utf-8 -*-

import re
import logging
from scrapy.http import Response
from functools import wraps


class retry_request(object):
    """
    重新发送request的装饰器
    """

    def __init__(self, pattern, settings):
        """
        符合正则表达式的响应请求将被重发。响应内容为空时，也会被重发。
        :param pattern: 正则表达式，eg: r'请登录[\w|W]+'
        :param settings: settings配置列表
        occasion： 装饰在请求响应函数上，带有Response对象的函数。
        EG:
        ``` python
        import scrapy
        from scrapy.utils.project import get_project_settings

        class myspdier(scrapy.spider):
            ...

            @retry_request(r'请登录[\w|W]+', get_project_settings())
            def parse(self, response):
                pass

        ```

        """

        self.logger = logging.getLogger(__name__)
        self.pattern = pattern
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    def __call__(self, func):

        @wraps(func)
        def wrapped_function(*args, **kwargs):
            # 匹配正则, 符合的直接 yield 出一个对象

            if len(args) == 2 and issubclass(args[1].__class__, Response):
                response = args[1]
                if not response.text or re.search(self.pattern, response.text) and self.pattern:
                    yield self.retry_request(response.request, self.max_retry_times, self.retry_priority_adjust)
                else:
                    yield from func(*args, **kwargs)
        return wrapped_function

    def retry_request(self, request, max_retry_times, retry_priority_adjust=-1):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = max_retry_times
        priority_adjust = retry_priority_adjust

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        if retries <= retry_times:
            self.logger.debug(" _ Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': retry_times})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + priority_adjust

            # if isinstance(reason, Exception):
            #     reason = global_object_name(reason.__class__)

            # stats.inc_value('retry/count')
            # stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            # stats.inc_value('retry/max_reached')
            self.logger.debug(" _ Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': retry_times})
