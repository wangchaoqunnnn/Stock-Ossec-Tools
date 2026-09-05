# -*- coding: utf-8 -*-
"""个股打分引擎（Python 3.8 兼容）。

六个维度打分（各 0-100），每项给出基于真实行情数据的理由：
  ① 基础面（估值近似业绩）：以市盈率 PE(TTM)、市净率 PB 为代理
  ② 所属板块热度：所属行业在行业资金净流入榜中的排名与流入
  ③ 技术面：日/周/月 K 线均线多头排列与上升趋势强度
  ④ 短线情绪：量比、换手、当日涨跌、涨速
  ⑤ 买点：价格相对均线/RSI/KDJ/近期低点的位置
  ⑥ 综合：加权汇总 ①-⑤

并给出操作建议：可买（红）/暂不宜买（绿，给出长线/短线/超短买点）。
观察池策略：综合 >= 60 或买点 >= 60 视为值得跟踪。
"""

from typing import Any, Dict, List, Optional, Tuple

from .eastmoney import EastMoneyService
from .kline import KlineService
from .rankings import RankingsService


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _pct(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return round(float(v), 2)


class StockScorer(object):
    def __init__(self) -> None:
        self._em = EastMoneyService()
        self._kline = KlineService()
        self._rank = RankingsService()

    # ------------------------------------------------------------------
    # 各维度打分
    # ------------------------------------------------------------------
    @staticmethod
    def score_fundamental(pe: Optional[float], pb: Optional[float]) -> Tuple[float, List[str]]:
        """① 基础面（以估值近似业绩）。"""
        reasons: List[str] = []
        if pe is None and pb is None:
            return 50.0, ["缺少市盈率/市净率数据，给中性分"]
        pe_s = 50.0
        if pe is not None:
            if pe <= 0:
                pe_s = 25.0
                reasons.append("市盈率(亏损/负值) %s，业绩承压" % _pct(pe))
            elif pe <= 15:
                pe_s = 85.0
                reasons.append("市盈率(TTM) %s，估值较低、盈利稳健" % _pct(pe))
            elif pe <= 30:
                pe_s = 70.0
                reasons.append("市盈率(TTM) %s，估值合理" % _pct(pe))
            elif pe <= 50:
                pe_s = 50.0
                reasons.append("市盈率(TTM) %s，估值偏高" % _pct(pe))
            else:
                pe_s = 30.0
                reasons.append("市盈率(TTM) %s，估值过高，需业绩兑现" % _pct(pe))
        else:
            reasons.append("缺少市盈率数据")

        pb_s = 50.0
        if pb is not None:
            if pb <= 0:
                pb_s = 25.0
            elif pb <= 1.5:
                pb_s = 85.0
                reasons.append("市净率 %s，接近净资产，安全边际高" % _pct(pb))
            elif pb <= 5:
                pb_s = 60.0
                reasons.append("市净率 %s，处于中性水平" % _pct(pb))
            else:
                pb_s = 35.0
                reasons.append("市净率 %s，估值高于行业均值" % _pct(pb))
        score = _clamp(0.65 * pe_s + 0.35 * pb_s)
        return round(score, 1), reasons

    @staticmethod
    def score_sector(industry: str, flow_rows: List[dict]) -> Tuple[float, List[str]]:
        """② 所属板块热度。"""
        reasons: List[str] = []
        if not industry:
            return 50.0, ["未获取到所属行业数据，给中性分"]
        idx = None
        for i, row in enumerate(flow_rows):
            if row.get("name") == industry:
                idx = i
                break
        if idx is None:
            return 50.0, ["行业「%s」未进入资金流榜前列" % industry]
        net = flow_rows[idx].get("net_inflow") or 0.0
        pct = flow_rows[idx].get("pct") or 0.0
        pos_score = _clamp((len(flow_rows) - idx) / len(flow_rows) * 70 + 20)  # 排名越前越高
        inflow_bonus = 15 if net > 0 else -10
        pct_bonus = _clamp(5 * pct, -10, 10)
        score = _clamp(pos_score + inflow_bonus + pct_bonus)
        reasons.append(
            "所属行业「%s」主力净流入 %s 亿，涨 %.2f%%，资金流榜第 %d/%d"
            % (industry, round(net / 1e8, 2), pct, idx + 1, len(flow_rows))
        )
        if score >= 65:
            reasons.append("行业处于资金流入前列，属于相对热门板块")
        elif score <= 40:
            reasons.append("行业资金呈流出或榜位靠后，热度一般")
        return round(score, 1), reasons

    @staticmethod
    def score_technical(day: Optional[dict], week: Optional[dict], month: Optional[dict]) -> Tuple[float, List[str]]:
        """③ 技术面：日/周/月 K 线上升趋势强度。"""
        reasons: List[str] = []

        def _tf_score(ind: Optional[dict], label: str) -> float:
            if not ind or not ind.get("kline"):
                reasons.append("%s：K线数据不足" % label)
                return 50.0
            kline = ind["kline"]
            ma = ind["indicators"]["ma"]
            closes = [r["close"] for r in kline if r.get("close") is not None]
            if not closes:
                reasons.append("%s：K线数据不足" % label)
                return 50.0
            price = closes[-1]
            ma5 = ma.get("ma5")
            ma20 = ma.get("ma20")
            ma60 = ma.get("ma60")
            s = 50.0
            if price > ma20 and ma20 > ma60:
                s = 82.0
                reasons.append("%s：价格站上 MA20/MA60，呈多头趋势" % label)
            elif price > ma60:
                s = 62.0
                reasons.append("%s：价格位于 MA60 上方，趋势中性偏多" % label)
            elif price > ma5:
                s = 45.0
                reasons.append("%s：价格跌破中期均线，短线反弹中" % label)
            else:
                s = 28.0
                reasons.append("%s：价格位于 MA60 下方，处于下行趋势" % label)
            # 短线斜率
            if len(closes) >= 6 and closes[-1] > closes[-6]:
                s = _clamp(s + 6)
                reasons.append("%s：近5周期收涨" % label)
            elif len(closes) >= 6:
                s = _clamp(s - 6)
            return s

        s_day = _tf_score(day, "日线")
        s_week = _tf_score(week, "周线")
        s_month = _tf_score(month, "月线")
        score = _clamp(0.5 * s_day + 0.3 * s_week + 0.2 * s_month)
        return round(score, 1), reasons

    @staticmethod
    def score_sentiment(quote: dict) -> Tuple[float, List[str]]:
        """④ 短线情绪：量比/换手/涨跌幅/涨速。"""
        reasons: List[str] = []
        pct = quote.get("change_pct")
        vr = quote.get("volume_ratio")
        turnover = quote.get("turnover")
        speed = quote.get("speed")
        s = 50.0
        if pct is not None:
            s += _clamp(pct * 2.2, -25, 25)
            if pct >= 5:
                reasons.append("当日上涨 %.2f%%，短线强势" % pct)
            elif pct <= -3:
                reasons.append("当日下跌 %.2f%%，短线情绪偏弱" % pct)
            else:
                reasons.append("当日涨跌 %.2f%%，情绪平稳" % pct)
        if vr is not None:
            if vr >= 2:
                s += 8
                reasons.append("量比 %.2f，明显放量" % vr)
            elif vr <= 0.6:
                s -= 6
                reasons.append("量比 %.2f，缩量" % vr)
        if turnover is not None:
            if turnover >= 8:
                s += 5
                reasons.append("换手率 %.2f%%，交投活跃" % turnover)
        if speed is not None:
            if speed >= 1:
                s += 8
                reasons.append("涨速 %.2f%%，盘口拉升" % speed)
            elif speed <= -1:
                s -= 8
                reasons.append("涨速 %.2f%%，盘口走弱" % speed)
        if not reasons:
            reasons.append("短线量价数据有限，给中性分")
        return round(_clamp(s), 1), reasons

    @staticmethod
    def score_buy_point(day: Optional[dict], price: Optional[float]) -> Tuple[float, List[str], Optional[float], Optional[float], Optional[float]]:
        """⑤ 买点打分（结合技术指标与价格位置）。

        返回 (score, reasons, 短线参考支撑, 观察确认价, 突破确认价)。
        """
        reasons: List[str] = []
        if not day or not day.get("indicators"):
            return 50.0, ["K线指标不足，无法判断买点"], None, None, None
        ind = day["indicators"]
        kline = day.get("kline") or []
        ma = ind.get("ma", {})
        price = price or (kline[-1].get("close") if kline else None)
        ma5 = ma.get("ma5")
        ma20 = ma.get("ma20")
        ma60 = ma.get("ma60")
        rsi = (ind.get("rsi") or {}).get("value")
        kdj = ind.get("kdj") or {}
        kd, jd = kdj.get("k"), kdj.get("d")
        boll = ind.get("boll") or {}
        s = 50.0
        if price and ma20:
            ratio = (price - ma20) / ma20 * 100
            if -2 <= ratio <= 3:
                s += 15
                reasons.append("现价距 MA20 仅 %.1f%%，接近短线支撑区" % ratio)
                short_support = round(ma20, 2)
            elif ratio > 8:
                s -= 15
                reasons.append("现价高出 MA20 达 %.1f%%，短期乖离偏大，追高风险" % ratio)
                short_support = round(ma20, 2)
            else:
                reasons.append("现价相对 MA20 乖离 %.1f%%" % ratio)
                short_support = round(ma20, 2)
        else:
            short_support = None
        if rsi is not None:
            if 35 <= rsi <= 60:
                s += 8
                reasons.append("RSI %.1f，位于健康区间，未超买" % rsi)
            elif rsi >= 75:
                s -= 12
                reasons.append("RSI %.1f，已进入超买区" % rsi)
            elif rsi <= 25:
                s += 10
                reasons.append("RSI %.1f，处于超卖区，存在反弹需求" % rsi)
        if kd is not None and jd is not None:
            if kd > jd and kd < 80:
                s += 6
                reasons.append("KDJ K(%.1f)>D(%.1f)，金叉向上" % (kd, jd))
            elif kd < jd:
                s -= 6
                reasons.append("KDJ K(%.1f)<D(%.1f)，短期偏弱" % (kd, jd))
        if boll.get("lower") and price and price <= boll["lower"] * 1.02:
            s += 6
            reasons.append("价格贴近布林下轨，处于超卖支撑区")
        recent_lows = [r.get("low") for r in kline[-20:] if r.get("low") is not None]
        observe_price = short_support
        if recent_lows:
            support = min(recent_lows)
            if short_support is None:
                short_support = round(support, 2)
            # 突破确认：近20日高点
            recent_highs = [r.get("high") for r in kline[-20:] if r.get("high") is not None]
            break_price = round(max(recent_highs), 2) if recent_highs else None
        else:
            break_price = None
        score = round(_clamp(s), 1)
        if score < 40:
            reasons.append("当前价格位置不佳，买点未现")
        return score, reasons, short_support, observe_price, break_price

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def score(self, code: str) -> Optional[dict]:
        """对个股进行六维打分并给出操作建议。"""
        code = str(code or "").strip()
        if not code:
            return None

        quote, _src = self._em.get_quote(code)
        if not quote:
            return None
        name = quote.get("name") or code
        price = quote.get("now_price")
        pct = quote.get("change_pct")

        # 行业与涨速等：批量接口（东财含行业/涨速，失败回退后为空则降级）
        batch = self._em.get_batch_quotes([code])
        row = batch[0] if batch else {}
        industry = row.get("industry") or ""
        if not industry:
            # 主源（push2）不可达、批量行情回退腾讯时无行业字段：
            # 依次尝试 push2delay f100 / 东财 F10 所属板块报告补全所属行业。
            industry = self._em.resolve_industry(code)
        speed = row.get("speed")
        for k in ("pe", "pb", "turnover", "volume_ratio"):
            if quote.get(k) is None:
                quote[k] = row.get(k)
        if speed is not None:
            quote["speed"] = speed

        # 行业资金流榜单（板块热度用）
        flow_rows = self._rank.industry_flow(30)

        # 日/周/月 K 线指标
        day = self._kline.get_indicators(code, "day", 120)
        week = self._kline.get_indicators(code, "week", 80)
        month = self._kline.get_indicators(code, "month", 60)

        fs, fs_r = self.score_fundamental(quote.get("pe"), quote.get("pb"))
        ss, ss_r = self.score_sector(industry, flow_rows)
        ts, ts_r = self.score_technical(day, week, month)
        es, es_r = self.score_sentiment(quote)
        bs, bs_r, short_support, observe_price, break_price = self.score_buy_point(day, price)

        # 综合：基础20 板块10 技术25 情绪15 买点30
        composite = round(_clamp(0.20 * fs + 0.10 * ss + 0.25 * ts + 0.15 * es + 0.30 * bs), 1)

        # 操作建议
        can_buy = composite >= 60 and bs >= 55 and (ts >= 50 or es >= 60)
        advice_lines: List[str] = []
        if can_buy:
            advice_lines.append("综合打分 %.1f、买点打分 %.1f，当前技术/买点条件成立，可少量买入或分批建仓" % (composite, bs))
            advice_lines.append("策略：现价附近轻仓试仓；跌破短线支撑（MA20/近期低点）止损观察。")
        else:
            advice_lines.append("综合打分 %.1f、买点打分 %.1f，当前时刻不具备良好买点，暂不建议追入" % (composite, bs))
        if ts <= 45:
            advice_lines.append("技术面偏弱（%.1f），下行趋势未扭转前以观望为主" % ts)
        if es <= 40:
            advice_lines.append("短线情绪低迷（%.1f），不宜抢反弹" % es)

        buy_points: List[dict] = []
        if not can_buy:
            if short_support:
                buy_points.append({
                    "type": "超短",
                    "price": short_support,
                    "note": "回踩短线支撑（MA20/近期低点附近）企稳可低吸，跌破不接",
                })
            observe = observe_price if observe_price else short_support
            if observe:
                buy_points.append({
                    "type": "短线",
                    "price": observe,
                    "note": "回调至观察位（短线支撑）放量企稳后分批介入",
                })
            ma60v = None
            if day and day.get("indicators", {}).get("ma", {}).get("ma60"):
                ma60v = day["indicators"]["ma"]["ma60"]
            if ma60v:
                buy_points.append({
                    "type": "长线",
                    "price": round(ma60v, 2),
                    "note": "价值区参考（MA60 附近），适合分批定投式布局",
                })
            if break_price:
                buy_points.append({
                    "type": "突破",
                    "price": break_price,
                    "note": "放量突破近20日高点后确认趋势再加仓",
                })
        if not buy_points:
            buy_points.append({"type": "现价", "price": price, "note": "当前即可执行买入"})

        # 观察池策略：综合>=60 或 买点>=60 视为值得跟踪
        worth_track = composite >= 60 or bs >= 60

        return {
            "code": code,
            "name": name,
            "price": price,
            "change_pct": pct,
            "industry": industry,
            "pe": quote.get("pe"),
            "pb": quote.get("pb"),
            "source": _src,
            "scores": {
                "fundamental": {"score": fs, "reasons": fs_r},
                "sector": {"score": ss, "reasons": ss_r},
                "technical": {"score": ts, "reasons": ts_r},
                "sentiment": {"score": es, "reasons": es_r},
                "buy_point": {"score": bs, "reasons": bs_r},
                "composite": {"score": composite, "reasons": ["综合为五项加权：基础20%%+板块10%%+技术25%%+情绪15%%+买点30%%"]},
            },
            "can_buy": bool(can_buy),
            "advice": advice_lines,
            "buy_points": buy_points,
            "worth_track": bool(worth_track),
            "evaluated_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
