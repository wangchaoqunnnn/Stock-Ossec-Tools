# -*- coding: utf-8 -*-
"""行情数据源封装（Python 3.8 兼容）。

主数据源：东方财富公开行情接口（字段丰富：行业、涨速等）；
备用数据源：腾讯行情（qt.gtimg.cn，结构简单稳定）。
东财请求失败或异常时自动回退到腾讯，保证页面可用。
"""

import time

import requests

from .cache import TTLCache

try:  # python -m backend.services.eastmoney（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config


class DataSourceError(Exception):
    """上游数据源异常。"""


def _num(value):
    """将可能为 '-'/None 的值安全转为数字。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get(url, params=None, retries=2):
    """带超时与重试的 GET 请求，返回 JSON（东财接口）。"""
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=config.UPSTREAM_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise DataSourceError("上游行情接口请求失败: %s" % last_error)


class EastMoneyService(object):
    """行情数据服务（东财主源 + 腾讯回退，带短缓存）。"""

    def __init__(self):
        self._cache = TTLCache(ttl=config.CACHE_TTL)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _code_to_secid(code):
        """A 股代码启发式转换为东财 secid（1=沪 0=深/北）。"""
        code = str(code).strip()
        if not code:
            return None
        if code.startswith(("6", "9")):
            return "1.%s" % code
        return "0.%s" % code

    @staticmethod
    def _code_to_tencent(code):
        """A 股代码转换为腾讯行情代码（sh/sz/bj 前缀）。"""
        code = str(code).strip()
        if not code:
            return None
        if code.startswith(("6", "9")):
            return "sh%s" % code
        if code.startswith(("4", "8")):
            return "bj%s" % code
        return "sz%s" % code

    @staticmethod
    def _friendly_time(ts):
        """时间戳（秒或毫秒）转为 'YYYY-MM-DD HH:MM:SS'。"""
        try:
            ts = float(ts)
            if ts > 1e12:
                ts = ts / 1000.0
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        except (TypeError, ValueError, OSError):
            return None

    # ------------------------------------------------------------------
    # 腾讯行情（备用源）
    # ------------------------------------------------------------------
    _TENCENT_INDEX_CODES = {
        "cn": ["sh000001", "sz399001", "sh000300", "sz399006", "sh000688", "bj899050"],
        "hk": ["hkHSI", "hkHSTECH", "hkHSCEI"],
        "us": ["usDJI", "usIXIC", "usINX"],
    }

    def _tencent_fetch(self, codes):
        """批量获取腾讯行情，返回 {原始代码: 字段列表}。"""
        if not codes:
            return {}
        try:
            resp = requests.get(
                "https://qt.gtimg.cn/q=%s" % ",".join(codes),
                timeout=config.UPSTREAM_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise DataSourceError("腾讯行情接口请求失败: %s" % exc)

        result = {}
        for line in resp.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                var_part, payload = line.split("=", 1)
                fields = payload.strip().strip('";').split("~")
                tcode = var_part.split("_", 1)[1]
            except (ValueError, IndexError):
                continue
            result[tcode] = fields
        return result

    @staticmethod
    def _clean_name(name):
        """腾讯部分名称带空格（如 '五 粮 液'），去除之。"""
        return (name or "").replace(" ", "").strip()

    @staticmethod
    def _tencent_row(fields):
        """腾讯 A 股字段列表 -> 规范化行情 dict。"""
        def pick(idx):
            if idx < len(fields):
                return _num(fields[idx])
            return None

        return {
            "now_price": pick(3),
            "prev_close": pick(4),
            "open": pick(5),
            "volume": pick(6),
            "change": pick(31),
            "change_pct": pick(32),
            "high": pick(33),
            "low": pick(34),
            "amount": None if pick(37) is None else pick(37) * 10000.0,
            "turnover": pick(38),
            "pe": pick(52),
            "amplitude": pick(43),
            "float_mv": None if pick(44) is None else pick(44) * 1e8,
            "total_mv": None if pick(45) is None else pick(45) * 1e8,
            "pb": pick(46),
            "volume_ratio": pick(49),
        }

    @staticmethod
    def _tencent_index_row(fields):
        """腾讯指数（港股/美股等紧凑布局）字段列表 -> 规范化 dict。"""
        def pick(idx):
            if idx < len(fields):
                return _num(fields[idx])
            return None

        return {
            "now": pick(3),
            "prev_close": pick(4),
            "open": pick(5),
            "volume": pick(6),
            "change": pick(31),
            "change_pct": pick(32),
            "high": pick(33),
            "low": pick(34),
        }

    # ------------------------------------------------------------------
    # 股票检索
    # ------------------------------------------------------------------
    _A_SHARE_TYPES = {"沪A", "深A", "京A"}

    def search(self, keyword, count=8):
        """按代码/名称关键词检索 A 股。"""
        keyword = (keyword or "").strip()
        if not keyword:
            return []
        key = "search:%s:%d" % (keyword, count)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        results = self._search_codetable(keyword, count)
        if not results:
            results = self._search_suggest(keyword, count)

        self._cache.set(key, results)
        return results

    def _search_codetable(self, keyword, count):
        """优先使用的检索接口（返回结构稳定）。"""
        try:
            payload = _get(
                "https://search-codetable.eastmoney.com/codetable/search/web",
                {"client": "web", "keyword": keyword, "pageIndex": 1, "pageSize": count},
            )
        except DataSourceError:
            return []

        rows = (payload or {}).get("result") or []
        results = []
        for row in rows:
            type_name = str(row.get("securityTypeName") or "")
            code = str(row.get("code") or "")
            name = str(row.get("shortName") or "")
            if type_name not in self._A_SHARE_TYPES or not code or not name:
                continue
            market = row.get("market")
            market = str(market) if market is not None else ""
            results.append(
                {
                    "code": code,
                    "name": name,
                    "market_type": market,
                    "security_type": type_name,
                    "quote_id": "%s.%s" % (market, code),
                }
            )
        return results

    def _search_suggest(self, keyword, count):
        """兜底检索接口（响应结构不稳定，做双重兼容）。"""
        try:
            payload = _get(
                config.EASTMONEY_SEARCH_API,
                {
                    "input": keyword,
                    "type": "14",
                    "token": config.EASTMONEY_SEARCH_TOKEN,
                    "count": count,
                },
            )
        except DataSourceError:
            return []

        rows = None
        table = (payload or {}).get("QuotationCodeTable")
        if table:
            rows = table.get("Data")
        if rows is None:
            result = (payload or {}).get("result") or {}
            rows = result.get("QuotationCodeTable", {}).get("Data") if isinstance(result, dict) else None
        if not rows:
            return []

        results = []
        for row in rows:
            code = str(row.get("Code") or "")
            name = str(row.get("Name") or "")
            type_name = str(row.get("SecurityTypeName") or "")
            if type_name not in self._A_SHARE_TYPES or not code or not name:
                continue
            results.append(
                {
                    "code": code,
                    "name": name,
                    "market_type": str(row.get("MarketType") or ""),
                    "security_type": type_name,
                    "quote_id": str(row.get("QuoteID") or ""),
                }
            )
        return results

    # ------------------------------------------------------------------
    # 个股行情详情
    # ------------------------------------------------------------------
    def get_quote(self, code):
        """获取单只股票行情详情（东财失败时回退腾讯）。

        返回 ``(quote, source)``，source 为 "eastmoney"/"tencent"。
        """
        code = str(code or "").strip()
        if not code:
            return None, None
        key = "quote:%s" % code
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        quote = None
        source = "eastmoney"
        error = None
        secid = self._code_to_secid(code)
        try:
            payload = _get(
                config.EASTMONEY_QUOTE_API,
                {
                    "secid": secid,
                    "fields": config.QUOTE_FIELDS,
                    "fltt": "2",
                    "invt": "2",
                },
            )
            d = (payload or {}).get("data")
            if d:
                quote = {
                    "code": str(d.get("f57") or code),
                    "name": str(d.get("f58") or ""),
                    "now_price": _num(d.get("f43")),
                    "change": _num(d.get("f169")),
                    "change_pct": _num(d.get("f170")),
                    "open": _num(d.get("f46")),
                    "high": _num(d.get("f44")),
                    "low": _num(d.get("f45")),
                    "prev_close": _num(d.get("f60")),
                    "volume": _num(d.get("f47")),
                    "amount": _num(d.get("f48")),
                    "turnover": _num(d.get("f168")),
                    "volume_ratio": _num(d.get("f50")),
                    "pe": _num(d.get("f162")),
                    "pb": _num(d.get("f167")),
                    "total_mv": _num(d.get("f116")),
                    "float_mv": _num(d.get("f117")),
                    "amplitude": _num(d.get("f171")),
                    "time": self._friendly_time(d.get("f86")),
                }
        except DataSourceError as exc:
            error = exc

        if quote is None:
            # 回退腾讯
            source = "tencent"
            tcode = self._code_to_tencent(code)
            rows = self._tencent_fetch([tcode])
            fields = rows.get(tcode)
            if fields:
                base = self._tencent_row(fields)
                quote = {
                    "code": code,
                    "name": self._clean_name(fields[1]) if len(fields) > 1 else "",
                    "now_price": base["now_price"],
                    "change": base["change"],
                    "change_pct": base["change_pct"],
                    "open": base["open"],
                    "high": base["high"],
                    "low": base["low"],
                    "prev_close": base["prev_close"],
                    "volume": base["volume"],
                    "amount": base["amount"],
                    "turnover": base["turnover"],
                    "volume_ratio": base["volume_ratio"],
                    "pe": base["pe"],
                    "pb": base["pb"],
                    "total_mv": base["total_mv"],
                    "float_mv": base["float_mv"],
                    "amplitude": base["amplitude"],
                    "time": None,
                }
            elif error is not None:
                raise error

        if quote is not None:
            self._cache.set(key, (quote, source))
        return quote, source

    # ------------------------------------------------------------------
    # 主要指数
    # ------------------------------------------------------------------
    def get_indices(self, market="cn"):
        """获取主要指数行情。market: cn / hk / us。

        返回 ``(list, source)``。
        """
        market = market if market in config.INDICES else "cn"
        key = "indices:%s" % market
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        result = self._indices_eastmoney(market)
        source = "eastmoney"
        if not result:
            result = self._indices_tencent(market)
            source = "tencent"

        self._cache.set(key, (result, source))
        return result, source

    def _indices_eastmoney(self, market):
        indices = config.INDICES[market]
        secids = ",".join(item["secid"] for item in indices)
        try:
            payload = _get(
                config.EASTMONEY_ULIST_API,
                {"secids": secids, "fields": config.ULIST_FIELDS, "fltt": "2", "invt": "2"},
            )
        except DataSourceError:
            return []

        diff = ((payload or {}).get("data") or {}).get("diff") or []
        if not isinstance(diff, list):
            diff = [diff]

        by_code = {}
        for row in diff:
            code = str(row.get("f12") or "")
            if code:
                by_code[code] = row

        result = []
        for item in indices:
            row = by_code.get(str(item["secid"]).split(".")[1], {})
            result.append(
                {
                    "name": item["name"],
                    "secid": item["secid"],
                    "now": _num(row.get("f2")),
                    "change": _num(row.get("f4")),
                    "change_pct": _num(row.get("f3")),
                }
            )
        return result

    def _indices_tencent(self, market):
        tcodes = self._TENCENT_INDEX_CODES.get(market, self._TENCENT_INDEX_CODES["cn"])
        try:
            rows = self._tencent_fetch(tcodes)
        except DataSourceError:
            return []

        result = []
        for index_item, tcode in zip(config.INDICES[market], tcodes):
            fields = rows.get(tcode)
            if not fields:
                continue
            base = self._tencent_index_row(fields)
            result.append(
                {
                    "name": index_item["name"],
                    "secid": index_item["secid"],
                    "now": base["now"],
                    "change": base["change"],
                    "change_pct": base["change_pct"],
                }
            )
        return result
