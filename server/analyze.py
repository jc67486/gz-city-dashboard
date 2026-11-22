# -*- coding: utf-8 -*-
"""
广东省 21 市经济结构对比分析 —— 计算 + 出图
运行：python analyze.py
产出：out/metrics.json（结论数字）、out/fig1_*.png、fig2_*.png、fig3_*.png
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "dashboard.db")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PEARL_RIVER = ["广州市", "深圳市", "佛山市", "东莞市", "惠州市", "珠海市",
               "江门市", "中山市", "肇庆市"]


def load():
    conn = sqlite3.connect(DB)
    city = pd.read_sql("SELECT * FROM city", conn)
    trend = pd.read_sql("SELECT * FROM gdp_trend ORDER BY year", conn)
    conn.close()
    city["region"] = np.where(city["city_name"].isin(PEARL_RIVER), "珠三角", "粤东西北")
    return city, trend


def concentration(city):
    """集中度：CR4、CR2、HHI"""
    gdp = city["gdp_yi"].sort_values(ascending=False).values
    total = gdp.sum()
    share = gdp / total
    return {
        "total_gdp": float(total),
        "cr2": float(share[:2].sum() * 100),
        "cr4": float(share[:4].sum() * 100),
        "hhi": float((share ** 2).sum() * 10000),
        "top2": city.nlargest(2, "gdp_yi")["city_name"].tolist(),
    }


def region_share(city):
    g = city.groupby("region")["gdp_yi"].agg(["sum", "count"])
    g["pct"] = g["sum"] / g["sum"].sum() * 100
    g["per_capita"] = city.groupby("region").apply(
        lambda d: d["gdp_yi"].sum() * 10000 / d["pop_wan"].sum(), include_groups=False)
    return g


def disparity(city):
    """人均 GDP 差距：极差倍数、变异系数、四分位"""
    pc = city["gdp_per_capita"]
    idx_max = pc.idxmax()
    idx_min = pc.idxmin()
    return {
        "max_city": city.loc[idx_max, "city_name"],
        "max_val": float(pc[idx_max]),
        "min_city": city.loc[idx_min, "city_name"],
        "min_val": float(pc[idx_min]),
        "ratio": float(pc[idx_max] / pc[idx_min]),
        "cv": float(pc.std(ddof=1) / pc.mean() * 100),
        "q1": float(pc.quantile(0.25)),
        "median": float(pc.median()),
        "mean": float(pc.mean()),
        "q3": float(pc.quantile(0.75)),
    }


def zipf(city):
    """位序-规模：log(GDP) = a + b*log(rank)，|b| 越小越均衡"""
    d = city.sort_values("gdp_yi", ascending=False).reset_index(drop=True)
    rank = np.arange(1, len(d) + 1)
    x, y = np.log(rank), np.log(d["gdp_yi"].values)
    b, a = np.polyfit(x, y, 1)
    pred = a + b * x
    ss_res = ((y - pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    return {"slope": float(b), "intercept": float(a), "r2": float(1 - ss_res / ss_tot),
            "rank": rank, "gdp": d["gdp_yi"].values, "names": d["city_name"].tolist()}


def cagr(trend):
    first, last = trend.iloc[0], trend.iloc[-1]
    n = last["year"] - first["year"]
    g = (last["gdp_yi"] / first["gdp_yi"]) ** (1 / n) - 1
    return {"start_year": int(first["year"]), "end_year": int(last["year"]),
            "cagr": float(g * 100), "start_gdp": float(first["gdp_yi"]),
            "end_gdp": float(last["gdp_yi"])}


# ---------------- 出图 ----------------
def fig_region(rs, path):
    fig, ax = plt.subplots(figsize=(6.4, 3.2), dpi=200)
    vals = rs["pct"].values
    labels = list(rs.index)
    colors = ["#1f4e79", "#5b9bd5"]
    bars = ax.barh(labels, vals, color=colors, height=0.5)
    for b, v, s in zip(bars, vals, rs["sum"].values):
        ax.text(v + 1.2, b.get_y() + b.get_height() / 2, f"{v:.1f}%  ({s/10000:.2f} 万亿)",
                va="center", fontsize=9, color="#333")
    ax.set_xlim(0, 100)
    ax.set_xlabel("GDP 占比（%）", fontsize=9)
    ax.set_title("珠三角 vs 粤东西北：GDP 份额", fontsize=11, color="#1f4e79")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_trend(trend, cg, path):
    fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=200)
    x = trend["year"].astype(str)
    y = trend["gdp_yi"] / 10000
    ax.plot(x, y, marker="o", color="#1f4e79", linewidth=2)
    ax.fill_between(x, y, color="#1f4e79", alpha=0.12)
    for xi, yi in zip(x, y):
        ax.text(xi, yi + 0.35, f"{yi:.2f}", ha="center", fontsize=8.5, color="#333")
    ax.set_ylabel("GDP（万亿元）", fontsize=9)
    ax.set_title(f"全省 GDP 走势：{cg['start_year']}–{cg['end_year']} 年均复合增速 {cg['cagr']:.1f}%",
                 fontsize=11, color="#1f4e79")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.set_ylim(0, y.max() * 1.15)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_zipf(z, path):
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=200)
    x = np.log(z["rank"])
    y = np.log(z["gdp"])
    ax.scatter(x, y, s=22, color="#1f4e79", alpha=0.75, label="21 个地级市")
    fit = z["intercept"] + z["slope"] * x
    ax.plot(x, fit, color="#c00000", linewidth=1.6,
            label=f"拟合斜率 {z['slope']:.2f}（R²={z['r2']:.3f}）")
    for i in [0, 1, 2, len(z["rank"]) - 1]:
        ax.annotate(z["names"][i], (x[i], y[i]), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color="#444")
    ax.set_xlabel("ln(位序)", fontsize=9)
    ax.set_ylabel("ln(GDP)", fontsize=9)
    ax.set_title("位序—规模分布（斜率越平越均衡）", fontsize=11, color="#1f4e79")
    ax.legend(fontsize=8.5, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25, linestyle="--")
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_disp(city, d, path):
    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=200)
    top = city.sort_values("gdp_per_capita", ascending=True)
    colors = ["#1f4e79" if n in PEARL_RIVER else "#9dc3e6" for n in top["city_name"]]
    ax.barh(top["city_name"], top["gdp_per_capita"] / 10000, color=colors, height=0.66)
    ax.axvline(d["median"] / 10000, color="#c00000", linestyle="--", linewidth=1.2)
    ax.text(d["median"] / 10000 + 0.15, -0.4, f"中位数 {d['median']/10000:.2f} 万",
            color="#c00000", fontsize=8.5)
    ax.set_xlabel("人均 GDP（万元）", fontsize=9)
    ax.set_title(f"人均 GDP 极差 {d['ratio']:.1f} 倍：{d['max_city']} vs {d['min_city']}",
                 fontsize=11, color="#1f4e79")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    city, trend = load()
    conc = concentration(city)
    rs = region_share(city)
    d = disparity(city)
    z = zipf(city)
    cg = cagr(trend)

    fig_region(rs, os.path.join(OUT, "fig1_region.png"))
    fig_trend(trend, cg, os.path.join(OUT, "fig2_trend.png"))
    fig_zipf(z, os.path.join(OUT, "fig3_zipf.png"))
    fig_disp(city, d, os.path.join(OUT, "fig4_percapita.png"))

    metrics = {
        "concentration": conc,
        "region": {k: {"gdp": float(rs.loc[k, "sum"]), "count": int(rs.loc[k, "count"]),
                       "pct": float(rs.loc[k, "pct"]), "per_capita": float(rs.loc[k, "per_capita"])}
                   for k in rs.index},
        "disparity": d,
        "zipf": {"slope": z["slope"], "r2": z["r2"]},
        "cagr": cg,
        "city_count": int(len(city)),
    }
    with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print("=" * 66)
    print(f"样本：{len(city)} 个地级市，全省 GDP {conc['total_gdp']/10000:.2f} 万亿元")
    print(f"集中度：CR2 {conc['cr2']:.1f}%（{'+'.join(conc['top2'])}）  CR4 {conc['cr4']:.1f}%  HHI {conc['hhi']:.0f}")
    for k, v in metrics["region"].items():
        print(f"  {k}：{v['count']} 市，GDP {v['gdp']/10000:.2f} 万亿，占 {v['pct']:.1f}%，人均 {v['per_capita']/10000:.2f} 万")
    print(f"人均差距：{d['max_city']} {d['max_val']/10000:.2f} 万 vs {d['min_city']} {d['min_val']/10000:.2f} 万 = {d['ratio']:.1f} 倍")
    print(f"人均变异系数 CV = {d['cv']:.1f}%   中位数 {d['median']/10000:.2f} 万（Q1 {d['q1']/10000:.2f} / Q3 {d['q3']/10000:.2f}）")
    print(f"位序-规模：斜率 {z['slope']:.2f}，R² {z['r2']:.3f}")
    print(f"趋势：{cg['start_year']}→{cg['end_year']} CAGR {cg['cagr']:.1f}%（{cg['start_gdp']/10000:.2f} → {cg['end_gdp']/10000:.2f} 万亿）")
    print("=" * 66)
    print("图表已输出到 out/：fig1_region.png / fig2_trend.png / fig3_zipf.png / fig4_percapita.png")


if __name__ == "__main__":
    main()
