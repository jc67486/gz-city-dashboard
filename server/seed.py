# -*- coding: utf-8 -*-
"""
广州城市数据可视化大屏 —— 数据准备与清洗脚本
流程：生成"脏"原始数据 -> Pandas 清洗 -> SQLite 入库（建索引） -> 打印清洗日志
运行：python seed.py
产出：data/raw_guangdong_stat.xlsx（汇总）、data/fact_month.csv（月度明细）、data/dashboard.db
"""
import os
import random
import sqlite3

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
RAW_XLSX = os.path.join(DATA_DIR, "raw_guangdong_stat.xlsx")
RAW_CSV = os.path.join(DATA_DIR, "fact_month.csv")
DB_PATH = os.path.join(DATA_DIR, "dashboard.db")

# 广东省 21 个地级市：名称、中心经纬度、2023 年 GDP（亿元）、常住人口（万人）
CITIES = [
    ("广州市", 113.2644, 23.1291, 30355.7, 1882.7),
    ("深圳市", 114.0579, 22.5431, 34606.4, 1779.0),
    ("佛山市", 113.1220, 23.0288, 13276.1, 961.3),
    ("东莞市", 113.7518, 23.0207, 11438.1, 1046.7),
    ("惠州市", 114.4162, 23.1115, 5639.4, 607.0),
    ("珠海市", 113.5767, 22.2707, 4233.2, 249.0),
    ("江门市", 113.0819, 22.5787, 4022.5, 483.5),
    ("茂名市", 110.9255, 21.6629, 4000.1, 623.5),
    ("中山市", 113.3926, 22.5176, 3850.6, 447.4),
    ("湛江市", 110.3594, 21.2707, 3793.6, 703.1),
    ("汕头市", 116.6822, 23.3535, 3158.3, 555.2),
    ("肇庆市", 112.4653, 23.0479, 2830.5, 415.0),
    ("揭阳市", 116.3728, 23.5497, 2300.5, 558.6),
    ("清远市", 113.0560, 23.6817, 2050.4, 397.0),
    ("韶关市", 113.5972, 24.8104, 1564.2, 285.6),
    ("阳江市", 111.9822, 21.8580, 1600.3, 262.3),
    ("梅州市", 116.1222, 24.2886, 1400.6, 386.2),
    ("潮州市", 116.6323, 23.6617, 1370.4, 257.5),
    ("河源市", 114.6978, 23.7463, 1300.2, 284.4),
    ("汕尾市", 115.3753, 22.7863, 1301.5, 266.2),
    ("云浮市", 112.0444, 22.9298, 1150.3, 239.6),
]

YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
GROWTH = {2019: 0.78, 2020: 0.80, 2021: 0.90, 2022: 0.95, 2023: 1.00, 2024: 1.05}

# 月度明细指标（长表：城市 × 月份 × 指标）
INDICATORS = ["GDP_ABS", "INDUSTRY_ADD", "INVEST_FIXED", "RETAIL_SALE", "EXPORT_IMPORT"]


def make_dirty_raw():
    """造两份"脏"原始数据"""
    rng = random.Random(2025)
    # ---------- 1. 汇总表（Excel，两个 sheet，表头带说明行） ----------
    col_names = ["City", "城市", "经度lng", "纬度lat", "GDP(亿元)", "pop 万人", "工业增加值占比"]
    core = {"广州市", "深圳市", "佛山市", "东莞市"}   # 核心城市不注入缺失，避免人均指标失真
    rows = []
    for name, lng, lat, gdp, pop in CITIES:
        unit_broken = rng.random() < 0.18
        gdp_cell = gdp * 10000 if unit_broken else gdp    # 约 18% 单位错成"万元"
        pop_cell = None if (name not in core and rng.random() < 0.18) else pop   # 非核心城市约 18% 缺失
        rows.append([name[:2], name, lng, lat, gdp_cell, pop_cell, round(rng.uniform(28, 42), 1)])
    df_raw = pd.DataFrame(rows, columns=col_names)

    trend_rows = []
    for y in YEARS:
        base = sum(c[3] for c in CITIES)
        gdp = base * GROWTH[y] * rng.uniform(0.995, 1.005)
        trend_rows.append([str(y), f"{gdp:,.1f}", round(gdp / 12656.8, 2)])
    df_trend = pd.DataFrame(trend_rows, columns=["year", "GDP(亿元)", "人均GDP(万元)"])

    with pd.ExcelWriter(RAW_XLSX, engine="openpyxl") as writer:
        pd.DataFrame({"备注": ["广东省统计年鉴（数据整理中，单位待核对）"]}).to_excel(
            writer, sheet_name="说明", index=False)
        df_raw.to_excel(writer, sheet_name="地市主要指标", index=False)
        df_trend.to_excel(writer, sheet_name="年度趋势", index=False)

    # ---------- 2. 月度明细（CSV，21 市 × 72 月 × 5 指标 = 7560 行，再灌脏数据） ----------
    detail = []
    for name, _, _, gdp23, pop in CITIES:
        for y in YEARS:
            for m in range(1, 13):
                base = gdp23 * GROWTH[y] / 12 * rng.uniform(0.82, 1.18)
                detail.append([name, f"{y}-{m:02d}", "GDP_ABS", f"{base:,.2f}"])
                detail.append([name, f"{y}-{m:02d}", "INDUSTRY_ADD", f"{base * 0.33:,.2f}"])
                detail.append([name, f"{y}-{m:02d}", "INVEST_FIXED", f"{base * 0.55:,.2f}"])
                detail.append([name, f"{y}-{m:02d}", "RETAIL_SALE", f"{base * 0.41:,.2f}"])
                detail.append([name, f"{y}-{m:02d}", "EXPORT_IMPORT", f"{base * 0.72:,.2f}"])
        # 每市再灌 10 行完全重复的记录（模拟导出重复）
        detail.extend([detail[-5] for _ in range(10)])

    df_detail = pd.DataFrame(detail, columns=["city_name", "month", "indicator", "value"])
    df_detail.to_csv(RAW_CSV, index=False, encoding="utf-8-sig")
    print(f"[生成] 汇总表 -> {RAW_XLSX}（{len(df_raw)} 行，含单位错乱/缺失）")
    print(f"[生成] 月度明细 -> {RAW_CSV}（{len(df_detail)} 行，含千分位字符串/重复行）")


def clean():
    """Pandas 清洗：表头对齐、单位统一、缺失填充、IQR 截断异常值、去重"""
    # ---------- 汇总表 ----------
    df = pd.read_excel(RAW_XLSX, sheet_name="地市主要指标")
    print(f"[读取] 地市主要指标：{len(df)} 行 {len(df.columns)} 列")
    df = df.rename(columns={
        "City": "city_short", "城市": "city_name", "经度lng": "lng", "纬度lat": "lat",
        "GDP(亿元)": "gdp_raw", "pop 万人": "pop_wan", "工业增加值占比": "industry_rate",
    })
    df["gdp_yi"] = np.where(df["gdp_raw"] > 100_000, df["gdp_raw"] / 10000, df["gdp_raw"])
    print(f"[单位统一] 修正万元口径 {int((df['gdp_raw'] > 100_000).sum())} 行")

    # 城市 GDP 为右偏分布，IQR 会把广深佛莞判成异常，改用业务取值区间校验
    LO, HI = 100.0, 50_000.0
    bad = (df["gdp_yi"] < LO) | (df["gdp_yi"] > HI)
    print(f"[异常值] 按业务区间 [{LO:.0f}, {HI:.0f}] 亿元校验，命中 {int(bad.sum())} 行 -> 置空后按中位数回填")
    df.loc[bad, "gdp_yi"] = np.nan

    miss_gdp = int(df["gdp_yi"].isna().sum())
    miss_pop = int(df["pop_wan"].isna().sum())
    df["gdp_yi"] = df["gdp_yi"].fillna(df["gdp_yi"].median())
    df["pop_wan"] = df["pop_wan"].fillna(df["pop_wan"].median())
    print(f"[缺失值] GDP 缺失 {miss_gdp} 处、人口缺失 {miss_pop} 处，按中位数填充")

    df["gdp_per_capita"] = (df["gdp_yi"] * 10000 / df["pop_wan"]).round(2)
    df["industry_rate"] = df["industry_rate"].round(1)
    df_clean = df[["city_name", "lng", "lat", "gdp_yi", "pop_wan",
                   "gdp_per_capita", "industry_rate"]].copy()
    print(f"[汇总表] 清洗后 {len(df_clean)} 行")

    # ---------- 月度明细 ----------
    d = pd.read_csv(RAW_CSV)
    n0 = len(d)
    d["value"] = d["value"].astype(str).str.replace(",", "").astype(float)
    d = d.drop_duplicates(subset=["city_name", "month", "indicator"], keep="first")
    n_dup = n0 - len(d)
    d = d[d["value"] > 0]
    d["year"] = d["month"].str.slice(0, 4).astype(int)
    print(f"[明细清洗] {n0} 行 -> 去重 {n_dup} 行、剔除异常 {n0 - n_dup - len(d)} 行，剩余 {len(d)} 行")

    trend = pd.read_excel(RAW_XLSX, sheet_name="年度趋势")
    trend["year"] = trend["year"].astype(int)
    trend["gdp_yi"] = trend["GDP(亿元)"].astype(str).str.replace(",", "").astype(float)
    trend = trend[["year", "gdp_yi", "人均GDP(万元)"]].rename(columns={"人均GDP(万元)": "per_capita"})
    return df_clean, d, trend


def to_sqlite(df_clean, detail, trend):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE city(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL, lng REAL, lat REAL,
        gdp_yi REAL, pop_wan REAL, gdp_per_capita REAL, industry_rate REAL)""")
    cur.execute("""CREATE TABLE fact_month(
        city_name TEXT, month TEXT, indicator TEXT, value REAL, year INTEGER)""")
    cur.execute("""CREATE TABLE gdp_trend(year INTEGER PRIMARY KEY, gdp_yi REAL, per_capita REAL)""")

    df_clean.to_sql("city", conn, if_exists="append", index=False, chunksize=1000)
    detail.to_sql("fact_month", conn, if_exists="append", index=False,
                  chunksize=1000, method="multi")
    trend.to_sql("gdp_trend", conn, if_exists="append", index=False)

    cur.execute("CREATE INDEX idx_city_name ON city(city_name)")
    cur.execute("CREATE INDEX idx_city_gdp ON city(gdp_yi DESC)")
    cur.execute("CREATE INDEX idx_fact_month ON fact_month(city_name, month)")
    cur.execute("CREATE INDEX idx_fact_ind ON fact_month(indicator, year)")
    conn.commit()

    n_city = cur.execute("SELECT COUNT(*) FROM city").fetchone()[0]
    n_fact = cur.execute("SELECT COUNT(*) FROM fact_month").fetchone()[0]
    plan = cur.execute(
        "EXPLAIN QUERY PLAN SELECT city_name, SUM(value) FROM fact_month "
        "WHERE indicator='GDP_ABS' AND year=2024 GROUP BY city_name").fetchall()
    conn.close()
    print(f"[入库] city {n_city} 行 / fact_month {n_fact} 行 / gdp_trend {len(trend)} 行")
    print(f"[索引验证] {plan}")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    make_dirty_raw()
    c_df, f_df, t_df = clean()
    to_sqlite(c_df, f_df, t_df)
    print("[完成] python app.py 启动接口服务")
