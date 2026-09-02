# -*- coding: utf-8 -*-
"""Stock-Ossec-Tools 后端服务入口（Python 3.8 兼容）。

启动::

    python app.py          # 默认 http://0.0.0.0:5000

若存在 frontend/dist 构建产物，则同时托管前端静态页面（单进程部署）。
"""

import logging
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.eastmoney import EastMoneyService
from services.rankings import RankingsService
from services.kline import KlineService

try:  # python -m backend.app（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config

app = Flask(__name__, static_folder=None)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("stock-ossec-tools")

service = EastMoneyService()
rankings = RankingsService()
kline = KlineService()


def ok(data=None, message="ok"):
    """统一成功响应。"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message, code=1, status=200):
    """统一失败响应。"""
    return jsonify({"code": code, "message": message, "data": None}), status


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    """兜底异常处理：未预期错误返回 JSON 500，避免泄露堆栈。"""
    logger.exception("Unhandled error: %s", exc)
    return fail("服务器内部错误，请稍后重试", code=500, status=500)


@app.route("/api/health")
def health():
    return ok({"status": "up", "service": "stock-ossec-tools-backend"})


@app.route("/api/indices")
def indices():
    market = request.args.get("market", "cn")
    if market not in config.INDICES:
        return fail("market 仅支持 cn / asia / us / futures", code=400, status=400)
    data, source = service.get_indices(market)
    return ok({"market": market, "label": config.MARKET_LABELS.get(market, market), "source": source, "items": data})


@app.route("/api/stock/search")
def stock_search():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return ok([])
    try:
        count = max(1, min(20, int(request.args.get("count", "8"))))
    except ValueError:
        count = 8
    data = service.search(keyword, count)
    return ok(data)


@app.route("/api/stock/quote")
def stock_quote():
    code = request.args.get("code", "").strip()
    if not code:
        return fail("缺少 code 参数", code=400, status=400)
    if not (code.isdigit() and len(code) == 6):
        return fail("股票代码格式不正确，应为 6 位数字", code=400, status=400)
    try:
        data, source = service.get_quote(code)
    except Exception:  # 双数据源均失败
        return fail("行情服务暂时不可用，请稍后重试", code=503, status=503)
    if data is None:
        return fail("未查询到该股票行情，请检查代码是否正确", code=404, status=404)
    data["source"] = source
    return ok(data)


@app.route("/api/stock/batch")
def stock_batch():
    codes = request.args.get("codes", "").strip()
    if not codes:
        return ok([])
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if len(code_list) > 50:
        return fail("单次最多查询 50 只股票", code=400, status=400)
    for c in code_list:
        if not (c.isdigit() and len(c) == 6):
            return fail("股票代码格式不正确：%s" % c, code=400, status=400)
    try:
        data = service.get_batch_quotes(code_list)
    except Exception:
        return fail("行情服务暂时不可用，请稍后重试", code=503, status=503)
    return ok(data)


@app.route("/api/rankings/market-breadth")
def market_breadth():
    try:
        data = rankings.market_breadth()
    except Exception:
        return fail("行情数据暂时不可用，请稍后重试", code=503, status=503)
    if data is None:
        return fail("市场涨跌分布数据暂时不可用", code=503, status=503)
    return ok(data)


@app.route("/api/rankings/industry-flow")
def industry_flow():
    try:
        limit = max(5, min(50, int(request.args.get("limit", "20"))))
    except ValueError:
        limit = 20
    data = rankings.industry_flow(limit)
    return ok(data)


@app.route("/api/rankings/concept-flow")
def concept_flow():
    try:
        limit = max(5, min(50, int(request.args.get("limit", "20"))))
    except ValueError:
        limit = 20
    data = rankings.concept_flow(limit)
    return ok(data)


@app.route("/api/rankings/stock-flow")
def stock_flow():
    try:
        limit = max(5, min(50, int(request.args.get("limit", "20"))))
    except ValueError:
        limit = 20
    data = rankings.stock_flow(limit)
    return ok(data)


@app.route("/api/rankings/top")
def stock_rank():
    sort = request.args.get("type", "gainers")
    if sort not in ("gainers", "losers", "amount", "turnover"):
        return fail("type 仅支持 gainers / losers / amount / turnover", code=400, status=400)
    try:
        limit = max(5, min(100, int(request.args.get("limit", "20"))))
    except ValueError:
        limit = 20
    data = rankings.stock_rank(sort, limit)
    return ok(data)


def _valid_code(code):
    return code.isdigit() and len(code) == 6


@app.route("/api/stock/kline")
def stock_kline():
    code = request.args.get("code", "").strip()
    if not _valid_code(code):
        return fail("股票代码格式不正确，应为 6 位数字", code=400, status=400)
    period = request.args.get("period", "day")
    try:
        count = max(10, min(500, int(request.args.get("count", "120"))))
    except ValueError:
        count = 120
    try:
        data = kline.get_kline(code, period, count)
    except Exception:
        return fail("K线数据暂时不可用，请稍后重试", code=503, status=503)
    return ok(data)


@app.route("/api/stock/minute")
def stock_minute():
    code = request.args.get("code", "").strip()
    if not _valid_code(code):
        return fail("股票代码格式不正确，应为 6 位数字", code=400, status=400)
    try:
        data = kline.get_minute(code)
    except Exception:
        return fail("分时数据暂时不可用，请稍后重试", code=503, status=503)
    return ok(data)


@app.route("/api/stock/indicators")
def stock_indicators():
    code = request.args.get("code", "").strip()
    if not _valid_code(code):
        return fail("股票代码格式不正确，应为 6 位数字", code=400, status=400)
    period = request.args.get("period", "day")
    try:
        data = kline.get_indicators(code, period)
    except Exception:
        return fail("指标数据暂时不可用，请稍后重试", code=503, status=503)
    if data is None:
        return fail("历史K线数据不足，暂无法计算指标", code=404, status=404)
    return ok(data)


# ----------------------------------------------------------------------
# 7x24 财经新闻
# ----------------------------------------------------------------------
@app.route("/api/news/7x24")
def news_7x24():
    """7x24小时财经新闻（来自东方财富）。"""
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        page_size = max(1, min(50, int(request.args.get("page_size", "20"))))
    except ValueError:
        page_size = 20

    try:
        import requests as _requests
        resp = _requests.get(
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns",
            params={
                "client": "web",
                "biz": "web_724",
                "column": "350",
                "order": "1",
                "needInteractData": "0",
                "page_index": page,
                "page_size": page_size,
            },
            timeout=10,
        )
        payload = resp.json()
    except Exception as e:
        logging.warning("获取7x24新闻失败: %s", e)
        return ok([])

    data = (payload or {}).get("data") or {}
    items = data.get("list") or []
    result = []
    for item in items:
        result.append({
            "title": item.get("title", ""),
            "content": item.get("digest", "") or item.get("content", ""),
            "source": item.get("media_name", "") or item.get("source", ""),
            "time": item.get("showtime", "") or item.get("publish_time", ""),
            "url": item.get("url", ""),
        })
    return ok(result)


# ----------------------------------------------------------------------
# 东财热榜
# ----------------------------------------------------------------------
@app.route("/api/hotlist")
def hotlist():
    """东方财富人气榜/飙升榜。"""
    sort_type = request.args.get("type", "popular")  # popular: 人气榜, surge: 飙升榜
    market = request.args.get("market", "a")  # a: A股, hk: 港股, us: 美股

    try:
        import requests as _requests
        # 东方财富热榜接口
        resp = _requests.post(
            "https://emappdata.eastmoney.com/stockrank/getAllCurrentList",
            json={
                "appId": "appId01",
                "globalId": "786e4c21-70dc-435a-93bb-38",
                "marketType": "",
                "pageNo": 1,
                "pageSize": 50,
                "rankType": "1" if sort_type == "popular" else "2",
            },
            timeout=10,
        )
        payload = resp.json()
    except Exception as e:
        logging.warning("获取东财热榜失败: %s", e)
        return ok([])

    data = (payload or {}).get("data") or []
    result = []
    for idx, item in enumerate(data):
        result.append({
            "rank": idx + 1,
            "code": item.get("sc", ""),
            "name": item.get("sn", ""),
            "price": item.get("p", 0),
            "change": item.get("zdp", 0),
            "new_fans": item.get("xgf", 0),
            "total_fans": item.get("fg", 0),
        })
    return ok(result)


# ----------------------------------------------------------------------
# 生产模式：托管前端构建产物
# ----------------------------------------------------------------------
@app.route("/")
def index_page():
    if not os.path.isdir(config.FRONTEND_DIST):
        return (
            "后端 API 正常。前端尚未构建：请先进入 frontend 目录执行 "
            "npm install && npm run build，再刷新本页面。",
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    return send_from_directory(config.FRONTEND_DIST, "index.html")


@app.route("/<path:path>")
def static_files(path):
    # 未定义的 API 路径返回 JSON 404，避免误命中前端兜底
    if path.startswith("api/"):
        return fail("接口不存在", code=404, status=404)
    if os.path.isfile(os.path.join(config.FRONTEND_DIST, path)):
        return send_from_directory(config.FRONTEND_DIST, path)
    if os.path.isdir(config.FRONTEND_DIST):
        return send_from_directory(config.FRONTEND_DIST, "index.html")
    return fail("not found", code=404, status=404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
