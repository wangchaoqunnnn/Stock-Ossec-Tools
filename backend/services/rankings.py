# -*- coding: utf-8 -*-
"""行情中枢数据源：市场涨跌分布、行业资金流向、股票榜单。

数据来自东方财富公开接口（push2 clist / push2ex 涨跌分布）。
这些接口仅东财提供，暂无腾讯回退；失败时返回空/None，由调用方降级处理。
"""

from typing import Any, Dict, List, Optional

from .cache import TTLCache
from .eastmoney import DataSourceError, _get, _num

try:  # python -m backend.services.rankings（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config


class RankingsService(object):
    """行情中枢数据服务（带短缓存）。"""

    _CLIST_API = "https://push2.eastmoney.com/api/qt/clist/get"
    _DIST_API = "https://push2ex.eastmoney.com/getTopicZDFenBu"
    # A 股范围（沪深京）
    _A_SHARE_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
    # 行业板块（剔除部分特殊板块）
    _INDUSTRY_FS = "m:90+t:2+f:!50"
    _CONCEPT_FS = "m:90+t:3+f:!50"

    def __init__(self) -> None:
        self._cache = TTLCache(ttl=config.CACHE_TTL)

    # ------------------------------------------------------------------
    # 市场涨跌分布
    # ------------------------------------------------------------------
    def market_breadth(self) -> Optional[dict]:
        """市场涨跌家数分布（上涨/下跌/平盘/涨停/跌停 + 分档分布）。

        返回 None 表示上游不可用。
        """
        key = "breadth"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            payload = _get(
                self._DIST_API,
                {"ut": "7eea3edcaed734bea9cbfc24409ed989", "dpt": "wz.ztzt"},
            )
        except DataSourceError:
            return None

        data = (payload or {}).get("data") or {}
        fenbu = data.get("fenbu") or []
        up = down = flat = limit_up = limit_down = 0
        dist = {}  # 涨跌幅档位 -> 家数
        for item in fenbu:
            for k, v in (item or {}).items():
                try:
                    kk = int(k)
                    vv = int(v)
                except (TypeError, ValueError):
                    continue
                dist[kk] = vv
                if kk > 0:
                    up += vv
                elif kk < 0:
                    down += vv
                else:
                    flat += vv
                if kk >= 10:
                    limit_up += vv
                if kk <= -10:
                    limit_down += vv

        total = up + down + flat
        result = {
            "up": up,
            "down": down,
            "flat": flat,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "total": total,
            "dist": dist,
        }
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 行业资金流向
    # ------------------------------------------------------------------
    def industry_flow(self, limit: int = 20) -> List[dict]:
        """行业主力资金净流入排名（按净流入降序）。"""
        limit = max(5, min(50, int(limit or 20)))
        key = "indflow:%d" % limit
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            payload = _get(
                self._CLIST_API,
                {
                    "pn": 1,
                    "pz": limit,
                    "po": 1,
                    "np": 1,
                    "fltt": "2",
                    "invt": "2",
                    "fid": "f62",
                    "fs": self._INDUSTRY_FS,
                    "fields": "f12,f14,f2,f3,f62,f184",
                },
            )
        except DataSourceError:
            return []

        diff = (((payload or {}).get("data") or {}).get("diff")) or []
        result = []
        for row in diff:
            result.append(
                {
                    "code": str(row.get("f12") or ""),
                    "name": str(row.get("f14") or ""),
                    "price": _num(row.get("f2")),
                    "pct": _num(row.get("f3")),
                    "net_inflow": _num(row.get("f62")),
                    "net_ratio": _num(row.get("f184")),
                }
            )
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 概念资金流向
    # ------------------------------------------------------------------
    def concept_flow(self, limit: int = 20) -> List[dict]:
        """概念主力资金净流入排名（按净流入降序）。"""
        limit = max(5, min(50, int(limit or 20)))
        key = "conflow:%d" % limit
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            payload = _get(
                self._CLIST_API,
                {
                    "pn": 1,
                    "pz": limit,
                    "po": 1,
                    "np": 1,
                    "fltt": "2",
                    "invt": "2",
                    "fid": "f62",
                    "fs": self._CONCEPT_FS,
                    "fields": "f12,f14,f2,f3,f62,f184",
                },
            )
        except DataSourceError:
            return []

        diff = (((payload or {}).get("data") or {}).get("diff")) or []
        result = []
        for row in diff:
            result.append(
                {
                    "code": str(row.get("f12") or ""),
                    "name": str(row.get("f14") or ""),
                    "price": _num(row.get("f2")),
                    "pct": _num(row.get("f3")),
                    "net_inflow": _num(row.get("f62")),
                    "net_ratio": _num(row.get("f184")),
                }
            )
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 个股资金流向
    # ------------------------------------------------------------------
    def stock_flow(self, limit: int = 20) -> List[dict]:
        """个股主力资金净流入排名（按净流入降序）。"""
        limit = max(5, min(50, int(limit or 20)))
        key = "stockflow:%d" % limit
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            payload = _get(
                self._CLIST_API,
                {
                    "pn": 1,
                    "pz": limit,
                    "po": 1,
                    "np": 1,
                    "fltt": "2",
                    "invt": "2",
                    "fid": "f62",
                    "fs": self._A_SHARE_FS,
                    "fields": "f12,f14,f2,f3,f62,f184",
                },
            )
        except DataSourceError:
            return []

        diff = (((payload or {}).get("data") or {}).get("diff")) or []
        result = []
        for row in diff:
            result.append(
                {
                    "code": str(row.get("f12") or ""),
                    "name": str(row.get("f14") or ""),
                    "price": _num(row.get("f2")),
                    "pct": _num(row.get("f3")),
                    "net_inflow": _num(row.get("f62")),
                    "net_ratio": _num(row.get("f184")),
                }
            )
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 股票榜单
    # ------------------------------------------------------------------
    _RANK_KINDS = {
        "gainers": ("f3", 1),   # 涨幅榜（按涨跌幅降序）
        "losers": ("f3", 0),    # 跌幅榜（按涨跌幅升序）
        "amount": ("f6", 1),    # 成交额榜
        "turnover": ("f8", 1),  # 换手率榜
    }

    def stock_rank(self, sort: str = "gainers", limit: int = 20) -> List[dict]:
        """股票榜单。sort: gainers / losers / amount / turnover。"""
        limit = max(5, min(100, int(limit or 20)))
        fid, po = self._RANK_KINDS.get(sort, ("f3", 1))
        key = "rank:%s:%d" % (sort, limit)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            payload = _get(
                self._CLIST_API,
                {
                    "pn": 1,
                    "pz": limit,
                    "po": po,
                    "np": 1,
                    "fltt": "2",
                    "invt": "2",
                    "fid": fid,
                    "fs": self._A_SHARE_FS,
                    "fields": "f12,f14,f2,f3,f5,f6,f8,f9,f10,f20,f23,f100",
                },
            )
        except DataSourceError:
            return []

        diff = (((payload or {}).get("data") or {}).get("diff")) or []
        result = []
        for row in diff:
            result.append(
                {
                    "code": str(row.get("f12") or ""),
                    "name": str(row.get("f14") or ""),
                    "price": _num(row.get("f2")),
                    "pct": _num(row.get("f3")),
                    "volume": _num(row.get("f5")),
                    "amount": _num(row.get("f6")),
                    "turnover": _num(row.get("f8")),
                    "pe": _num(row.get("f9")),
                    "volume_ratio": _num(row.get("f10")),
                    "total_mv": _num(row.get("f20")),
                    "pb": _num(row.get("f23")),
                    "industry": str(row.get("f100") or ""),
                }
            )
        self._cache.set(key, result)
        return result
