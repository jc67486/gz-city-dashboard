# -*- coding: utf-8 -*-
"""
广州城市数据可视化大屏 —— 后端接口（Flask + SQLite）
统一响应结构 {code, data, msg}；高频接口带 60s 内存缓存；参数化查询防注入
运行：python app.py  ->  http://127.0.0.1:5001
"""
import os
import time
import sqlite3
from functools import wraps, lru_cache

from flask import Flask, jsonify, request
from flask_cors import CORS

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "dashboard.db")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

CACHE_TTL = 60
_cache = {}


def ok(data, msg="ok"):
    return jsonify({"code": 0, "data": data, "msg": msg})


def err(msg="参数错误", code=400):
    return jsonify({"code": code, "data": None, "msg": msg}), 400


def cached(ttl=CACHE_TTL):
    """简易内存缓存：同一 worker 内命中直接返回"""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = request.full_path
            now = time.time()
            if key in _cache and now - _cache[key][0] < ttl:
                payload, = _cache[key][1:]
                return payload
            payload = fn(*args, **kwargs)
            _cache[key] = (now, payload)
            return payload
        return wrapper
    return deco


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


@app.get("/api/health")
def health():
    return ok({"status": "up", "ts": int(time.time())})


@app.get("/api/overview")
@cached(60)
def overview():
    """顶部 KPI：全省 GDP、常住人口、人均 GDP、地市数量"""
    with conn() as c:
        row = c.execute("""
            SELECT SUM(gdp_yi) AS gdp, SUM(pop_wan) AS pop,
                   COUNT(*) AS city_cnt, MAX(industry_rate) AS top_industry
            FROM city
        """).fetchone()
        year = c.execute("SELECT MAX(year) FROM gdp_trend").fetchone()[0]
    gdp, pop = row["gdp"], row["pop"]
    return ok({
        "year": year,
        "gdp_yi": round(gdp, 1),
        "pop_wan": round(pop, 1),
        "gdp_per_capita": round(gdp * 10000 / pop, 2),
        "city_cnt": row["city_cnt"],
        "updated_at": time.strftime("%H:%M:%S"),
    })


@app.get("/api/trend")
@cached(60)
def trend():
    """年度趋势：近 N 年 GDP 与人均 GDP"""
    rng = request.args.get("range", "6")
    if not rng.isdigit() or not (1 <= int(rng) <= 10):
        return err("range 参数需为 1-10 的整数")
    limit = int(rng)
    with conn() as c:
        rows = c.execute(
            "SELECT year, gdp_yi, per_capita FROM gdp_trend ORDER BY year DESC LIMIT ?", (limit,)
        ).fetchall()
    data = [dict(r) for r in rows][::-1]
    return ok({"list": data})


@app.get("/api/region-share")
@cached(60)
def region_share():
    """地区占比：按 GDP 分组（珠三角/粤东/粤西/粤北）"""
    groups = {
        "珠三角": ["广州市", "深圳市", "佛山市", "东莞市", "惠州市", "珠海市", "江门市",
                "中山市", "肇庆市"],
        "粤东": ["汕头市", "潮州市", "揭阳市", "汕尾市"],
        "粤西": ["湛江市", "茂名市", "阳江市"],
        "粤北": ["韶关市", "清远市", "梅州市", "河源市", "云浮市"],
    }
    with conn() as c:
        rows = c.execute("SELECT city_name, gdp_yi FROM city").fetchall()
    total = sum(r["gdp_yi"] for r in rows) or 1
    acc = []
    for gname, cities in groups.items():
        v = sum(r["gdp_yi"] for r in rows if r["city_name"] in cities)
        acc.append({"name": gname, "value": round(v, 1), "pct": round(v / total * 100, 1)})
    return ok({"list": acc})


@app.get("/api/city-rank")
@cached(60)
def city_rank():
    """Top 排行：按 GDP 降序"""
    top = request.args.get("top", "10")
    if not top.isdigit() or not (1 <= int(top) <= 21):
        return err("top 参数需为 1-21 的整数")
    with conn() as c:
        rows = c.execute(
            "SELECT city_name, gdp_yi, pop_wan, gdp_per_capita FROM city "
            "ORDER BY gdp_yi DESC LIMIT ?", (int(top),)
        ).fetchall()
    return ok({"list": [dict(r) for r in rows]})


@app.get("/api/city-map")
@cached(60)
def city_map():
    """地图散点：城市坐标 + 指标值"""
    with conn() as c:
        rows = c.execute(
            "SELECT city_name, lng, lat, gdp_yi, gdp_per_capita FROM city ORDER BY gdp_yi DESC"
        ).fetchall()
    data = [{"name": r["city_name"], "coord": [r["lng"], r["lat"]],
             "value": round(r["gdp_yi"], 1), "per_capita": r["gdp_per_capita"]} for r in rows]
    return ok({"list": data})


@app.get("/api/industry")
@cached(60)
def industry():
    """产业结构（示意，按城市 GDP 加权生成占比）"""
    with conn() as c:
        rows = c.execute("SELECT SUM(gdp_yi) AS g, AVG(industry_rate) AS r FROM city").fetchone()
    g, r = rows["g"], rows["r"]
    primary = round(g * 0.041, 1)
    secondary = round(g * (r / 100), 1)
    tertiary = round(g - primary - secondary, 1)
    return ok({"list": [
        {"name": "第一产业", "value": primary},
        {"name": "第二产业", "value": secondary},
        {"name": "第三产业", "value": tertiary},
    ]})


@app.errorhandler(404)
def not_found(_):
    return jsonify({"code": 404, "data": None, "msg": "接口不存在"}), 404


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        raise SystemExit("请先运行 python seed.py 生成数据库")
    app.run(host="127.0.0.1", port=5001, debug=False)
