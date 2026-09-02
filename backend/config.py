# -*- coding: utf-8 -*-
"""全局配置。"""

import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
EASTMONEY_CODETABLE_API = "https://search-codetable.eastmoney.com/codetable/search/web"
EASTMONEY_SEARCH_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"

# 腾讯行情批量接口
TENCENT_QUOTE_API = "https://qt.gtimg.cn/q="

# 个股详情字段（fltt=2 返回浮点）
QUOTE_FIELDS = "f43,f44,f45,f46,f47,f48,f50,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171,f86"

# 批量行情字段（指数）
ULIST_FIELDS = "f12,f14,f2,f3,f4,f5,f6,f8,f9,f10,f15,f16,f17,f18,f20,f21,f22,f23,f100"

# 主要指数定义：
#   secid    - 东方财富 secid
#   tencent  - 腾讯行情代码（腾讯不支持的为 None，仅东财主源可获取）
#   name     - 显示名称
INDICES = {
    "cn": [
        {"secid": "1.000001", "tencent": "sh000001", "name": "上证指数"},
        {"secid": "0.399001", "tencent": "sz399001", "name": "深证成指"},
        {"secid": "1.000300", "tencent": "sh000300", "name": "沪深300"},
        {"secid": "0.399006", "tencent": "sz399006", "name": "创业板指"},
        {"secid": "1.000688", "tencent": "sh000688", "name": "科创50"},
        {"secid": "0.899050", "tencent": "bj899050", "name": "北证50"},
    ],
    "asia": [
        {"secid": "100.N225", "tencent": None, "name": "日经225"},
        {"secid": "100.KS11", "tencent": None, "name": "韩国KOSPI"},
        {"secid": "100.AXJO", "tencent": None, "name": "澳洲ASX200"},
        {"secid": "100.HSI", "tencent": "hkHSI", "name": "恒生指数"},
        {"secid": "100.HSTECH", "tencent": "hkHSTECH", "name": "恒生科技"},
        {"secid": "100.HSCEI", "tencent": "hkHSCEI", "name": "国企指数"},
        {"secid": "100.TWSE", "tencent": None, "name": "台湾加权"},
    ],
    "us": [
        {"secid": "100.DJIA", "tencent": "usDJI", "name": "道琼斯"},
        {"secid": "100.NDX", "tencent": "usIXIC", "name": "纳斯达克100"},
        {"secid": "100.SPX", "tencent": "usINX", "name": "标普500"},
    ],
    "futures": [
        {"secid": "113.IF00Y", "tencent": None, "name": "沪深300股指"},
        {"secid": "113.IH00Y", "tencent": None, "name": "上证50股指"},
        {"secid": "113.IC00Y", "tencent": None, "name": "中证500股指"},
        {"secid": "113.IM00Y", "tencent": None, "name": "中证1000股指"},
        {"secid": "113.AU00Y", "tencent": None, "name": "黄金期货"},
        {"secid": "113.SC00Y", "tencent": None, "name": "原油期货"},
    ],
}

# 市场切换文案
MARKET_LABELS = {"cn": "A股", "asia": "亚太", "us": "美股", "futures": "期货"}
