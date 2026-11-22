# -*- coding: utf-8 -*-
"""
把 6 个接口的响应导出成静态 JSON（供 Vercel / GitHub Pages 纯静态部署）
运行：python export_static.py   ->  前端 public/mock/*.json

为什么需要：Vercel 只能托管静态文件，Flask 不在那里。
导出的数据结构与接口完全一致（{code, data, msg}），前端切到静态模式后代码零改动。
"""
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "dashboard.db")
PUBLIC = os.path.join(HERE, "..", "public", "mock")

REGIONS = {
    "珠三角": ["广州市", "深圳市", "佛山市", "东莞市", "惠州市", "珠海市", "江门市", "中山市", "肇庆市"],
    "粤东": ["汕头市", "潮州市", "揭阳市", "汕尾市"],
    "粤西": ["湛江市", "茂名市", "阳江市"],
    "粤北": ["韶关市", "清远市", "梅州市", "河源市", "云浮市"],
}


def rows(cur, sql, args=()):
    return [dict(r) for r in cur.execute(sql, args).fetchall()]


def main():
    if not os.path.exists(DB):
        raise SystemExit("请先运行 python seed.py")
    os.makedirs(PUBLIC, exist_ok=True)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) overview
    ov = dict(cur.execute("""
        SELECT SUM(gdp_yi) AS gdp_yi, SUM(pop_wan) AS pop_wan, COUNT(*) AS city_cnt
        FROM city
    """).fetchone())
    year = cur.execute("SELECT MAX(year) FROM gdp_trend").fetchone()[0]
    overview = {
        "year": year,
        "gdp_yi": round(ov["gdp_yi"], 1),
        "pop_wan": round(ov["pop_wan"], 1),
        "gdp_per_capita": round(ov["gdp_yi"] * 10000 / ov["pop_wan"], 2),
        "city_cnt": ov["city_cnt"],
        "updated_at": "静态快照",
    }

    # 2) trend
    trend = {"list": [dict(r) for r in cur.execute(
        "SELECT year, gdp_yi, per_capita FROM gdp_trend ORDER BY year").fetchall()]}

    # 3) region-share
    city_rows = rows(cur, "SELECT city_name, gdp_yi FROM city")
    total = sum(r["gdp_yi"] for r in city_rows) or 1
    region = []
    for gname, cities in REGIONS.items():
        v = sum(r["gdp_yi"] for r in city_rows if r["city_name"] in cities)
        region.append({"name": gname, "value": round(v, 1), "pct": round(v / total * 100, 1)})

    # 4) city-rank（导出全部 21 个，前端按 top 参数切片）
    rank = {"list": [dict(r) for r in cur.execute(
        "SELECT city_name, gdp_yi, pop_wan, gdp_per_capita FROM city ORDER BY gdp_yi DESC").fetchall()]}

    # 5) city-map
    cmap = {"list": [
        {"name": r["city_name"], "coord": [r["lng"], r["lat"]],
         "value": round(r["gdp_yi"], 1), "per_capita": r["gdp_per_capita"]}
        for r in cur.execute(
            "SELECT city_name, lng, lat, gdp_yi, gdp_per_capita FROM city ORDER BY gdp_yi DESC"
        ).fetchall()]}

    # 6) industry
    agg = dict(cur.execute("SELECT SUM(gdp_yi) AS g, AVG(industry_rate) AS r FROM city").fetchone())
    primary = round(agg["g"] * 0.041, 1)
    secondary = round(agg["g"] * (agg["r"] / 100), 1)
    industry = {"list": [
        {"name": "第一产业", "value": primary},
        {"name": "第二产业", "value": secondary},
        {"name": "第三产业", "value": round(agg["g"] - primary - secondary, 1)},
    ]}
    conn.close()

    payloads = {
        "overview": overview, "trend": trend, "region-share": {"list": region},
        "city-rank": rank, "city-map": cmap, "industry": industry,
    }
    for name, data in payloads.items():
        path = os.path.join(PUBLIC, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"code": 0, "data": data, "msg": "static"}, f, ensure_ascii=False)
        print(f"  写出 public/mock/{name}.json  ({os.path.getsize(path) / 1024:.1f} KB)")

    print(f"\n共 6 个静态数据文件 -> {os.path.abspath(PUBLIC)}")
    print("下一步：npm run build 后用 Vercel 部署，前端会自动走静态数据")


if __name__ == "__main__":
    main()
