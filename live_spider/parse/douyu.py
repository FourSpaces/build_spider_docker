# -*- coding: utf-8 -*-
import re
import json
import datetime
from urllib.parse import urljoin
from scrapy.selector import Selector

"""
解析斗鱼爬虫数据
"""

class douyu(object):

    @classmethod
    def anchor_list(cls, html, url):

        try:
            json_obj = json.loads(html)
        except Exception:
            pass

        status_code = json_obj.get('code')
        if status_code == 0:
            # 解析数据
            data = json_obj.get('data', {}).get('list')
            anchor_list = []
            anchor_list_serial = []

            for item in data:
                anchor = {}
                room_id = item.get('rid')
                anchor['rid'] = '{}_dy'.format(room_id)
                anchor['room_id'] = room_id
                anchor['room_name'] = item.get('roomName')
                anchor['room_src'] = item.get('roomSrc')
                anchor['nickname'] = item.get('nickname')
                anchor['owner_uid'] = item.get('owner_uid')
                anchor['avatar'] = item.get('avatar')
                anchor['is_vertical'] = item.get('isVertical')  # 是否竖屏
                anchor['cate_name'] = item.get('')
                anchor['hn'] = item.get('hn')
                anchor['platform'] = 'douyu'
                anchor['is_live'] = item.get('isLive')      # 在直播 为1 , 否则为 0
                anchor['scheme_url'] = 'douyutvtest://platformapi/startApp?room_id={}&isVertical=0'.format(room_id)

                anchor_list.append(anchor)

                item['rid'] = '{}_dy'.format(room_id)
                item['room_id'] = room_id
                item['platform'] = 'douyu'
                anchor_list_serial.append(item)

            return anchor_list, anchor_list_serial
        else:
            return None, None



