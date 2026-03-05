# -*- coding: utf-8 -*-
"""
代理:https://jahttp.zhimaruanjian.com/getapi/

@desc: adata 请求工具类
@author: 1nchaos
@time:2023/3/30
@log: 封装请求次数
"""

import threading
import time
from urllib.parse import urlparse

import requests


class RateLimiter:
    """
    域名频率限制器
    控制同一个域名的请求频率，默认每分钟30次
    """
    def __init__(self, default_max_requests: int = 30, time_window: int = 60):
        """
        :param default_max_requests: 默认每分钟最大请求次数
        :param time_window: 时间窗口（秒），默认60秒
        """
        self.default_max_requests = default_max_requests
        self.time_window = time_window
        self._domain_limits = {}  # 域名 -> 最大请求次数
        self._domain_requests = {}  # 域名 -> [(timestamp, count), ...]
        self._lock = threading.Lock()

    def set_limit(self, domain: str, max_requests: int):
        """
        设置指定域名的请求频率限制
        :param domain: 域名，如 "api.example.com"
        :param max_requests: 每分钟最大请求次数
        """
        with self._lock:
            self._domain_limits[domain] = max_requests

    def get_limit(self, domain: str) -> int:
        """
        获取指定域名的请求频率限制
        """
        return self._domain_limits.get(domain, self.default_max_requests)

    def acquire(self, url: str):
        """
        获取请求许可，如果超过频率限制则等待
        :param url: 请求URL
        """
        domain = urlparse(url).netloc
        if not domain:
            return

        max_requests = self.get_limit(domain)

        with self._lock:
            now = time.time()
            window_start = now - self.time_window

            # 获取该域名的请求记录
            requests_list = self._domain_requests.get(domain, [])
            # 清理过期的记录
            requests_list = [ts for ts in requests_list if ts > window_start]

            # 检查是否超过限制
            if len(requests_list) >= max_requests:
                # 需要等待的时间
                oldest_request = requests_list[0]
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
                    window_start = now - self.time_window
                    requests_list = [ts for ts in requests_list if ts > window_start]

            # 记录本次请求
            requests_list.append(now)
            self._domain_requests[domain] = requests_list


class SunProxy(object):
    _data = {}
    _instance_lock = threading.Lock()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(SunProxy, "_instance"):
            with SunProxy._instance_lock:
                if not hasattr(SunProxy, "_instance"):
                    SunProxy._instance = object.__new__(cls)

    @classmethod
    def set(cls, key, value):
        cls._data[key] = value

    @classmethod
    def get(cls, key):
        return cls._data.get(key)

    @classmethod
    def delete(cls, key):
        if key in cls._data:
            del cls._data[key]


class SunRequests(object):
    _rate_limiter = RateLimiter(default_max_requests=30, time_window=60)

    def __init__(self, sun_proxy: SunProxy = None) -> None:
        super().__init__()
        self.sun_proxy = sun_proxy

    @classmethod
    def set_rate_limit(cls, domain: str, max_requests: int):
        """
        设置指定域名的请求频率限制
        :param domain: 域名，如 "api.example.com"
        :param max_requests: 每分钟最大请求次数
        """
        cls._rate_limiter.set_limit(domain, max_requests)

    @classmethod
    def set_default_rate_limit(cls, max_requests: int):
        """
        设置默认的请求频率限制（所有域名）
        :param max_requests: 每分钟最大请求次数
        """
        cls._rate_limiter.default_max_requests = max_requests

    def request(self, method='get', url=None, times=3, retry_wait_time=1588, proxies=None, wait_time=None, **kwargs):
        """
        简单封装的请求，参考requests，增加循环次数和次数之间的等待时间
        :param proxies: 代理配置
        :param method: 请求方法： get；post
        :param url: url
        :param times: 次数，int
        :param retry_wait_time: 重试等待时间，毫秒
        :param wait_time: 等待时间：毫秒；表示每个请求的间隔时间，在请求之前等待sleep，主要用于防止请求太频繁的限制。
        :param kwargs: 其它 requests 参数，用法相同
        :return: res
        """
        # 1. 频率限制检查
        if url:
            self._rate_limiter.acquire(url)
        # 2. 获取设置代理
        proxies = self.__get_proxies(proxies)
        # 3. 请求数据结果
        res = None
        for i in range(times):
            if wait_time:
                time.sleep(wait_time / 1000)
            res = requests.request(method=method, url=url, proxies=proxies, **kwargs)
            if res.status_code in (200, 404):
                return res
            time.sleep(retry_wait_time / 1000)
            if i == times - 1:
                return res
        return res

    def __get_proxies(self, proxies):
        """
        获取代理配置
        """
        if proxies is None:
            proxies = {}
        is_proxy = SunProxy.get('is_proxy')
        ip = SunProxy.get('ip')
        proxy_url = SunProxy.get('proxy_url')
        if not ip and is_proxy and proxy_url:
            ip = requests.get(url=proxy_url).text.replace('\r\n', '') \
                .replace('\r', '').replace('\n', '').replace('\t', '')
        if is_proxy and ip:
            proxies = {'https': f"http://{ip}", 'http': f"http://{ip}"}
        return proxies


sun_requests = SunRequests()
