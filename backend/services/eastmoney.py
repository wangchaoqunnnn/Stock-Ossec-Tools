# -*- coding: utf-8 -*-
"""行情数据源封装（Python 3.8 兼容）。

主数据源：东方财富公开行情接口（字段丰富）；
备用数据源：腾讯行情（qt.gtimg.cn，结构简单稳定）。

设计要点：
- 主备数据源**并发请求**：哪个先成功返回用哪个（主源成功优先），
  避免主源挂起时用户长时间等待；
- 请求带短缓存（TTL 10s），控制上游频率；
- 所有对外方法返回 ``(data, source)`` 或纯 ``data``（见各方法注释），
  source 为 "eastmoney" / "tencent"，用于标识实际数据来源。
"""

import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from .cache import TTLCache

try:  # python -m backend.services.eastmoney（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config


class DataSourceError(Exception):
    """上游数据源异常。"""


# 共享线程池：并发请求主备数据源。常驻线程在进程退出时自然回收。
_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _num(value: Any) -> Optional[float]:
    """将可能为 '-'/None 的值安全转为数字。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get(url: str, params: Optional[dict] = None, retries: int = 1) -> dict:
    """带超时与重试的 GET 请求，返回 JSON（东财接口）。

    默认重试 1 次（共 2 次尝试）：调用方通常有腾讯回退，无需多次重试拖慢响应。
    """
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
    """行情数据服务（东财主源 + 腾讯回退，并发取最快可用源，带短缓存）。"""

    def __init__(self) -> None:
        self._cache = TTLCache(ttl=config.CACHE_TTL)

    # ------------------------------------------------------------------
    # 并发编排
    # ------------------------------------------------------------------
    @staticmethod
    def _first_available(primary: Callable, fallback: Callable) -> Tuple[Any, str]:
        """并发执行主备源，返回 ``(data, source)``。

        - 优先返回主源的成功结果（非空）；
        - 主源未完成或失败时，返回备源的成功结果；
        - 两源均正常响应但无数据 -> ``(None, "tencent")``（调用方按"未找到"处理）；
        - 两源均异常 -> 抛出最后一个 DataSourceError（调用方按"服务不可用"处理）。
        """
        futures = {
            "eastmoney": _EXECUTOR.submit(primary),
            "tencent": _EXECUTOR.submit(fallback),
        }
        done, pending = wait(list(futures.values()), return_when=FIRST_COMPLETED)
        order = [name for name, f in futures.items() if f in done]
        order += [name for name, f in futures.items() if f not in done]

        any_success = False
        last_error = None
        for name in order:
            try:
                data = futures[name].result()
            except DataSourceError as exc:
                last_error = exc
                continue
            any_success = True
            if data:
                return data, name
        if any_success:
            return None, "tencent"
        raise last_error

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _code_to_secid(code: str) -> Optional[str]:
        """A 股代码启发式转换为东财 secid（1=沪 0=深/北）。"""
        code = str(code).strip()
        if not code:
            return None
        if code.startswith(("6", "9")):
            return "1.%s" % code
        return "0.%s" % code

    @staticmethod
    def _code_to_emcode(code: str) -> Optional[str]:
        """A 股代码 -> 东财 SECUCODE（如 600519.SH / 000938.SZ / 8xxxxx.BJ）。"""
        code = str(code).strip()
        if not code:
            return None
        if code.startswith(("6", "9")):
            return "%s.SH" % code
        if code.startswith(("4", "8")):
            return "%s.BJ" % code
        return "%s.SZ" % code

    @staticmethod
    def _code_to_tencent(code: str) -> Optional[str]:
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
    def _friendly_time(ts: Any) -> Optional[str]:
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
    def _tencent_fetch(self, codes: List[str]) -> Dict[str, List[str]]:
        """批量获取腾讯行情，返回 {原始代码: 字段列表}。"""
        if not codes:
            return {}
        try:
            resp = requests.get(
                config.TENCENT_QUOTE_API + ",".join(codes),
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
    def _clean_name(name: str) -> str:
        """腾讯部分名称带空格（如 '五 粮 液'），去除之。"""
        return (name or "").replace(" ", "").strip()

    @staticmethod
    def _tencent_row(fields: List[str]) -> Dict[str, Any]:
        """腾讯 A 股字段列表 -> 规范化行情 dict。"""
        def pick(idx: int) -> Optional[float]:
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
    def _tencent_index_row(fields: List[str]) -> Dict[str, Any]:
        """腾讯指数（港股/美股等紧凑布局）字段列表 -> 规范化 dict。"""
        def pick(idx: int) -> Optional[float]:
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
    # 股票检索（无腾讯回退，codetable -> suggest 双通道）
    # ------------------------------------------------------------------
    _A_SHARE_TYPES = {"沪A", "深A", "京A", "科创板", "创业板"}

    def search(self, keyword: str, count: int = 8) -> List[dict]:
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

    def _search_codetable(self, keyword: str, count: int) -> List[dict]:
        """优先使用的检索接口（返回结构稳定，含拼音字段）。"""
        try:
            payload = _get(
                config.EASTMONEY_CODETABLE_API,
                {"client": "web", "keyword": keyword, "pageIndex": 1, "pageSize": count},
            )
        except DataSourceError:
            return []

        rows = (payload or {}).get("result") or []
        kw = keyword.strip().lower()
        results = []
        for row in rows:
            type_name = str(row.get("securityTypeName") or "")
            code = str(row.get("code") or "")
            name = str(row.get("shortName") or "")
            pinyin = str(row.get("pinyin") or "")
            if type_name not in self._A_SHARE_TYPES or not code or not name:
                continue
            # 支持代码 / 名称 / 中文拼音首字母检索
            if kw.isascii():
                if not (kw in code.lower() or pinyin.lower().startswith(kw)):
                    continue
            else:
                if not (kw in name.lower() or kw in code.lower()):
                    continue
            market = row.get("market")
            market = str(market) if market is not None else ""
            results.append(
                {
                    "code": code,
                    "name": name,
                    "pinyin": pinyin,
                    "market_type": market,
                    "security_type": type_name,
                    "quote_id": "%s.%s" % (market, code),
                }
            )
        return results

    def _search_suggest(self, keyword: str, count: int) -> List[dict]:
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
    def get_quote(self, code: str) -> Tuple[Optional[dict], Optional[str]]:
        """获取单只股票行情详情（主备源并发，优先主源）。

        返回 ``(quote, source)``；双数据源均无结果时返回 ``(None, "tencent")``。
        """
        code = str(code or "").strip()
        if not code:
            return None, None
        key = "quote:%s" % code
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        data, source = self._first_available(
            lambda: self._quote_from_eastmoney(code),
            lambda: self._quote_from_tencent(code),
        )
        if data is not None:
            self._cache.set(key, (data, source))
        return data, source

    def _quote_from_eastmoney(self, code: str) -> dict:
        secid = self._code_to_secid(code)
        payload = _get(
            config.EASTMONEY_QUOTE_API,
            {"secid": secid, "fields": config.QUOTE_FIELDS, "fltt": "2", "invt": "2"},
        )
        d = (payload or {}).get("data")
        if not d:
            return None
        return {
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

    def _quote_from_tencent(self, code: str) -> dict:
        tcode = self._code_to_tencent(code)
        rows = self._tencent_fetch([tcode])
        fields = rows.get(tcode)
        if not fields:
            return None
        base = self._tencent_row(fields)
        return {
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

    # ------------------------------------------------------------------
    # 主要指数
    # ------------------------------------------------------------------
    def get_indices(self, market: str = "cn") -> Tuple[List[dict], str]:
        """获取主要指数行情。market: cn / asia / us / futures。

        返回 ``(list, source)``。
        """
        market = market if market in config.INDICES else "cn"
        key = "indices:%s" % market
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        data, source = self._first_available(
            lambda: self._indices_eastmoney(market),
            lambda: self._indices_tencent(market),
        )
        data = data if data is not None else []
        self._cache.set(key, (data, source))
        return data, source

    def _indices_eastmoney(self, market: str) -> List[dict]:
        indices = config.INDICES[market]
        secids = ",".join(item["secid"] for item in indices)
        payload = _get(
            config.EASTMONEY_ULIST_API,
            {"secids": secids, "fields": config.ULIST_FIELDS, "fltt": "2", "invt": "2"},
        )

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

    def _indices_tencent(self, market: str) -> List[dict]:
        """腾讯回退：仅取腾讯支持的指数（tencent 代码非空的条目）。

        腾讯不支持的指数（如日经225、期货）保留条目但字段为 None，
        避免与其它市场的代码错位。
        """
        indices = config.INDICES[market]
        tencent_codes = [item.get("tencent") for item in indices]
        fetchable = [c for c in tencent_codes if c]
        try:
            rows = self._tencent_fetch(fetchable)
        except DataSourceError:
            rows = {}

        result = []
        for item, tcode in zip(indices, tencent_codes):
            fields = rows.get(tcode) if tcode else None
            if not fields:
                result.append(
                    {
                        "name": item["name"],
                        "secid": item["secid"],
                        "now": None,
                        "change": None,
                        "change_pct": None,
                    }
                )
                continue
            base = self._tencent_index_row(fields)
            result.append(
                {
                    "name": item["name"],
                    "secid": item["secid"],
                    "now": base["now"],
                    "change": base["change"],
                    "change_pct": base["change_pct"],
                }
            )
        return result

    # ------------------------------------------------------------------
    # 批量行情
    # ------------------------------------------------------------------
    def get_batch_quotes(self, codes: List[str]) -> List[dict]:
        """批量获取 A 股行情（主备源并发，优先主源）。

        返回 ``list``，每个元素为规范化行情 dict。
        """
        codes = [str(c).strip() for c in codes if c]
        if not codes:
            return []
        key = "batch:%s" % ",".join(sorted(codes))
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        data, _source = self._first_available(
            lambda: self._batch_eastmoney(codes),
            lambda: self._batch_tencent(codes),
        )
        data = data if data is not None else []
        self._cache.set(key, data)
        return data

    # ------------------------------------------------------------------
    # 所属行业解析（个股 -> 二级行业名，与资金流板块名单同口径）
    # ------------------------------------------------------------------
    def resolve_industry(self, code: str) -> str:
        """解析个股所属行业（二级行业名，如「白酒Ⅱ」「保险Ⅱ」「电池」）。

        仅在批量行情未携带行业字段（主 push2 不可达、回退腾讯）时启用：
          1. 东财备用行情主机 push2delay 的 ulist f100（同口径，数据延迟数分钟）；
          2. 东财 F10 datacenter 所属板块报告：取 BOARD_TYPE=行业 的二级（L2）行业名。

        全部失败返回空串，由调用方降级处理（给中性分）。
        """
        code = str(code or "").strip()
        if not code:
            return ""
        key = "ind:%s" % code
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        industry = self._industry_from_delay_ulist(code) or self._industry_from_f10(code)
        self._cache.set(key, industry or "")
        return industry or ""

    def _industry_from_delay_ulist(self, code: str) -> str:
        secid = self._code_to_secid(code)
        if not secid:
            return ""
        try:
            payload = _get(
                config.EASTMONEY_ULIST_API_DELAY,
                {"secids": secid, "fields": "f12,f100", "fltt": "2", "invt": "2"},
            )
        except DataSourceError:
            return ""
        diff = ((payload or {}).get("data") or {}).get("diff") or []
        if not isinstance(diff, list):
            diff = [diff]
        for row in diff:
            if str(row.get("f12") or "") == code:
                return str(row.get("f100") or "").strip()
        return ""

    def _industry_from_f10(self, code: str) -> str:
        secucode = self._code_to_emcode(code)
        if not secucode:
            return ""
        try:
            payload = _get(
                config.EASTMONEY_F10_BOARDTYPE_API,
                {
                    "reportName": "RPT_F10_CORETHEME_BOARDTYPE",
                    "columns": "SECUCODE,BOARD_CODE,BOARD_NAME,BOARD_TYPE,BOARD_LEVEL,BOARD_RANK",
                    "filter": '(SECUCODE="%s")' % secucode,
                    "pageSize": 100,
                    "pageNumber": 1,
                    "source": "HSF10",
                    "client": "PC",
                },
            )
        except DataSourceError:
            return ""
        rows = (((payload or {}).get("result") or {}).get("data")) or []
        industry_rows = [r for r in rows if (r.get("BOARD_TYPE") or "") == "行业"]
        for level in (2, 1, 3):
            for r in industry_rows:
                if r.get("BOARD_LEVEL") == level:
                    name = str(r.get("BOARD_NAME") or "").strip()
                    if name:
                        return name
        return ""

    def _batch_eastmoney(self, codes: List[str]) -> List[dict]:
        secids = ",".join(self._code_to_secid(c) for c in codes)
        payload = _get(
            config.EASTMONEY_ULIST_API,
            {"secids": secids, "fields": config.ULIST_FIELDS, "fltt": "2", "invt": "2"},
        )

        diff = ((payload or {}).get("data") or {}).get("diff") or []
        if not isinstance(diff, list):
            diff = [diff]

        by_code = {}
        for row in diff:
            code = str(row.get("f12") or "")
            if code:
                by_code[code] = row

        result = []
        for code in codes:
            row = by_code.get(code, {})
            result.append(
                {
                    "code": code,
                    "name": str(row.get("f14") or ""),
                    "now_price": _num(row.get("f2")),
                    "change_pct": _num(row.get("f3")),
                    "change": _num(row.get("f4")),
                    "volume": _num(row.get("f5")),
                    "amount": _num(row.get("f6")),
                    "turnover": _num(row.get("f8")),
                    "pe": _num(row.get("f9")),
                    "volume_ratio": _num(row.get("f10")),
                    "high": _num(row.get("f15")),
                    "low": _num(row.get("f16")),
                    "open": _num(row.get("f17")),
                    "prev_close": _num(row.get("f18")),
                    "total_mv": _num(row.get("f20")),
                    "float_mv": _num(row.get("f21")),
                    "speed": _num(row.get("f22")),
                    "pb": _num(row.get("f23")),
                    "industry": str(row.get("f100") or ""),
                }
            )
        return result

    def _batch_tencent(self, codes: List[str]) -> List[dict]:
        tcodes = [self._code_to_tencent(c) for c in codes]
        rows = self._tencent_fetch(tcodes)

        result = []
        for code, tcode in zip(codes, tcodes):
            fields = rows.get(tcode)
            if not fields:
                result.append({"code": code, "name": "", "now_price": None})
                continue
            base = self._tencent_row(fields)
            result.append(
                {
                    "code": code,
                    "name": self._clean_name(fields[1]) if len(fields) > 1 else "",
                    "now_price": base["now_price"],
                    "change_pct": base["change_pct"],
                    "change": base["change"],
                    "volume": base["volume"],
                    "amount": base["amount"],
                    "turnover": base["turnover"],
                    "pe": base["pe"],
                    "volume_ratio": base["volume_ratio"],
                    "high": base["high"],
                    "low": base["low"],
                    "open": base["open"],
                    "prev_close": base["prev_close"],
                    "total_mv": base["total_mv"],
                    "float_mv": base["float_mv"],
                    "speed": None,
                    "pb": base["pb"],
                    "industry": "",
                }
            )
        return result
