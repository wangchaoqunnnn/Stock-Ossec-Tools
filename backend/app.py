# -*- coding: utf-8 -*-
"""Stock-Ossec-Tools 后端服务入口（Python 3.8 兼容）。

启动::

    python app.py          # 默认 http://0.0.0.0:5000

若存在 frontend/dist 构建产物，则同时托管前端静态页面（单进程部署）。
"""

import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.eastmoney import EastMoneyService

try:  # python -m backend.app（项目根目录运行）
    from backend import config
except ImportError:  # python app.py（backend 目录运行）
    import config

app = Flask(__name__, static_folder=None)
CORS(app)

service = EastMoneyService()

# 关注清单字段：field -> (中文标签, 排序 key)
WATCH_SORTABLE = {
    "code": "代码",
    "now_price": "现价",
    "change_pct": "涨跌幅",
    "speed": "涨速",
    "turnover": "换手率",
    "volume_ratio": "量比",
    "pe": "市盈率",
    "pb": "市净率",
    "total_mv": "总市值",
    "float_mv": "流通市值",
}


def ok(data=None, message="ok"):
    """统一成功响应。"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message, code=1, status=200):
    """统一失败响应。"""
    return jsonify({"code": code, "message": message, "data": None}), status


def _num_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@app.route("/api/health")
def health():
    return ok({"status": "up", "service": "stock-ossec-tools-backend"})


@app.route("/api/indices")
def indices():
    market = request.args.get("market", "cn")
    if market not in config.INDICES:
        return fail("market 仅支持 cn / hk / us")
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
        return fail("缺少 code 参数")
    try:
        data, source = service.get_quote(code)
    except Exception:  # 双数据源均失败
        return fail("行情服务暂时不可用，请稍后重试", code=503, status=503)
    if data is None:
        return fail("未查询到该股票行情，请检查代码是否正确", code=404)
    data["source"] = source
    return ok(data)


@app.route("/api/watch/list")
def watch_list():
    rows, source = service.get_watch_list()

    sort = request.args.get("sort", "")
    order = request.args.get("order", "desc")
    try:
        page = max(1, int(request.args.get("page", "1")))
        page_size = int(request.args.get("page_size", "15"))
    except ValueError:
        page = 1
        page_size = 15
    page_size = max(5, min(50, page_size))

    if sort in WATCH_SORTABLE:
        reverse = order == "desc"

        def _has_value(r):
            return _num_or_none(r.get(sort)) is not None

        rows_with = [r for r in rows if _has_value(r)]
        rows_na = [r for r in rows if not _has_value(r)]
        rows_with.sort(key=lambda r: _num_or_none(r.get(sort)), reverse=reverse)
        rows = rows_with + rows_na

    total = len(rows)
    start = (page - 1) * page_size
    items = rows[start:start + page_size]

    return ok(
        {
            "source": source,
            "sortable": [{"key": k, "label": v} for k, v in WATCH_SORTABLE.items()],
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    )


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
    if os.path.isfile(os.path.join(config.FRONTEND_DIST, path)):
        return send_from_directory(config.FRONTEND_DIST, path)
    if os.path.isdir(config.FRONTEND_DIST):
        return send_from_directory(config.FRONTEND_DIST, "index.html")
    return fail("not found", code=404, status=404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
