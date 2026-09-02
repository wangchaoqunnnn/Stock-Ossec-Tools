# -*- coding: utf-8 -*-
"""后端 API 单元测试（mock 上游行情接口，确定性验证）。

运行：cd backend && python -m unittest discover -s tests -v
"""

import json
import unittest
from unittest import mock

import app as app_module
from services import eastmoney as em
from services import rankings as rk

app = app_module.app
app.config["TESTING"] = False  # 走统一错误处理，便于断言响应结构


# ----------------------------------------------------------------------
# 工具：构造上游响应
# ----------------------------------------------------------------------
class FakeResponse(object):
    def __init__(self, payload, status=200, text=None):
        self._payload = payload
        self.status_code = status
        # 腾讯接口读 resp.text，东财接口读 resp.json()
        self.text = text if text is not None else json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise em.DataSourceError("HTTP %d" % self.status_code)

    def json(self):
        return self._payload


def make_tencent_line(code, name, price, change, change_pct, high, low, prev_close, open_, volume,
                      amount_wan, turnover, pe, pb, amplitude, float_mv_yi, total_mv_yi, volume_ratio):
    """构造腾讯 A 股行情行（字段布局与 qt.gtimg.cn 一致）。"""
    f = ["0"] * 60
    f[0] = "1"
    f[1] = name
    f[2] = code
    f[3] = str(price)
    f[4] = str(prev_close)
    f[5] = str(open_)
    f[6] = str(volume)
    f[30] = "20260901161439"
    f[31] = str(change)
    f[32] = str(change_pct)
    f[33] = str(high)
    f[34] = str(low)
    f[37] = str(amount_wan)
    f[38] = str(turnover)
    f[43] = str(amplitude)
    f[44] = str(float_mv_yi)
    f[45] = str(total_mv_yi)
    f[46] = str(pb)
    f[49] = str(volume_ratio)
    f[52] = str(pe)
    return 'v_%s="%s";' % (code, "~".join(f))


def em_quote_payload(code, name, price=10.0, change_pct=1.5, industry=None):
    """构造东财 stock/get 响应。"""
    d = {
        "f43": price, "f44": price + 0.5, "f45": price - 0.5, "f46": price - 0.1,
        "f47": 100000, "f48": 1e8, "f50": 1.2, "f57": code, "f58": name,
        "f60": price - 0.1, "f116": 5e10, "f117": 4e10, "f162": 15.0, "f167": 1.8,
        "f168": 2.5, "f169": price * change_pct / 100, "f170": change_pct,
        "f171": 3.0, "f86": 1720000000000,
    }
    return {"rc": 0, "data": d}


def em_ulist_payload(rows):
    """构造东财 ulist 响应。rows: [{code,name,price,pct,industry}]"""
    diff = []
    for r in rows:
        diff.append({
            "f12": r["code"], "f14": r.get("name", ""), "f2": r.get("price", 10.0),
            "f3": r.get("pct", 0.0), "f4": r.get("change", 0.0), "f5": 1000,
            "f6": 1e7, "f8": 1.0, "f9": 10.0, "f10": 1.1, "f15": 11.0, "f16": 9.0,
            "f17": 9.9, "f18": 9.8, "f20": 1e10, "f21": 9e9, "f22": 0.1, "f23": 1.5,
            "f100": r.get("industry", ""),
        })
    return {"rc": 0, "data": {"total": len(diff), "diff": diff}}


# ----------------------------------------------------------------------
# 测试
# ----------------------------------------------------------------------
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        em.requests.get = mock.Mock()
        em.time.sleep = mock.Mock()  # 关闭重试等待
        app_module.rankings._cache.clear()


class HealthTest(BaseTestCase):
    def test_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["status"], "up")


class IndicesTest(BaseTestCase):
    def test_invalid_market(self):
        resp = self.client.get("/api/indices?market=xxx")
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(resp.get_json()["code"], 0)

    def test_eastmoney_path(self):
        em.requests.get.return_value = FakeResponse(em_ulist_payload([
            {"code": "000001", "name": "上证指数", "price": 3979.89, "pct": -0.16, "change": -6.41},
            {"code": "399001", "name": "深证成指", "price": 13872.38, "pct": -1.02, "change": -142.6},
        ]))
        resp = self.client.get("/api/indices?market=cn")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["source"], "eastmoney")
        self.assertEqual(len(body["data"]["items"]), 6)  # cn 市场固定 6 项
        first = body["data"]["items"][0]
        self.assertEqual(first["name"], "上证指数")
        self.assertEqual(first["now"], 3979.89)

    def test_tencent_fallback_no_cross_market(self):
        # 东财失败 -> 回退腾讯；仅返回恒生指数，其余 asia 条目为 None
        class TencentResp(object):
            text = 'v_hkHSI="100~恒生指数~HSI~25032.540~25100.0~25010.0~1000~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0.0~2026/09/01 18:31:11~-67.46~-0.27~25100.0~24980.0~25032.5~1000~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0";'
            raise_for_status = lambda self: None

        def fake_get(url, timeout=8, **kw):
            if "qt.gtimg.cn" in url:
                return TencentResp()
            raise em.DataSourceError("eastmoney down")

        em.requests.get.side_effect = fake_get
        resp = self.client.get("/api/indices?market=asia")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["source"], "tencent")
        items = {i["name"]: i for i in body["data"]["items"]}
        self.assertEqual(items["恒生指数"]["now"], 25032.54)
        self.assertIsNone(items["日经225"]["now"])
        self.assertIsNone(items["台湾加权"]["now"])


class SearchTest(BaseTestCase):
    def test_empty_keyword(self):
        resp = self.client.get("/api/stock/search")
        self.assertEqual(resp.get_json()["data"], [])

    def test_codetable_results(self):
        em.requests.get.return_value = FakeResponse({"result": [
            {"code": "600000", "shortName": "浦发银行", "market": 1, "securityTypeName": "沪A"},
            {"code": "000938", "shortName": "紫光股份", "market": 0, "securityTypeName": "深A"},
            {"code": "360003", "shortName": "浦发优1", "market": 1, "securityTypeName": "债券"},
        ]})
        resp = self.client.get("/api/stock/search?keyword=浦发")
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 2)  # 债券被过滤
        self.assertEqual(data[1]["quote_id"], "0.000938")  # 深市 market=0 不再丢失

    def test_suggest_fallback(self):
        # codetable 失败 -> suggest
        def fake_get(url, params=None, retries=2, **kw):
            if "codetable" in url:
                raise em.DataSourceError("codetable down")
            return FakeResponse({"QuotationCodeTable": {"Data": [
                {"Code": "601318", "Name": "中国平安", "MarketType": 1, "SecurityTypeName": "沪A"},
            ]}})

        em.requests.get.side_effect = fake_get
        resp = self.client.get("/api/stock/search?keyword=平安")
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "601318")

    def test_count_clamped(self):
        em.requests.get.return_value = FakeResponse({"result": []})
        resp = self.client.get("/api/stock/search?keyword=x&count=999")
        self.assertEqual(resp.status_code, 200)


class QuoteTest(BaseTestCase):
    def test_missing_code(self):
        resp = self.client.get("/api/stock/quote")
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(resp.get_json()["code"], 0)

    def test_invalid_code(self):
        for bad in ("undefined", "123", "abcdef", "1234567", "12 345"):
            resp = self.client.get("/api/stock/quote?code=%s" % bad)
            self.assertEqual(resp.status_code, 400, bad)
            body = resp.get_json()
            self.assertEqual(body["code"], 400, bad)

    def test_eastmoney_quote(self):
        em.requests.get.return_value = FakeResponse(em_quote_payload("600519", "贵州茅台", price=1299.56, change_pct=0.0))
        resp = self.client.get("/api/stock/quote?code=600519")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["name"], "贵州茅台")
        self.assertEqual(body["data"]["source"], "eastmoney")
        self.assertEqual(body["data"]["now_price"], 1299.56)

    def test_tencent_fallback(self):
        def fake_get(url, timeout=8, **kw):
            if "qt.gtimg.cn" in url:
                return FakeResponse({}, status=200, text=make_tencent_line(
                    "sz000938", "紫光股份", 38.32, -0.63, -1.62, 39.55, 38.3,
                    38.95, 38.71, 1904614, 738676.0, 6.66, 25.29, 6.13, 3.21,
                    1095.98, 1095.98, 1.23))
            raise em.DataSourceError("eastmoney down")

        em.requests.get.side_effect = fake_get
        resp = self.client.get("/api/stock/quote?code=000938")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["source"], "tencent")
        self.assertEqual(body["data"]["name"], "紫光股份")
        self.assertEqual(body["data"]["now_price"], 38.32)
        self.assertEqual(body["data"]["change_pct"], -1.62)

    def test_both_sources_fail_503(self):
        em.requests.get.side_effect = em.DataSourceError("all down")
        resp = self.client.get("/api/stock/quote?code=600519")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.get_json()["code"], 503)

    def test_unknown_code_404(self):
        # 东财返回空 data，腾讯也无该代码
        def fake_get(url, timeout=8, **kw):
            if "qt.gtimg.cn" in url:
                return FakeResponse({"text": ""}, status=200)
            return FakeResponse({"rc": 0, "data": None})

        em.requests.get.side_effect = fake_get
        resp = self.client.get("/api/stock/quote?code=999999")
        self.assertEqual(resp.status_code, 404)

    def test_quote_cached(self):
        em.requests.get.return_value = FakeResponse(em_quote_payload("600000", "浦发银行"))
        self.client.get("/api/stock/quote?code=600000")
        first_calls = em.requests.get.call_count
        self.client.get("/api/stock/quote?code=600000")
        self.assertEqual(em.requests.get.call_count, first_calls, "第二次请求应命中缓存")


class BatchTest(BaseTestCase):
    def test_invalid_codes(self):
        resp = self.client.get("/api/stock/batch?codes=600519,abc")
        self.assertEqual(resp.status_code, 400)

    def test_too_many(self):
        codes = ",".join("600%03d" % i for i in range(60))
        resp = self.client.get("/api/stock/batch?codes=%s" % codes)
        self.assertEqual(resp.status_code, 400)

    def test_empty(self):
        resp = self.client.get("/api/stock/batch")
        self.assertEqual(resp.get_json()["data"], [])

    def test_eastmoney_batch(self):
        em.requests.get.return_value = FakeResponse(em_ulist_payload([
            {"code": "600519", "name": "贵州茅台", "price": 1299.56, "pct": 0.0, "industry": "白酒"},
            {"code": "300750", "name": "宁德时代", "price": 358.1, "pct": -1.5, "industry": "电池"},
        ]))
        resp = self.client.get("/api/stock/batch?codes=600519,300750")
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["industry"], "白酒")
        self.assertEqual(data[1]["now_price"], 358.1)


class RoutingTest(BaseTestCase):
    def test_unknown_api_404_json(self):
        resp = self.client.get("/api/not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()["code"], 404)

    def test_index_page_without_dist(self):
        with mock.patch.object(app_module.config, "FRONTEND_DIST", "/nonexistent/dist"):
            resp = self.client.get("/")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("后端 API 正常", resp.get_data(as_text=True))


class RankingsTest(BaseTestCase):
    def test_market_breadth(self):
        payload = {"data": {"fenbu": [
            {"-1": 10}, {"-10": 1}, {"0": 5}, {"1": 8}, {"10": 2},
        ]}}
        rk._get = mock.Mock(return_value=payload)
        resp = self.client.get("/api/rankings/market-breadth")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        d = body["data"]
        self.assertEqual(d["up"], 10)      # 涨幅档位 1(+8) 与 10(+2)
        self.assertEqual(d["down"], 11)    # 跌幅档位 -1(10) 与 -10(1)
        self.assertEqual(d["flat"], 5)
        self.assertEqual(d["limit_up"], 2)
        self.assertEqual(d["limit_down"], 1)
        self.assertEqual(d["total"], 26)

    def test_market_breadth_unavailable(self):
        rk._get = mock.Mock(side_effect=em.DataSourceError("down"))
        resp = self.client.get("/api/rankings/market-breadth")
        self.assertEqual(resp.status_code, 503)

    def test_industry_flow(self):
        payload = {"data": {"diff": [
            {"f12": "BK0475", "f14": "银行", "f2": 1000.0, "f3": 1.5, "f62": 2e8, "f184": 5.0},
            {"f12": "BK0476", "f14": "证券", "f2": 2000.0, "f3": -0.5, "f62": -1e8, "f184": -3.0},
        ]}}
        rk._get = mock.Mock(return_value=payload)
        resp = self.client.get("/api/rankings/industry-flow?limit=10")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(len(body["data"]), 2)
        self.assertEqual(body["data"][0]["name"], "银行")
        self.assertEqual(body["data"][0]["net_inflow"], 2e8)
        self.assertEqual(body["data"][1]["net_inflow"], -1e8)

    def test_stock_rank(self):
        payload = {"data": {"diff": [
            {"f12": "600000", "f14": "浦发银行", "f2": 9.35, "f3": 2.07, "f5": 1000,
             "f6": 1e8, "f8": 1.2, "f9": 5.0, "f10": 1.1, "f20": 1e10, "f23": 0.5, "f100": "银行"},
        ]}}
        rk._get = mock.Mock(return_value=payload)
        resp = self.client.get("/api/rankings/top?type=gainers&limit=10")
        body = resp.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["code"], "600000")
        self.assertEqual(body["data"][0]["industry"], "银行")

    def test_stock_rank_invalid_type(self):
        resp = self.client.get("/api/rankings/top?type=xxx")
        self.assertEqual(resp.status_code, 400)

    def test_rankings_clamp_limit(self):
        rk._get = mock.Mock(return_value={"data": {"diff": []}})
        resp = self.client.get("/api/rankings/top?type=gainers&limit=9999")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
