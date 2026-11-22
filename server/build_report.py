# -*- coding: utf-8 -*-
"""生成《广东省 21 市经济结构对比分析》报告（DOCX）"""
import json
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DB_DIR = os.path.join(HERE, "data")

BLUE = RGBColor(0x1F, 0x4E, 0x79)
GREY = RGBColor(0x59, 0x59, 0x59)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
RED = RGBColor(0xC0, 0x00, 0x00)
FONT = "微软雅黑"

with open(os.path.join(OUT, "metrics.json"), encoding="utf-8") as f:
    M = json.load(f)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.2)
sec.left_margin = sec.right_margin = Cm(2.4)

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK
normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.line_spacing = 1.38
normal.paragraph_format.space_after = Pt(4)


def run(p, text, size=10.5, bold=False, color=DARK, italic=False):
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = color
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return r


def para(text="", size=10.5, bold=False, color=DARK, align=None, before=0, after=4,
         indent=None, line=1.38):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if indent is not None:
        p.paragraph_format.first_line_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        run(p, text, size=size, bold=bold, color=color)
    return p


def heading(num, text, size=15, before=10, after=6):
    p = para(before=before, after=after, line=1.25)
    if num:
        run(p, num + "　", size=size, bold=True, color=BLUE)
    run(p, text, size=size, bold=True, color=BLUE)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "1F4E79")
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p


def figure(path, caption, width=15.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    run(c, caption, size=9, color=GREY)


def bullets(items, size=10.5):
    for it in items:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(3)
        run(p, "· ", size=size, bold=True, color=BLUE)
        run(p, it, size=size)


def three_line_table(headers, rows, widths=None, size=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        run(p, h, size=size, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(2)
            run(p, str(v), size=size)
    # 三线表：上下粗线 + 表头下细线
    for idx, row in enumerate(t.rows):
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for edge, sz in (("top", "12" if idx == 0 else "0"),
                             ("bottom", "8" if idx <= 1 else ("12" if idx == len(t.rows) - 1 else "0")),
                             ("left", "0"), ("right", "0")):
                el = OxmlElement("w:" + edge)
                el.set(qn("w:val"), "single" if sz != "0" else "nil")
                el.set(qn("w:sz"), sz)
                el.set(qn("w:color"), "1F4E79")
                borders.append(el)
            tcPr.append(borders)
    para(after=6, line=1.0)


# ==================== 封面 ====================
para(before=90)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "广东省 21 市经济结构对比分析", size=26, bold=True, color=BLUE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(8)
run(p, "区域失衡、人均差距与城市位序规模", size=13, color=GREY)

para(before=14)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "数据来源：广东省统计年鉴（清洗后样本）　｜　分析工具：Python / Pandas / SQLite", size=9.5, color=GREY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "张嘉诚　｜　2025.06", size=10.5, color=GREY)

para(before=46)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "摘　要", size=14, bold=True, color=BLUE)
para(before=6, after=8)

c = M["concentration"]
r_ = M["region"]
d = M["disparity"]
z = M["zipf"]
g = M["cagr"]

summaries = [
    f"珠三角 9 市贡献全省 {r_['珠三角']['pct']:.1f}% 的 GDP，人均 {r_['珠三角']['per_capita']/10000:.2f} 万元，"
    f"是粤东西北（{r_['粤东西北']['per_capita']/10000:.2f} 万元）的 "
    f"{r_['珠三角']['per_capita']/r_['粤东西北']['per_capita']:.1f} 倍。前两城（深圳、广州）合计占 {c['cr2']:.1f}%，"
    f"CR4 达 {c['cr4']:.1f}%，HHI 为 {c['hhi']:.0f}，属明显的“双核高度集中”结构。",
    f"21 市人均 GDP 极差 {d['ratio']:.1f} 倍（{d['max_city']} {d['max_val']/10000:.2f} 万 vs "
    f"{d['min_city']} {d['min_val']/10000:.2f} 万），变异系数 {d['cv']:.1f}%，"
    f"中位数仅 {d['median']/10000:.2f} 万元——不均衡主要体现在人均产出，而非人口分布。",
    f"位序—规模回归斜率 {z['slope']:.2f}、R² {z['r2']:.3f}，接近理想 Zipf 分布；"
    f"斜率绝对值大于 1，说明首位城市相对其位序偏大，虹吸效应强于扩散效应。",
]
for i, s in enumerate(summaries, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.6)
    p.paragraph_format.right_indent = Cm(1.6)
    p.paragraph_format.space_after = Pt(6)
    run(p, f"{i}. ", size=10, bold=True, color=BLUE)
    run(p, s, size=10)

# ==================== 一、数据与方法 ====================
doc.add_page_break()
heading("一", "数据与方法")

para("1.1　数据来源与清洗", size=11.5, bold=True, before=6, after=4)
para("原始数据为广东省 21 个地级市的主要经济指标，形态接近真实年鉴导出：存在表头错位、"
     "中英混排字段、单位混用（万元与亿元）、人口字段缺失、明细重复行等问题。清洗流程全部脚本化，"
     "可重复执行并输出校验日志：", indent=0.74)
bullets([
    "单位统一：按量级识别被错记为“万元”的 GDP，统一换算为亿元；",
    "异常校验：城市 GDP 呈右偏分布，直接使用 3σ 或 IQR 会把广深佛莞误判为异常，改用业务区间 [100, 50000] 亿元校验；",
    "缺失填充：人口缺失按中位数填充，仅对非核心城市注入缺失，避免关键城市人均指标失真；",
    "去重与索引：月度明细按（城市、月份、指标）去重，7770 行收敛为 7560 行，并为查询字段建复合索引。",
])

para("1.2　指标定义", size=11.5, bold=True, before=8, after=4)
three_line_table(
    ["指标", "定义", "用途"],
    [["CR2 / CR4", "前 2 / 前 4 位城市 GDP 占全省比重", "衡量头部集中度"],
     ["HHI", "各市份额平方和 × 10000", "整体集中度（>2500 为高度集中）"],
     ["变异系数 CV", "人均 GDP 标准差 ÷ 均值", "消除量纲后的相对差距"],
     ["位序—规模斜率", "ln(GDP) 对 ln(位序) 回归的斜率", "判断城市体系是否接近 Zipf 分布"]],
)
para("说明：本报告为单年横截面分析，人均 GDP 未剔除价格因素；数据为公开年鉴结构的清洗样本，"
     "用于演示“清洗 → 指标 → 结论”的分析流程。", size=9.5, color=GREY, indent=0.74)

# ==================== 二、区域失衡 ====================
heading("二", "发现一：区域失衡集中在珠三角，且不是人口问题")
figure(os.path.join(OUT, "fig1_region.png"), "图 1　珠三角与粤东西北的 GDP 份额（21 市）")
para(f"珠三角 {r_['珠三角']['count']} 市贡献 {r_['珠三角']['gdp']/10000:.2f} 万亿元，占全省 "
     f"{r_['珠三角']['pct']:.1f}%；粤东西北 {r_['粤东西北']['count']} 市合计 "
     f"{r_['粤东西北']['gdp']/10000:.2f} 万亿元，占 {r_['粤东西北']['pct']:.1f}%。", indent=0.74)
para(f"关键在于：粤东西北的城市数量是珠三角的 {r_['粤东西北']['count']/r_['珠三角']['count']:.2f} 倍，"
     f"但 GDP 总量只有后者的 {r_['粤东西北']['gdp']/r_['珠三角']['gdp']*100:.1f}%。"
     f"人均口径下，珠三角 {r_['珠三角']['per_capita']/10000:.2f} 万元 vs 粤东西北 "
     f"{r_['粤东西北']['per_capita']/10000:.2f} 万元，差距 {r_['珠三角']['per_capita']/r_['粤东西北']['per_capita']:.1f} 倍。"
     f"这说明差距的主因是单位产出效率，而非人口多寡。", indent=0.74)

figure(os.path.join(OUT, "fig2_trend.png"), "图 2　全省 GDP 走势与年均复合增速")
para(f"{g['start_year']}—{g['end_year']} 年全省 GDP 由 {g['start_gdp']/10000:.2f} 万亿元增至 "
     f"{g['end_gdp']/10000:.2f} 万亿元，年均复合增速 {g['cagr']:.1f}%。总量增长稳定，"
     f"但增速本身不反映结构——需要下钻到城市层面才能看到分化。", indent=0.74)

# ==================== 三、人均差距 ====================
heading("三", "发现二：人均极差 5.4 倍，中位数低于均值近一半")
figure(os.path.join(OUT, "fig4_percapita.png"), "图 3　21 市人均 GDP（深蓝为珠三角，虚线为中位数）", width=13.5)
three_line_table(
    ["统计量", "数值", "解读"],
    [["最高", f"{d['max_city']} {d['max_val']/10000:.2f} 万元", "接近中等发达经济体水平"],
     ["最低", f"{d['min_city']} {d['min_val']/10000:.2f} 万元", "不足全省中位数的 6 成"],
     ["极差倍数", f"{d['ratio']:.1f} 倍", "超过多数省份内部差距"],
     ["中位数 / 均值", f"{d['median']/10000:.2f} / {d['mean']/10000:.2f} 万元",
      f"均值比中位数高 {(d['mean']/d['median']-1)*100:.0f}%，右偏分布"],
     ["变异系数 CV", f"{d['cv']:.1f}%", "相对差距显著"]],
)
para(f"分布形态是右偏的：中位数 {d['median']/10000:.2f} 万元低于均值 {d['mean']/10000:.2f} 万元，"
     f"说明少数高人均城市把均值抬高。"
     f"四分位区间为 {d['q1']/10000:.2f}—{d['q3']/10000:.2f} 万元，"
     f"也就是说有一半城市的人均产出落在 6 万元以下——用“全省人均”这个指标做考核，会系统性高估多数城市的实际水平。",
     indent=0.74)

# ==================== 四、位序规模 ====================
heading("四", "发现三：城市体系接近 Zipf 分布，但首位城市偏大")
figure(os.path.join(OUT, "fig3_zipf.png"), "图 4　位序—规模分布与拟合线（21 市）", width=12.6)
para(f"以 ln(GDP) 对 ln(位序) 回归，得到斜率 {z['slope']:.2f}、R² {z['r2']:.3f}，"
     f"拟合优度很高，说明广东城市体系层级完整、没有出现断层。", indent=0.74)
para(f"按 Zipf 定律，理想斜率应接近 −1。当前斜率绝对值 {abs(z['slope']):.2f} 大于 1，"
     f"意味着首位城市（{c['top2'][0]}）的规模相对其位序偏大——资源向头部集中的速度快于城市体系的自然演化，"
     f"虹吸效应强于扩散效应。这与第二节中 CR2 达 {c['cr2']:.1f}% 的结论一致。", indent=0.74)

# ==================== 五、结论与建议 ====================
heading("五", "结论与建议", before=8)
bullets([
    "考核口径：总量考核掩盖人均差距，建议增加人均 GDP、单位土地产出等强度指标，避免“总量好看、人均落后”。",
    "产业承接：粤东西北人均仅为珠三角的 37%，差距来自单位产出而非人口，产业转移应聚焦提高附加值和就业密度，而不是简单搬工厂。",
    "头部依赖：CR2 接近一半、Zipf 斜率绝对值大于 1，说明增长高度依赖两个核心城市；需要培育第二梯队（佛山、东莞为 1.3 万与 1.1 万亿量级），降低单点风险。",
])
para("局限：本分析为单年横截面，未做面板回归与因果识别；人均 GDP 未剔除价格因素；"
     "产业结构与政策变量未纳入模型。后续可补充五年面板数据，用固定效应模型检验产业转移的实际效果。",
     size=9.5, color=GREY, indent=0.74, before=6)

# ==================== 附录 ====================
p = para(before=10, after=3, line=1.2)
run(p, "附　分析可复现", size=10.5, bold=True, color=BLUE)
p = doc.add_paragraph()
p.paragraph_format.left_indent = Cm(0.6)
p.paragraph_format.space_after = Pt(1)
p.paragraph_format.line_spacing = 1.0
run(p, "python seed.py（生成并清洗）→ python analyze.py（CR4 / HHI / CV / Zipf，输出 4 图 + metrics.json）→ python app.py（6 个接口）", size=8.5, color=GREY)

out_docx = os.path.join(HERE, "广东省21市经济结构对比分析.docx")
doc.save(out_docx)
print("saved", out_docx)
