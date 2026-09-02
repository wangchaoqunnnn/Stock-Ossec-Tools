# -*- coding: utf-8 -*-
"""个股真实行情数据：K 线、分时、技术指标（腾讯公开接口，稳定可靠）。

腾讯接口字段说明：
- fqkline/get 返回 qfqday / qfqweek / qfqmonth，每行为
  [date, open, close, high, low, volume, ...]
- minute/query 返回 "HHMM price volume amount" 的分时明细
"""

import statistics
from typing import Any, Dict, List, Optional

import requests

from .cache import TTLCache

try:  # python -m backend.services.kline（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config


class DataSourceError(Exception):
    """数据源异常。"""


def _num(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class KlineService(object):
    """个股 K 线 / 分时 / 技术指标服务（带短缓存）。"""

    _KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    _MINUTE_API = "https://web.ifzq.gtimg.cn/appstock/app/minute/query"

    def __init__(self) -> None:
        self._cache = TTLCache(ttl=config.CACHE_TTL)

    @staticmethod
    def _tencent_code(code: str) -> str:
        code = str(code).strip()
        if code.startswith(("6", "9")):
            return "sh%s" % code
        if code.startswith(("4", "8")):
            return "bj%s" % code
        return "sz%s" % code

    def _http_get(self, url: str, params: Dict[str, str]) -> dict:
        try:
            resp = requests.get(url, params=params, timeout=config.UPSTREAM_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            raise DataSourceError("行情接口请求失败: %s" % exc)

    # ------------------------------------------------------------------
    # K 线
    # ------------------------------------------------------------------
    def get_kline(self, code: str, period: str = "day", count: int = 120) -> List[dict]:
        """获取前复权 K 线。period: day / week / month。"""
        period = period if period in ("day", "week", "month") else "day"
        count = max(10, min(500, int(count or 120)))
        key = "kline:%s:%s:%d" % (code, period, count)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        tcode = self._tencent_code(code)
        payload = self._http_get(self._KLINE_API, {"param": "%s,%s,,,%d,qfq" % (tcode, period, count)})
        data = ((payload or {}).get("data") or {}).get(tcode) or {}
        rows = data.get("qfq%s" % period) or data.get(period) or []

        result = []
        for row in rows:
            if len(row) < 6:
                continue
            result.append(
                {
                    "date": str(row[0]),
                    "open": _num(row[1]),
                    "close": _num(row[2]),
                    "high": _num(row[3]),
                    "low": _num(row[4]),
                    "volume": _num(row[5]),
                }
            )
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 分时
    # ------------------------------------------------------------------
    def get_minute(self, code: str) -> List[dict]:
        """获取当日分时明细。"""
        key = "minute:%s" % code
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        tcode = self._tencent_code(code)
        payload = self._http_get(self._MINUTE_API, {"code": tcode})
        try:
            rows = ((payload or {}).get("data") or {}).get(tcode, {}).get("data", {}).get("data") or []
        except AttributeError:
            rows = []

        result = []
        for row in rows:
            parts = str(row).split()
            if len(parts) < 2:
                continue
            result.append(
                {
                    "time": parts[0],
                    "price": _num(parts[1]),
                    "volume": _num(parts[2]) if len(parts) > 2 else None,
                }
            )
        self._cache.set(key, result)
        return result

    # ------------------------------------------------------------------
    # 技术指标
    # ------------------------------------------------------------------
    @staticmethod
    def _ema(values: List[float], n: int) -> List[float]:
        if not values:
            return []
        k = 2.0 / (n + 1)
        ema = [values[0]]
        for v in values[1:]:
            ema.append(v * k + ema[-1] * (1 - k))
        return ema

    @staticmethod
    def _ma(values: List[float], n: int) -> List[Optional[float]]:
        out: List[Optional[float]] = [None] * len(values)
        for i in range(len(values)):
            if i >= n - 1:
                out[i] = sum(values[i - n + 1:i + 1]) / n
        return out

    def get_indicators(self, code: str, period: str = "day", count: int = 120) -> Optional[dict]:
        """基于真实 K 线计算常用技术指标，返回 K 线与最新指标。"""
        kline = self.get_kline(code, period, count)
        if len(kline) < 30:
            return None
        closes = [r["close"] for r in kline if r["close"] is not None]
        highs = [r["high"] for r in kline if r["high"] is not None]
        lows = [r["low"] for r in kline if r["low"] is not None]
        n = len(closes)

        # 均线
        def latest(series, default=None):
            for v in reversed(series):
                if v is not None:
                    return v
            return default

        ma5 = latest(self._ma(closes, 5))
        ma10 = latest(self._ma(closes, 10))
        ma20 = latest(self._ma(closes, 20))
        ma60 = latest(self._ma(closes, 60))

        # MACD (12, 26, 9)
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        dif = [a - b for a, b in zip(ema12, ema26)]
        dea = self._ema(dif, 9)
        macd_hist = 2 * (dif[-1] - dea[-1])
        macd_signal = "金叉" if dif[-1] >= dea[-1] else "死叉"

        # KDJ (9, 3, 3)
        k_val = d_val = 50.0
        j_val = 50.0
        if n >= 9:
            rsv_series = []
            for i in range(n):
                low_n = min(lows[max(0, i - 8):i + 1])
                high_n = max(highs[max(0, i - 8):i + 1])
                rsv_series.append(50.0 if high_n == low_n else (closes[i] - low_n) / (high_n - low_n) * 100)
            kk = 50.0
            dd = 50.0
            for rsv in rsv_series:
                kk = 2 / 3 * kk + 1 / 3 * rsv
                dd = 2 / 3 * dd + 1 / 3 * kk
            k_val, d_val = kk, dd
            j_val = 3 * kk - 2 * dd
        kdj_signal = "偏强" if k_val >= d_val else "偏弱"

        # RSI (14)
        rsi = 50.0
        if n > 14:
            gains = []
            losses = []
            for i in range(1, n):
                diff = closes[i] - closes[i - 1]
                gains.append(max(diff, 0.0))
                losses.append(max(-diff, 0.0))
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 50.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
        if rsi >= 70:
            rsi_signal = "超买"
        elif rsi <= 30:
            rsi_signal = "超卖"
        else:
            rsi_signal = "中性"

        # BOLL (20, 2)
        boll_mid = ma20
        if n >= 20:
            window = closes[-20:]
            boll_mid = statistics.mean(window)
            std = statistics.pstdev(window)
            boll_upper = boll_mid + 2 * std
            boll_lower = boll_mid - 2 * std
        else:
            boll_upper = boll_lower = None
        last_close = closes[-1]
        if boll_upper is not None:
            if last_close >= boll_upper:
                boll_signal = "突破上轨"
            elif last_close <= boll_lower:
                boll_signal = "跌破下轨"
            elif last_close >= boll_mid:
                boll_signal = "中轨上方"
            else:
                boll_signal = "中轨下方"
        else:
            boll_signal = "--"

        return {
            "kline": kline,
            "indicators": {
                "macd": {"value": round(macd_hist, 3), "signal": macd_signal},
                "kdj": {"k": round(k_val, 2), "d": round(d_val, 2), "j": round(j_val, 2), "signal": kdj_signal},
                "rsi": {"value": round(rsi, 2), "signal": rsi_signal},
                "boll": {"mid": boll_mid, "upper": boll_upper, "lower": boll_lower, "signal": boll_signal},
                "ma": {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60},
            },
        }
