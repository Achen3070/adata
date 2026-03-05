#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试频率限制功能
"""
import time
from adata.common.utils import RateLimiter, requests

print("=== 测试频率限制功能 ===")

print("\n1. 测试基本功能")
test_url = "https://httpbin.org/get"
print(f"请求URL: {test_url}")

# 设置默认限制为 5 次/分钟方便测试
RateLimiter.set_default_limit(5)

start_time = time.time()
for i in range(7):
    print(f"发起第 {i+1} 次请求...")
    res = requests.get(test_url)
    print(f"  响应状态码: {res.status_code}")
end_time = time.time()

print(f"\n总耗时: {end_time - start_time:.2f} 秒")
print("（如果前5次请求很快，第6次和第7次请求有等待，说明频率限制工作正常）")

print("\n2. 测试域名级别的限制")
# 为特定域名设置不同的限制
RateLimiter.set_domain_limit("httpbin.org", 3)
print("设置 httpbin.org 限制为 3 次/分钟")

start_time = time.time()
for i in range(5):
    print(f"发起第 {i+1} 次请求到 httpbin.org...")
    res = requests.get(test_url)
    print(f"  响应状态码: {res.status_code}")
end_time = time.time()

print(f"\n总耗时: {end_time - start_time:.2f} 秒")
print("\n测试完成！")
