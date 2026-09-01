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


def ok(data=None, message="ok"):
    """统一成功响应。"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message, code=1, status=200):
    """统一失败响应。"""
    return jsonify({"code": code, "message": message, "data": None}), status


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
    if not (code.isdigit() and len(code) == 6):
        return fail("股票代码格式不正确，应为 6 位数字", code=400, status=400)
    try:
        data, source = service.get_quote(code)
    except Exception:  # 双数据源均失败
        return fail("行情服务暂时不可用，请稍后重试", code=503, status=503)
    if data is None:
        return fail("未查询到该股票行情，请检查代码是否正确", code=404)
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
    data = service.get_batch_quotes(code_list)
    return ok(data)


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
