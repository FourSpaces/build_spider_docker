# -*- coding:utf-8 -*-

import logging
import redis
from datetime import datetime
from pymongo import TEXT, ASCENDING, MongoClient
from scrapy.utils.project import get_project_settings
from traceback import format_exc
from scrapy.conf import settings
from twisted.internet import reactor


class MongoPipeline(object):

    def __init__(self, mongo_url, tableinfo):

        self.mg_url = mongo_url
        self.client = MongoClient(self.mg_url).get_database()

        self.table_list = list(tableinfo.keys())
        self.table_info = tableinfo
        self.key_id_dict = {}
        self.names = {}
        self.bulk = {}
        self.bulk_nums = {}
        self.bulk_limit = 20

    def initialization(self, tablelist):
        """
        初始化Mongo管道模块
        :param tablelist: 
        :return: 
        """

        for table_name in tablelist:
            self.names.update({table_name: table_name})
            self.bulk.update({table_name: self.client[table_name].initialize_unordered_bulk_op()})
            self.bulk_nums.update({table_name: 0})

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGODB_URL'),
            tableinfo=crawler.settings.get('MONGODB_TABS'),
        )

    def open_spider(self, spider):
        self.initialization(self.table_list)

        # 创建索引
        for tabname, tabindex in self.table_info.items():
            index = True
            for key_id, value in tabindex:
                self.client[tabname].ensure_index(key_id, unique=value)
                if index:
                    self.key_id_dict.update({tabname: key_id})
                index = False

    def close_spider(self, spider):
        # 关闭爬虫前，清理管道中的数据
        for table_name in self.table_list:
            self.bulk[table_name] = self.bulk_execute_db(self.bulk_nums[table_name], self.bulk_limit,
                                                         self.bulk[table_name], self.client[table_name], False)

    def process_item(self, item, spider):
        class_name = item.__class__.__name__
        collection = self.names[class_name] if class_name not in 'dict' else self.names.get(item.get('type', ''), '')

        try:

            if collection in self.table_list and item.get('data'):
                # 获取唯一ID 的名字
                operating = item.get('operating', 'INSERT')
                if operating in 'UPDATE':
                    self.update_db(collection, self.key_id_dict.get(collection), item.get('data'))
                elif operating in 'INSERT':
                    self.insert_db(collection, item.get('data'))
                elif operating in 'UPDATE&INSERT' or operating in 'INSERT&UPDATE':
                    self.update_db(collection, self.key_id_dict.get(collection), item.get('data'))
                    self.insert_db(collection+'_serial', item.get('data'))

        except Exception:
            logging.error(format_exc())
        return item

    def update_db(self, collection, id, datas):

        if isinstance(datas, list):
            # 更新数据
            bulk = self.client[collection].initialize_unordered_bulk_op()
            for item_data in datas:
                item_data['update_date'] = datetime.utcnow()
                bulk.find({id: item_data[id]}).upsert().update({'$set': dict(item_data),
                                                                '$setOnInsert': {
                                                                    'install_date': datetime.utcnow(),
                                                                              }})
            bulk.execute()
        elif isinstance(datas, dict):
            bulk = self.client[collection].initialize_unordered_bulk_op()
            bulk.find({id: datas[id]}).upsert().update({'$set': dict(datas),
                                                            '$setOnInsert': {
                                                                'install_date': datetime.utcnow(),
                                                            }})
            bulk.execute()

    def insert_db(self, collection, datas):
        """
        插入数据到库中
        :param collection: 
        :param datas: 
        :return: 
        """

        if isinstance(datas, list):
            self.client[collection].insert(datas)
        elif isinstance(datas, dict):
            self.client[collection].insert_one(datas)

    def bulk_execute_db(self, bulk_nums, bulk_limit, bulk_object, collection, tab=True):
        if (bulk_nums % bulk_limit == 0) == tab:
            re = bulk_object.execute()
            if re:
                bulk_object = collection.initialize_unordered_bulk_op()

        return bulk_object


class RedisPipeline(object):

    def __init__(self):
        settings = get_project_settings()
        self.redis_url = settings.get('REDIS_URL')
        self.pool = redis.ConnectionPool.from_url(self.redis_url)

    def open_spider(self, spider):
        self.redis_db = redis.StrictRedis(connection_pool=self.pool)
        self.adapters = {
            'sadd': self.redis_db.sadd,
            'lpush': self.redis_db.lpush,
            'delete': self.redis_db.delete,
        }
        logging.info("redis start")

    def close_spider(self, spider):
        logging.info("redis end")

    def process_item(self, item, spider):

        if item.get('type') == 'redis':
            try:
                self.operate_redis_list(item.get('data'))
            except Exception as a:
                logging.error(format_exc())

        return item

    def operate_redis(self, item):
        key = item.get('key')
        value = item.get('value')
        plug = item.get('plug')
        is_pipeline = item.get('pipeline', False)

        assert key, 'key can not be empty'
        assert plug and plug in self.adapters.keys(), 'plug can not be empty'
        if is_pipeline and isinstance(value, list):
            pipe = self.redis_db.pipeline()
            pipe_adapters = {
                'sadd': pipe.sadd,
                'lpush': pipe.lpush,
                'delete': pipe.delete,
            }

            for v in value:
                pipe_adapters[plug](key, v)
            pipe.execute()
        else:
            self.adapters[plug](key, value)

    def operate_redis_list(self, item_list):
        if isinstance(item_list, list):
            for item in item_list:
                self.operate_redis(item)
        else:
            self.operate_redis(item_list)