# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from random import randint
from copy import deepcopy
from traceback import format_exc
from ..parse.douyu import douyu
from urllib.parse import urljoin, urlencode
from ..utils.scrapy_decorators import retry_request
from scrapy.utils.project import get_project_settings


class douyuSpider(scrapy.Spider):
    name = 'douyu_spider'
    allowed_domains = ['douyucdn.cn', 'douyucdn.com']
    start_urls = ['https://wxapp.douyucdn.cn/api/home/index']

    custom_settings = {
        'RETRY_TIMES': 8,
        'DOWNLOAD_TIMEOUT': 8,
        # 'DOWNLOAD_DELAY': 0.2,

        'USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 '
                      '(KHTML, like Gecko) Mobile/15E302 MicroMessenger/6.6.6 NetType/4G Language/zh_CN',
        'REDIS_START_URLS_AS_SET': True,
        'DEFAULT_REQUEST_HEADERS': {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Referer': 'https://servicewechat.com/wxca1e7ba3fe{}ff{}/2/page-frame.html'.format(randint(10, 99),
                                                                                               randint(10, 99)),
            'Accept-Language': 'zh-CN',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'live_spider.middlewares_.middlewares.HttpDownloaderMiddleware': 543,
        },
        'ITEM_PIPELINES': {
            'live_spider.pipelines_.public.MongoPipeline': 100,
        },

        'MONGODB_TABS': {
            'anchor_info': [('rid', True), ('room_id', False)],
            'anchor_info_serial': [('rid', False), ('room_id', False)],
            'anchor_info_primeval': [('rid', True), ('room_id', False)],
            # 'user-app': [('app_id', True)],
        },

        'REDIRECT_ENABLED': False,
        #'HTTPERROR_ALLOWED_CODES': [302],
        # 'LOG_LEVEL': 'INFO',
    }

    def parse(self, response):
        # 遍历发送数据
        for p in range(1, 11):
            yield from self.build_anchor_list(p)

    def build_anchor_list(self, p):
        url = "https://wxapp.douyucdn.cn/api/room/list?type=&page={}"
        yield scrapy.Request(url.format(p), meta={'page': p}, callback=self.parse_anchor_list)
        yield scrapy.Request(url.format(p+10), meta={'page': p+10}, callback=self.parse_anchor_list)

    @retry_request(r'"result"\s*:\s*\[\s?\]', get_project_settings())
    def parse_anchor_list(self, response):

        page = response.meta.get('page')
        anchor_list, anchor_list_serial = douyu.anchor_list(response.text, response.url)

        if anchor_list and anchor_list_serial:
            # 将数据 yield 到库中

            yield {'type': 'anchor_info', 'data': anchor_list, 'operating': 'UPDATE&INSERT'}
            yield {'type': 'anchor_info_primeval', 'data': anchor_list_serial, 'operating': 'UPDATE'}
            # 开始新的链接
            yield from self.build_anchor_list(page+10)
        else:
            logging.info('url: {}  page: {} end'.format(response.url, page))

        pass

    def parse_copy(self, response):

        if "category?type=" in response.url:
            # 解析直播分类
            try:
                live_class = json.loads(response.text)
                cate1Info = live_class.get('cate1Info')
                cate1dict = {cate.get('cate1Id'): cate.get('cate1Name') for cate in cate1Info}

                cate2Info = live_class.get('cate2Info')

                for cate in cate2Info:
                    cate['class_type'] = cate1dict.get(cate.get('cate1Id'))
                    meta = {}
                    meta['cate'] = deepcopy(cate)
                    yield self.build_roomlists_request(cate.get('shortName', ""), 1, meta)
                    yield self.build_roomlists_request(cate.get('shortName', ""), 2, meta)
            except Exception:
                logging.error(format_exc())

        elif "list/index" in response.url:
            yield self.build_roomlists_request("", 1, {})
            yield self.build_roomlists_request("", 2, {})

    @retry_request(r'"result"\s*:\s*\[\s?\]', get_project_settings())
    def parse_live_list_copy(self, response):

        # 解析直播列表
        try:
            json_data = json.loads(response.text)
            shortName = json_data.get('shortName')
            page_count = json_data.get('pageCount')
            nowPage = json_data.get('nowPage')

            #
            if int(nowPage) <= 2:
                # print('============= {}: {}'.format(shortName, page_count))
                # 遍历发送请求
                for p in range(2, int(page_count)+1):
                    meta = {}
                    meta['cate'] = deepcopy(response.meta.get('cate', {}))
                    yield self.build_roomlists_request(shortName, p, meta)

            # 解析组合数据 存储到数据库中
            result_date = json_data.get('result')
            anchor_list = []
            for result in result_date:
                result.update(response.meta.get('cate', {}))
                anchor_list.append(result)

            if anchor_list:
                yield {'type': 'douyu_anchor', 'data': anchor_list, 'operating': 'UPDATE&INSERT'}

        except Exception:
            logging.error(format_exc())

    def build_roomlists_request_copy(self, short_name, page, meta):

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "10",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://m.douyu.com",
            "Referer": "https://m.douyu.com/roomlists/jdqs",
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Mobile Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",

        }

        referer_url = "https://m.douyu.com/roomlists/{}".format(short_name)
        url = "https://m.douyu.com/roomlists"

        data = {'page': page, 'type': short_name}

        data_url = urlencode(data)

        headers['Referer'] = referer_url
        headers['Content-Length'] = "%d" % len(data_url)
        return scrapy.Request(url, method='POST', callback=self.parse_live_list, meta=meta, body=data_url,
                             headers=headers)


class douyuApiSpider(scrapy.Spider):
    name = 'douyu_api_spider'
    allowed_domains = ['douyucdn.cn']
    start_urls = ['https://m.douyu.com/list/index']

    url_stencil = 'http://open.douyucdn.cn/api/RoomApi/live?limit={}&offset={}'

    custom_settings = {
        'RETRY_TIMES': 10,
        'DOWNLOAD_DELAY': 0.2,
        'RETRY_HTTP_CODES': [502, 503, 504, 400, 408, 302],

        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/63.0.3239.84 Safari/537.36',
        'REDIS_START_URLS_AS_SET': True,
        'DEFAULT_REQUEST_HEADERS': {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': 1,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'live_spider.middlewares_.middlewares.HttpDownloaderMiddleware': 543,
        },
        'ITEM_PIPELINES': {
            'live_spider.pipelines_.public.MongoPipeline': 100,
        },
        'REDIRECT_ENABLED': False,
        #'HTTPERROR_ALLOWED_CODES': [500],
    }

    def make_requests_from_url(self, url):
        return scrapy.Request(self.url_stencil.format(100, 0), meta={'page': 0, 'limit': 100})

    def parse(self, response):
        #
        meta = response.meta

        page = meta.get('page')
        limit = meta.get('limit')

        try:
            result = json.loads(response.text)

            result_date = result.get('data')
            # data_len = len(result_date)
            if result_date:
                yield {'type': 'douyu_anchor', 'data': result_date, 'operating': 'UPDATE'}
        except Exception:
            logging.error(format_exc())

        finally:
            if not page % 3:
                for p in range(page + 1, page + 11):
                    meta = {'page': p, 'limit': limit}
                    yield scrapy.Request(self.url_stencil.format(limit, p * limit), meta=meta)

        # 解析数据











