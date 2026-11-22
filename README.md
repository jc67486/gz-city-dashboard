# 广东省城市运行监测大屏

> Vue 3 + Vite + ECharts 5 + Flask + Pandas ｜ 21 个地级市 × 72 个月的指标看板
> 在线演示：【部署后把 Vercel 地址填这里】

![大屏主视图](shot/screen1.png)

基于广东省统计年鉴公开数据的可视化大屏：Pandas 清洗 → SQLite 入库 → Flask 提供 6 个 REST 接口 → Vue 3 + ECharts 渲染 6 类图表，支持 1920×1080 等比自适应、30s 轮询与失败降级。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3（组合式 API）、Vite 5、ECharts 5（按需引入）、Axios |
| 后端 | Flask 3、SQLite（可切 MySQL）、Gunicorn 部署 |
| 数据 | Pandas / NumPy 清洗、SQLAlchemy 分批写入 |

## 目录结构

```
big-screen/
├── server/
│   ├── seed.py            # 生成脏数据 → Pandas 清洗 → 入库 + 建索引
│   ├── app.py             # Flask 接口（统一 code/data/msg，60s 内存缓存）
│   └── data/              # raw_guangdong_stat.xlsx / fact_month.csv / dashboard.db
├── src/
│   ├── api/index.js       # Axios 封装 + 错误码映射
│   ├── hooks/useChart.js  # 图表实例统一管理（创建 / resize / 销毁）
│   ├── components/PanelBox.vue
│   └── App.vue            # 1920×1080 设计稿 + transform: scale 自适应
└── public/guangdong.json  # 广东 GeoJSON
```

## 快速开始

```bash
# 1. 后端
cd server
pip install flask flask-cors pandas numpy openpyxl
python seed.py          # 生成数据并打印清洗日志
python app.py           # http://127.0.0.1:5001

# 2. 前端
cd ..
npm install
npm run dev             # http://127.0.0.1:5173
```

## 接口

| 接口 | 说明 |
|---|---|
| GET /api/overview | 顶部 KPI（GDP / 人口 / 人均 / 地市数） |
| GET /api/trend?range=6 | 年度趋势 |
| GET /api/region-share | 珠三角 / 粤东 / 粤西 / 粤北 占比 |
| GET /api/city-rank?top=10 | GDP 排行 |
| GET /api/city-map | 城市坐标 + 指标（地图散点） |
| GET /api/industry | 三次产业占比 |

## 数据清洗做了什么

原始数据被刻意做脏（模拟真实年鉴导出）：

- **表头错位 / 中英混排字段** → rename 统一为英文列名
- **单位混用（万元 / 亿元）** → 按量级判断后统一为亿元（修正 4 行）
- **人口字段缺失** → 中位数填充（3 处）
- **异常值** → 城市 GDP 为右偏分布，IQR 会把广深佛莞误判为异常，改用业务区间 [100, 50000] 亿元校验
- **明细重复行** → 按 (城市, 月份, 指标) 去重，7770 → 7560 行
- **索引** → (city_name, month)、(indicator, year)，EXPLAIN 验证命中

## 分析报告

`ash
cd server
python analyze.py       # CR4 / HHI / 变异系数 / 位序-规模回归，输出 4 张图与 metrics.json
python build_report.py  # 生成《广东省 21 市经济结构对比分析》DOCX（5 页）
`

报告结论：
- 珠三角 9 市占全省 GDP 81.5%，人均 13.79 万元，是粤东西北（5.19 万）的 2.7 倍；CR2 48.0%、CR4 66.3%、HHI 1410
- 人均 GDP 极差 5.4 倍（深圳 19.45 万 vs 梅州 3.63 万），变异系数 54.2%，中位数 6.08 万低于均值 7.91 万（右偏）
- 位序—规模回归斜率 -1.21、R² 0.969，接近 Zipf 分布；斜率绝对值 >1 说明首位城市偏大、虹吸强于扩散

## 测试

`ash
cd server
python -m pytest tests -q --cov=app --cov-report=term-missing   # 13 passed, 97%
`

## 实测数据

- 接口响应：平均 45 ms（首次冷启动 181 ms，60s 缓存命中后 35–56 ms）
- 构建产物：826 KB，626 个模块；echarts 分包 gzip 后 210 KB
- 数据量：21 个地市 + 7560 行月度明细 + 6 年趋势

## 踩坑记录

1. **ECharts 地图散点空白**：`effectScatter` 在 `geo` 坐标系下 value 必须是 `[lng, lat, 数值]`，传 `{coord, value}` 不渲染。
2. **缩放后文字模糊**：`transform: scale` 只缩放 CSS 尺寸，canvas 按 CSS 像素绘制，需用 `devicePixelRatio × 2` 初始化实例再 `resize()`。
3. **dev server 被外部进程拖死**：把浏览器 user-data-dir 放进项目目录后，Vite 的 watcher 会去 watch 浏览器缓存文件并报 EBUSY，需在 `server.watch.ignored` 里排除。
