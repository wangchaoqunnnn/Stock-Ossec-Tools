# -*- coding: utf-8 -*-
"""全局配置。"""

import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 预置关注清单（股票代码池）
WATCH_LIST_PATH = os.path.join(BASE_DIR, "data", "watch_list.json")

# 前端构建产物目录（生产模式静态托管）
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

# 上游行情缓存时间（秒）
CACHE_TTL = 10

# 上游接口超时（秒）
UPSTREAM_TIMEOUT = 8

# 东方财富公开接口
EASTMONEY_QUOTE_API = "https://push2.eastmoney.com/api/qt/stock/get"
EASTMONEY_ULIST_API = "https://push2.eastmoney.com/api/qt/ulist.np/get"
EASTMONEY_SEARCH_API = "https://searchapi.eastmoney.com/api/suggest/get"
EASTMONEY_SEARCH_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"

# 个股详情字段（fltt=2 返回浮点）
QUOTE_FIELDS = "f43,f44,f45,f46,f47,f48,f50,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171,f86"

# 批量行情字段（关注清单 / 指数）
ULIST_FIELDS = "f12,f14,f2,f3,f4,f5,f6,f8,f9,f10,f15,f16,f17,f18,f20,f21,f22,f23,f100"

# 主要指数定义（secid -> 名称）
INDICES = {
    "cn": [
        {"secid": "1.000001", "name": "上证指数"},
        {"secid": "0.399001", "name": "深证成指"},
        {"secid": "1.000300", "name": "沪深300"},
        {"secid": "0.399006", "name": "创业板指"},
        {"secid": "1.000688", "name": "科创50"},
        {"secid": "0.899050", "name": "北证50"},
    ],
    "hk": [
        {"secid": "100.HSI", "name": "恒生指数"},
        {"secid": "100.HSTECH", "name": "恒生科技"},
        {"secid": "100.HSCEI", "name": "国企指数"},
    ],
    "us": [
        {"secid": "100.DJIA", "name": "道琼斯"},
        {"secid": "100.NDX", "name": "纳斯达克100"},
        {"secid": "100.SPX", "name": "标普500"},
    ],
}

# 市场切换文案
MARKET_LABELS = {"cn": "A股", "hk": "港股", "us": "美股"}
