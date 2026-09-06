# -*- coding: utf-8 -*-
"""分时量价形态与「能否以当前市价立即买入」判断（Python 3.8 兼容）。

输入：最新行情（腾讯实时）+ 当日/最近交易日分时明细（腾讯 minute/query）+ 日线均线。
识别常见分时形态并给出市价买入结论与建议价位：

- 冲高回落 / 放量诱多：盘中放量急拉至日内高位后明显回落，现价跌破或贴近分时均价；
- 无量拉升：价格近期抬升但量能持续萎缩（承接不足，易冲高回落）；
- 量价齐升：价升量增、量能配合健康；
- 放量上攻 / 缩量回调 / 放量下杀 等辅助形态。

结论分三档：
- market：可尝试市价单（轻仓、分批）；
- limit：不建议市价追高，建议挂限价单等回踩位企稳；
- wait：建议观望，等待给出企稳/转强信号价。

仅供学习参考，不构成投资建议。
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from .eastmoney import EastMoneyService
from .kline import KlineService


def _mean(values: List[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _to_hhmm_min(hhmm: str) -> Optional[int]:
    """'0930' -> 570（当日分钟数），异常返回 None。"""
    try:
        t = str(hhmm).strip()
        if len(t) != 4:
            return None
        return int(t[0:2]) * 60 + int(t[2:4])
    except (TypeError, ValueError):
        return None


class IntradayJudge(object):
    """分时形态识别 + 市价买入可行性判断。"""

    def __init__(self) -> None:
        self._em = EastMoneyService()
        self._kline = KlineService()

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def judge(self, code: str) -> Optional[dict]:
        """对个股分时进行量价形态分析，返回能否市价买入的结论。"""
        code = str(code or "").strip()
        if not code:
            return None

        quote, _src = self._em.get_quote(code)
        if not quote or quote.get("now_price") is None:
            return None
        session = self._kline.get_minute_session(code)
        rows = session.get("rows") or []
        data_date = str(session.get("date") or "")

        name = quote.get("name") or code
        cur = float(quote.get("now_price"))
        prev_close = quote.get("prev_close")
        if not prev_close or prev_close <= 0:
            pct = quote.get("change_pct")
            prev_close = cur / (1 + (pct or 0.0) / 100.0) if pct is not None else cur

        stats = self._build_stats(rows, code)
        if stats is None:
            return {
                "code": code,
                "name": name,
                "trade_note": self._trade_note(data_date, rows),
                "data_date": data_date,
                "patterns": [],
                "verdict": {
                    "action": "wait",
                    "tone": "deny",
                    "title": "分时样本不足，暂不判断能否市价买入",
                },
                "reasons": ["分时明细数据过少，无法可靠判断量价形态，建议参考上方的等待买点价位"],
                "suggestion": None,
                "levels": None,
                "quote": {"price": cur, "change_pct": quote.get("change_pct")},
            }

        # 形态识别
        patterns = self._detect_patterns(stats, cur, prev_close)
        verdict, suggestion, reasons = self._decide(stats, cur, prev_close, patterns, quote)

        levels = {
            "price": round(cur, 2),
            "vwap": round(stats["vwap"], 2) if stats.get("vwap") else None,
            "day_high": round(stats["day_high"], 2) if stats.get("day_high") else None,
            "day_low": round(stats["day_low"], 2) if stats.get("day_low") else None,
            "recent_low": round(stats["recent_low"], 2) if stats.get("recent_low") else None,
            "ma20": round(stats["ma20"], 2) if stats.get("ma20") else None,
            "pct_from_vwap": round((cur / stats["vwap"] - 1) * 100, 2) if stats.get("vwap") else None,
            "change_pct": round((cur / prev_close - 1) * 100, 2),
        }

        return {
            "code": code,
            "name": name,
            "trade_note": self._trade_note(data_date, rows),
            "data_date": data_date,
            "patterns": patterns,
            "verdict": verdict,
            "reasons": reasons,
            "suggestion": suggestion,
            "levels": levels,
            "quote": {"price": cur, "change_pct": quote.get("change_pct")},
        }

    # ------------------------------------------------------------------
    # 数据整理
    # ------------------------------------------------------------------
    def _build_stats(self, rows: List[dict], code: str) -> Optional[dict]:
        """由分时行计算量价统计特征；数据不足返回 None。"""
        prices: List[float] = []
        cum_v: List[float] = []
        cum_a: List[float] = []
        times: List[int] = []
        for r in rows:
            p = r.get("price")
            if p is None:
                continue
            prices.append(float(p))
            v = r.get("volume")
            a = r.get("amount")
            cum_v.append(float(v) if v is not None else (cum_v[-1] if cum_v else 0.0))
            cum_a.append(float(a) if a is not None else (cum_a[-1] if cum_a else 0.0))
            tm = _to_hhmm_min(r.get("time"))
            times.append(tm if tm is not None else (times[-1] + 1 if times else 0))

        n = len(prices)
        if n < 15:
            return None

        # 每分钟成交量增量（跨午休等长间隔不计算）
        dvs: List[float] = [0.0] * n
        for i in range(1, n):
            gap = times[i] - times[i - 1]
            if 0 < gap <= 3:
                dvs[i] = max(0.0, cum_v[i] - cum_v[i - 1])

        # 分时均价线（累计额 / 累计量）
        vwap = None
        if cum_v[-1] > 0 and cum_a[-1] > 0:
            vwap = cum_a[-1] / (cum_v[-1] * 100.0)
        if vwap is None or vwap <= 0:
            vwap = _mean(prices[-30:])

        day_high = max(prices)
        day_low = min(prices)
        hi_idx = prices.index(day_high)
        lo_idx = prices.index(day_low)

        # 日线 MA20（可空）
        ma20 = None
        try:
            ind = self._kline.get_indicators(code, "day", 120)
            if ind:
                ma20 = (ind.get("indicators") or {}).get("ma", {}).get("ma20")
        except Exception:
            ma20 = None
        return {
            "prices": prices,
            "dvs": dvs,
            "times": times,
            "n": n,
            "vwap": vwap,
            "day_high": day_high,
            "day_low": day_low,
            "hi_idx": hi_idx,
            "lo_idx": lo_idx,
            "recent_low": min(prices[-30:]) if n >= 30 else day_low,
            "recent_high": max(prices[-30:]) if n >= 30 else day_high,
            "ma20": ma20,
            "day_base_vol": self._day_base_vol(dvs, n),
        }

    def _day_base_vol(self, dvs: List[float], n: int) -> float:
        """日内基准每分钟成交量：剔除首尾各若干分钟的均值。"""
        lo, hi = min(5, n), max(6, n - 8)
        seg = dvs[lo:hi] if hi > lo else dvs
        m = _mean(seg)
        if m is None or m <= 0:
            m = _mean(dvs[1:]) or 0.0
        return m if m > 0 else 1.0

    # ------------------------------------------------------------------
    # 形态识别
    # ------------------------------------------------------------------
    def _detect_patterns(
        self, st: dict, cur: float, prev_close: float
    ) -> List[dict]:
        prices = st["prices"]
        dvs = st["dvs"]
        n = st["n"]
        vwap = st["vwap"]
        base = st["day_base_vol"]
        day_high = st["day_high"]
        pct_day = (cur / prev_close - 1) * 100.0
        pullback = (day_high - cur) / day_high * 100.0  # 距日高回落 %
        pct_vwap = (cur / vwap - 1) * 100.0

        last_k = min(15, n - 1)
        last_seg = dvs[n - last_k:n]
        chg_last = (prices[-1] / prices[n - 1 - last_k] - 1) * 100.0
        vol_ratio = (_mean(last_seg) or 0.0) / base  # 近15分钟量 / 日内基准量
        chg_5 = (prices[-1] / prices[n - 6] - 1) * 100.0 if n > 5 else 0.0
        hi_idx = st["hi_idx"]
        since_high = n - 1 - hi_idx  # 距日内高点已过分钟数

        patterns: List[dict] = []

        def add(tag, name, desc, tone):
            patterns.append({"tag": tag, "name": name, "desc": desc, "tone": tone})

        # ---- 现价距日高较近：拉升/滞涨状态 ----
        if pullback < 1.0:
            if chg_last >= 1.2:
                if vol_ratio >= 1.35:
                    if pct_day <= 5.5:
                        add("vol_up", "放量上攻",
                            "近15分钟上涨 %.2f%% 且量能为日内均量的 %.0f%%，价量配合" % (chg_last, vol_ratio * 100),
                            "good")
                    else:
                        add("chase_zone", "高位放量冲高",
                            "当日已涨 %.2f%% 仍放量上冲，处追高区，谨防冲高诱多" % pct_day, "risk")
                elif vol_ratio <= 0.8:
                    add("no_vol_up", "无量拉升",
                        "近15分钟上涨 %.2f%% 但量能仅日内均量的 %.0f%%，承接不足、易冲高回落" % (chg_last, vol_ratio * 100),
                        "risk")
                else:
                    add("rising", "缓步拉升",
                        "近15分钟上涨 %.2f%%，量能温和（日内均量的 %.0f%%）" % (chg_last, vol_ratio * 100),
                        "neutral")
            elif chg_last <= -0.8:
                if vol_ratio >= 1.35:
                    add("vol_dump", "放量回落",
                        "近15分钟下跌 %.2f%% 且量能放大至日内均量的 %.0f%%，抛压较重" % (-chg_last, vol_ratio * 100),
                        "risk")
                else:
                    add("shrink_drop", "缩量回调",
                        "近15分钟回落 %.2f%%、量能萎缩（日内均量的 %.0f%%），属获利回吐式缩量回调" % (-chg_last, vol_ratio * 100),
                        "neutral")
            else:
                add("flat_high", "高位横盘",
                    "价格贴着日内高位横盘，等待方向选择" if pct_day >= 0 else "低位横盘震荡，量能清淡",
                    "neutral")

        # ---- 已从高点回落 >=1% ----
        else:
            drop_k = max(3, since_high)
            drop_vol = (_mean(dvs[hi_idx + 1:n]) or 0.0) / base if n - hi_idx > 2 else 0.0
            drop_pct = (cur / day_high - 1) * 100.0  # 相对日高（负值）

            if since_high <= 120 and pct_day >= 0.3:
                # 冲高后不久、当日仍红盘
                if cur < vwap or drop_vol >= 1.25:
                    add("spike_fade", "冲高回落（疑似诱多）",
                        "盘中放量冲至日内高点 %.2f 后回落 %.2f%%，现价%s分时均价"
                        % (day_high, -drop_pct, "已跌破" if cur < vwap else "仅贴近"),
                        "risk")
                else:
                    add("pullback_hold", "冲高后缩量回踩",
                        "冲高至日内高点 %.2f 后小幅缩量回踩 %.2f%%，仍守住分时均价上方" % (day_high, -drop_pct),
                        "good")
            elif since_high <= 120:
                # 冲高后不久、已回落绿盘
                if drop_vol >= 1.25:
                    add("spike_dump", "冲高跳水（放量出货嫌疑）",
                        "冲高后放量回落至绿盘 %.2f%%，量能达日内均量的 %.0f%%" % (-drop_pct, drop_vol * 100),
                        "risk")
                else:
                    add("shrink_drop", "缩量回调",
                        "冲高后回落至绿盘 %.2f%% 但为缩量回调（日内均量的 %.0f%%），恐慌有限" % (-drop_pct, drop_vol * 100),
                        "neutral")
            else:
                # 日内高点出现在较久之前
                if pullback >= 2.5:
                    add("off_high", "大幅脱离日内高点",
                        "现价较日内高点 %.2f 回落 %.2f%%，全天呈冲高回落/走弱结构" % (day_high, -drop_pct),
                        "risk")
                elif cur < vwap * 0.997:
                    if pct_day >= 0.8:
                        add("fade_below_vwap", "冲高回落（跌破均价）",
                            "当日曾冲高 %.2f，现价已跌回分时均价下方 %.2f%%，冲高诱多嫌疑"
                            % (day_high, -pct_vwap),
                            "risk")
                    else:
                        add("below_vwap", "弱势于分时均价",
                            "现价低于分时均价 %.2f%%，分时偏弱" % -pct_vwap,
                            "neutral")
                else:
                    add("pullback_hold", "回落守均价",
                        "现价自日内高点 %.2f 回落 %.2f%% 后仍守在分时均价附近/上方，属强势整理"
                        % (day_high, -drop_pct),
                        "good")

        # ---- 量价齐升（健康形态，窗口较长时判断） ----
        if n >= 25 and chg_last > 0 and pct_day >= -0.5 and pct_day <= 6:
            win = 20
            up_vols: List[float] = []
            dn_vols: List[float] = []
            up_cnt = 0
            for i in range(n - win, n):
                if dvs[i] <= 0:
                    continue
                if prices[i] > prices[i - 1]:
                    up_vols.append(dvs[i])
                    up_cnt += 1
                elif prices[i] < prices[i - 1]:
                    dn_vols.append(dvs[i])
            up_v = _mean(up_vols) or 0.0
            dn_v = _mean(dn_vols) or 0.0
            if up_cnt >= 12 and up_v >= base * 0.9 and up_v >= dn_v * 1.15:
                add("vol_price_rise", "量价齐升",
                    "近20分钟上涨分钟占比高（%d/20）且上涨量能为下跌量能的 %.0f%%，买盘主动" % (up_cnt, up_v / dn_v * 100 if dn_v > 0 else 0),
                    "good")

        # ---- 缩量回踩支撑（出现低价支撑机会） ----
        if chg_last <= -0.3 and vol_ratio <= 0.8:
            near_low = (cur - st["day_low"]) / st["day_low"] * 100.0
            if near_low <= 1.2 and pct_day >= -3:
                add("dip_support", "缩量回踩至日低附近",
                    "现价距日内低点仅 %.2f%%，缩量回踩，若不再破低则存在低吸机会" % near_low,
                    "good")

        return patterns

    # ------------------------------------------------------------------
    # 结论
    # ------------------------------------------------------------------
    def _decide(
        self,
        st: dict,
        cur: float,
        prev_close: float,
        patterns: List[dict],
        quote: dict,
    ) -> Tuple[dict, Optional[dict], List[str]]:
        vwap = st["vwap"]
        day_high = st["day_high"]
        day_low = st["day_low"]
        ma20 = st["ma20"]
        pct_day = (cur / prev_close - 1) * 100.0
        pct_vwap = (cur / vwap - 1) * 100.0
        pullback = (day_high - cur) / day_high * 100.0

        tags = [p["tag"] for p in patterns]
        score = 50.0
        notes: List[str] = []

        # 看空/风险项
        if "spike_fade" in tags or "spike_dump" in tags:
            score -= 30
            notes.append("出现冲高回落/诱多形态，追高者易被套在日内高位")
        if "fade_below_vwap" in tags:
            score -= 18
            notes.append("当日冲高后跌回分时均价下方，呈冲高诱多走势")
        if "no_vol_up" in tags:
            score -= 20
            notes.append("拉升无量，量能跟不上价格，冲高回落概率大")
        if "vol_dump" in tags:
            score -= 24
            notes.append("放量回落，说明上方抛压沉重")
        if "chase_zone" in tags:
            score -= 22
            notes.append("处于高位放量冲高段，当日涨幅已大，不宜市价追")
        if "off_high" in tags:
            score -= 14
            notes.append("现价已明显脱离日内高点，分时结构转弱")
        if pct_day >= 6.5 and pullback < 1.5:
            score -= 18
            notes.append("当日涨幅 %.2f%% 且贴近日内高点，追高风险大" % pct_day)
        if pct_vwap < -1.5:
            score -= 8
            notes.append("现价低于分时均价 %.2f%%，分时处于弱势区" % (-pct_vwap))

        # 看多/加分项
        if "vol_price_rise" in tags:
            score += 18
        if "vol_up" in tags:
            score += 14
        if "dip_support" in tags:
            score += 12
        if "pullback_hold" in tags:
            score += 8
        if pct_vwap >= 0.5:
            score += 6
            notes.append("现价站上分时均价 %.2f%%，当日分时偏强" % pct_vwap)
        if "shrink_drop" in tags and pct_day >= -2.5:
            score += 6
            notes.append("回调为缩量性质，属获利回吐而非恐慌出逃")

        # 参考价位
        support_price = vwap if cur > vwap else None
        support_note = "回踩分时均价 %s 企稳再介入" % _fmt(vwap)
        if support_price is None:
            support_price = st["recent_low"]
            support_note = "站稳分时均价 %s / 日内低点 %s 之上再介入" % (_fmt(vwap), _fmt(day_low))
        if ma20:
            support_note += "；中线参考 MA20 %s" % _fmt(ma20)

        score = _clamp(score)
        has_hard_risk = any(
            t in tags
            for t in ("spike_fade", "spike_dump", "fade_below_vwap", "no_vol_up", "vol_dump", "chase_zone", "off_high")
        )

        reasons: List[str] = []
        verdict: dict
        suggestion: Optional[dict]

        if score >= 62 and not has_hard_risk:
            verdict = {
                "action": "market",
                "tone": "allow",
                "title": "✓ 可以当前市价买入（轻仓试探）",
            }
            short_note = "分时均价 %s" % _fmt(vwap) if cur > vwap else "分时均价 %s / 日内低点 %s" % (_fmt(vwap), _fmt(day_low))
            suggestion = {
                "price": round(cur, 2),
                "kind": "market",
                "note": "现价 %s 可市价单轻仓买入；若回踩 %s 附近企稳可再加一笔" % (_fmt(cur), short_note),
            }
            reasons.append("分时量价形态健康，无诱多/无量拉升等危险特征，市价单风险可控")
        elif score >= 45:
            verdict = {
                "action": "limit",
                "tone": "deny",
                "title": "不建议市价追高 —— 挂限价单等回踩",
            }
            suggestion = {
                "price": round(support_price, 2) if support_price else round(cur, 2),
                "kind": "limit",
                "note": support_note + "；市价单易追在日内高位",
            }
            reasons.append("现价位置一般/存在回落风险，直接市价买入易买贵，建议限价挂单等回踩")
        else:
            verdict = {
                "action": "wait",
                "tone": "deny",
                "title": "✗ 暂不宜买入 —— 建议观望",
            }
            suggestion = {
                "price": round(support_price, 2) if support_price else None,
                "kind": "wait",
                "note": support_note + "；出现放量企稳再考虑介入",
            }
            reasons.append("分时形态偏弱或危险特征明显，市价买入胜率低，等待企稳信号")

        reasons = notes + reasons
        reasons.append("市价单按对手价立即成交、存在滑点：建议优先使用限价单控制成交价")
        return verdict, suggestion, reasons

    # ------------------------------------------------------------------
    # 交易状态文案
    # ------------------------------------------------------------------
    @staticmethod
    def _trade_note(data_date: str, rows: List[dict]) -> str:
        today = time.strftime("%Y%m%d")
        if not data_date:
            return "暂无分时数据"
        now = time.strftime("%H%M")
        in_session = ("0925" <= now <= "1135") or ("1255" <= now <= "1505")
        last_t = str(rows[-1].get("time") or "") if rows else ""
        if data_date == today:
            if in_session and last_t:
                return "今日盘中（分时截至 %s:%s）" % (last_t[:2], last_t[2:])
            if rows:
                return "今日已收盘，以下基于今日完整分时形态"
            return "今日分时暂无数据"
        d = "%s-%s-%s" % (data_date[0:4], data_date[4:6], data_date[6:8])
        return "当前非交易时段：最近交易日 %s 分时（静态分析，供盘后复盘参考）" % d


def _fmt(v: Optional[float]) -> str:
    return "--" if v is None else ("%.2f" % v)
