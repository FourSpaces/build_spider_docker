# -*- coding:utf-8 -*-
import re
from math import log10
from functools import wraps
from traceback import format_exc


def try_except(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            print(format_exc())
    return wrapped_function


class BassClass(object):

    def build_redis_dict(self, key, value, plug='sadd', pipeline=False):
        """
        生产 reids 字典
        :param key:
        :param value:
        :param plug:
        :param pipeline:
        :return: 生成的redis 字典
        """
        return {'type': 'redis', 'data': {'key': key, 'value': value, 'plug': plug, 'pipeline': pipeline}}

    def build_redis_dict_list(self, list, plug='sadd', pipeline=False):

        return_dict = {'type': 'redis', 'data': []}
        for item in list:
            plug = item.get('plug') if item.get('plug') else plug
            pipeline = item.get('pipeline') if item.get('pipeline') else pipeline
            dict_list = {'key': item['key'], 'value': item['value'], 'plug': plug, 'pipeline': pipeline}
            return_dict['data'].append(dict_list)

        return return_dict

    def resend_request(self, response, RETRY_TIMES):
        # 获取response请求内的request 对象
        request = response.request

        number = request.meta.get('retry_times', 0)
        #
        if number > RETRY_TIMES:
            return None
        else:
            request.meta.pop('proxy')
            #request.meta.pop('depth')
            request.meta.pop('download_timeout')
            request.meta.pop('download_slot')
            request.meta.pop('download_latency')
            request.dont_filter = True

            request.meta.update({'retry_times': number+1})
            return request

    def add_prefix_rediskey(self, prefix):
        for it in [item for item in dir(self) if 'redis_' == item[:6] and 'key' in item]:
            self.__setattr__(it, prefix + '_' + self.__getattribute__(it))



class GeoHash(object):

    #  Note: the alphabet in geohash differs from the common base32
    #  alphabet described in IETF's RFC 4648
    #  (http://tools.ietf.org/html/rfc4648)
    __base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
    __decodemap = { }
    for i in range(len(__base32)):
        __decodemap[__base32[i]] = i
    del i

    @classmethod
    def decode_exactly(cls, geohash):
        """
        Decode the geohash to its exact values, including the error
        margins of the result.  Returns four float values: latitude,
        longitude, the plus/minus error for latitude (as a positive
        number) and the plus/minus error for longitude (as a positive
        number).
        """
        lat_interval, lon_interval = (-90.0, 90.0), (-180.0, 180.0)
        lat_err, lon_err = 90.0, 180.0
        is_even = True
        for c in geohash:
            cd = cls.__decodemap[c]
            for mask in [16, 8, 4, 2, 1]:
                if is_even: # adds longitude info
                    lon_err /= 2
                    if cd & mask:
                        lon_interval = ((lon_interval[0]+lon_interval[1])/2, lon_interval[1])
                    else:
                        lon_interval = (lon_interval[0], (lon_interval[0]+lon_interval[1])/2)
                else:      # adds latitude info
                    lat_err /= 2
                    if cd & mask:
                        lat_interval = ((lat_interval[0]+lat_interval[1])/2, lat_interval[1])
                    else:
                        lat_interval = (lat_interval[0], (lat_interval[0]+lat_interval[1])/2)
                is_even = not is_even
        lat = (lat_interval[0] + lat_interval[1]) / 2
        lon = (lon_interval[0] + lon_interval[1]) / 2
        return lat, lon, lat_err, lon_err

    @classmethod
    def decode(cls, geohash):
        """
        Decode geohash, returning two strings with latitude and longitude
        containing only relevant digits and with trailing zeroes removed.
        """
        lat, lon, lat_err, lon_err = cls.decode_exactly(geohash)
        # Format to the number of decimals that are known
        lats = "%.*f" % (max(1, int(round(-log10(lat_err)))) - 1, lat)
        lons = "%.*f" % (max(1, int(round(-log10(lon_err)))) - 1, lon)
        if '.' in lats: lats = lats.rstrip('0')
        if '.' in lons: lons = lons.rstrip('0')
        return lats, lons

    @classmethod
    def encode(cls, latitude, longitude, precision=12):
        """
        Encode a position given in float arguments latitude, longitude to
        a geohash which will have the character count precision.
        """
        lat_interval, lon_interval = (-90.0, 90.0), (-180.0, 180.0)
        geohash = []
        bits = [ 16, 8, 4, 2, 1 ]
        bit = 0
        ch = 0
        even = True
        while len(geohash) < precision:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if longitude > mid:
                    ch |= bits[bit]
                    lon_interval = (mid, lon_interval[1])
                else:
                    lon_interval = (lon_interval[0], mid)
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if latitude > mid:
                    ch |= bits[bit]
                    lat_interval = (mid, lat_interval[1])
                else:
                    lat_interval = (lat_interval[0], mid)
            even = not even
            if bit < 4:
                bit += 1
            else:
                geohash += cls.__base32[ch]
                bit = 0
                ch = 0
        return ''.join(geohash)


class Conditionlist(object):
    # 模版URL
    templet = ''

    # 次序优先级
    # 生成排序

    def __init__(self, param_dict, push_sort, print_sour=None):
        #self.templet = templet
        self.param_dict = param_dict
        self.push_sort_dict = dict(zip(list(range(len(push_sort))), push_sort))
        self.push_sort = push_sort
        self.push_sort_len = len(push_sort)

    #@try_except
    def build_condition(self, url):
        tab_list = []
        for tab in self.get_new_tab(url):
            tab_list.append("{}{}".format(tab, url))
        return tab_list

    def get_new_tab(self, url):
        # 遍历出url 中的规则
        try:
            if url:
                ss = {item[0]: item[1].groups()
                      for item in map(lambda x: (x[0], re.search(x[1], url)), self.push_sort_dict.items()) if item[1]}
                max = list(ss.keys())
                max.sort()
                max = max[-1]
            else:
                max = -1
        except Exception:
            format_exc()
        finally:
            if max < (self.push_sort_len - 1):
                return self.param_dict.get(self.push_sort[max+1])
            else:
                return []


if __name__ == "__main__":

    param_dict = {
        'l[1-5]': ['l1', 'l2', 'l3', 'l4', 'l5'],
        'a[1-8]': ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8'],
        'lc[1-5]': ['lc1', 'lc2', 'lc3', 'lc4', 'lc5'],
        'f[1-5]': ['f1', 'f2', 'f3', 'f4', 'f5']
    }

    push_sort = ['lc[1-5]', 'a[1-8]', 'l[1-5]', 'f[1-5]']

    sss = Conditionlist(param_dict, push_sort)
    for url in ['', 'lc1', 'lc2a6', 'f2', 'lc6a7', 'lc6f2']:
        sss.build_condition(url)

