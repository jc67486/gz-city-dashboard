<template>
  <div class="viewport">
    <div class="screen" :style="{ transform: `scale(${scale})` }">
      <!-- 顶部 -->
      <header class="topbar">
        <div class="topbar__left">
          <span class="dot"></span>
          <span class="topbar__meta">数据来源：广东省统计年鉴 · 已清洗入库</span>
        </div>
        <h1 class="topbar__title">广东省城市运行监测大屏</h1>
        <div class="topbar__right">
          <span class="clock">{{ clock }}</span>
          <span class="status" :class="{ 'status--warn': stale }">
            {{ stale ? '数据更新失败，展示上次结果' : `数据更新于 ${updateTime}` }}
          </span>
        </div>
      </header>

      <!-- 主体 -->
      <main class="grid">
        <!-- 左列 -->
        <div class="col">
          <div class="cell cell--h44">
            <PanelBox title="年度 GDP 趋势" sub="2019–2024">
              <div ref="trendEl" class="chart"></div>
            </PanelBox>
          </div>
          <div class="cell cell--h56">
            <PanelBox title="产业结构" sub="三次产业占比">
              <div ref="industryEl" class="chart"></div>
            </PanelBox>
          </div>
        </div>

        <!-- 中列 -->
        <div class="col">
          <div class="kpis">
            <div v-for="k in kpiList" :key="k.label" class="kpi">
              <div class="kpi__label">{{ k.label }}</div>
              <div class="kpi__value">
                <span class="num">{{ k.value }}</span>
                <span class="unit">{{ k.unit }}</span>
              </div>
              <div class="kpi__foot">{{ k.foot }}</div>
            </div>
          </div>
          <div class="cell map-cell">
            <PanelBox title="地市经济热度" sub="21 个地级市 · 单位：亿元">
              <div ref="mapEl" class="chart"></div>
            </PanelBox>
          </div>
        </div>

        <!-- 右列 -->
        <div class="col">
          <div class="cell cell--h52">
            <PanelBox title="GDP 十强城市" sub="Top 10">
              <div ref="rankEl" class="chart"></div>
            </PanelBox>
          </div>
          <div class="cell cell--h48">
            <PanelBox title="区域经济占比" sub="珠三角 / 粤东 / 粤西 / 粤北">
              <div ref="regionEl" class="chart"></div>
            </PanelBox>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PanelBox from './components/PanelBox.vue'
import { useChart, echarts } from './hooks/useChart'
import {
  getOverview, getTrend, getRegionShare, getCityRank, getCityMap, getIndustry
} from './api'

/* ---------------- 自适应：1920×1080 设计稿等比缩放 ---------------- */
const DESIGN_W = 1920
const DESIGN_H = 1080
const scale = ref(1)
const fit = () => {
  scale.value = Math.min(window.innerWidth / DESIGN_W, window.innerHeight / DESIGN_H)
}
const onResize = () => fit()

/* ---------------- 数据 ---------------- */
const overview = ref(null)
const trendList = ref([])
const industryList = ref([])
const regionList = ref([])
const rankList = ref([])
const mapList = ref([])
const updateTime = ref('--:--:--')
const stale = ref(false)
const clock = ref('')

const kpiList = computed(() => {
  const o = overview.value
  if (!o) return []
  return [
    { label: `${o.year} 年全省 GDP`, value: (o.gdp_yi / 10000).toFixed(2), unit: '万亿元', foot: '21 个地级市合计' },
    { label: '常住人口', value: (o.pop_wan / 10000).toFixed(2), unit: '亿人', foot: '地市口径汇总' },
    { label: '人均 GDP', value: (o.gdp_per_capita / 10000).toFixed(2), unit: '万元/人', foot: 'GDP ÷ 常住人口' },
    { label: '覆盖地市', value: o.city_cnt, unit: '个', foot: '含珠三角与粤东西北' }
  ]
})

const clockTimer = setInterval(() => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  clock.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}, 1000)

async function loadAll() {
  const results = await Promise.allSettled([
    getOverview(), getTrend(6), getRegionShare(), getCityRank(10), getCityMap(), getIndustry()
  ])
  const [ov, tr, rg, rk, mp, ind] = results
  let failed = 0
  if (ov.status === 'fulfilled') overview.value = ov.value
  else failed++
  if (tr.status === 'fulfilled') trendList.value = tr.value.list
  else failed++
  if (rg.status === 'fulfilled') regionList.value = rg.value.list
  else failed++
  if (rk.status === 'fulfilled') rankList.value = rk.value.list
  else failed++
  if (mp.status === 'fulfilled') mapList.value = mp.value.list
  else failed++
  if (ind.status === 'fulfilled') industryList.value = ind.value.list
  else failed++

  if (failed >= 4) {
    stale.value = true
  } else {
    stale.value = false
    const d = new Date()
    const p = (n) => String(n).padStart(2, '0')
    updateTime.value = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  }
}

/* ---------------- 轮询：页面隐藏时暂停 ---------------- */
let pollTimer = null
const startPoll = () => { if (!pollTimer) pollTimer = setInterval(loadAll, 30000) }
const stopPoll = () => { clearInterval(pollTimer); pollTimer = null }
const onVisible = () => (document.hidden ? stopPoll() : (loadAll(), startPoll()))

/* ---------------- 图表 ---------------- */
const trendEl = ref(null)
const industryEl = ref(null)
const regionEl = ref(null)
const rankEl = ref(null)
const mapEl = ref(null)

const axisStyle = {
  axisLine: { lineStyle: { color: 'rgba(120,180,255,0.35)' } },
  axisLabel: { color: '#8fb6dc', fontSize: 12 },
  splitLine: { lineStyle: { color: 'rgba(120,180,255,0.10)' } }
}

const trendOption = computed(() => {
  const years = trendList.value.map((i) => i.year)
  const gdp = trendList.value.map((i) => +i.gdp_yi.toFixed(0))
  const per = trendList.value.map((i) => i.per_capita)
  if (!years.length) return null
  return {
    grid: { left: 52, right: 52, top: 42, bottom: 28 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(6,20,40,0.92)', borderColor: '#1d6fff', textStyle: { color: '#cfe6ff' } },
    legend: { data: ['GDP 总量', '人均 GDP'], right: 8, top: 4, textStyle: { color: '#8fb6dc', fontSize: 12 }, itemWidth: 14, itemHeight: 8 },
    xAxis: { type: 'category', data: years, boundaryGap: true, ...axisStyle, splitLine: { show: false } },
    yAxis: [
      { type: 'value', name: '亿元', nameTextStyle: { color: '#6f9dc9', fontSize: 11 }, ...axisStyle },
      { type: 'value', name: '万元', nameTextStyle: { color: '#6f9dc9', fontSize: 11 }, ...axisStyle, splitLine: { show: false } }
    ],
    series: [
      {
        name: 'GDP 总量', type: 'bar', data: gdp, barWidth: 22,
        itemStyle: {
          borderRadius: [3, 3, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#37e0ff' }, { offset: 1, color: 'rgba(29,111,255,0.18)' }
          ])
        }
      },
      {
        name: '人均 GDP', type: 'line', yAxisIndex: 1, data: per, smooth: true, symbolSize: 6,
        lineStyle: { width: 2.4, color: '#ffd666' },
        itemStyle: { color: '#ffd666' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,214,102,0.28)' }, { offset: 1, color: 'rgba(255,214,102,0)' }
          ])
        }
      }
    ]
  }
})

const industryOption = computed(() => {
  if (!industryList.value.length) return null
  return {
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 亿元（{d}%）', backgroundColor: 'rgba(6,20,40,0.92)', borderColor: '#1d6fff', textStyle: { color: '#cfe6ff' } },
    legend: { orient: 'vertical', right: 12, top: 'center', textStyle: { color: '#8fb6dc', fontSize: 12 }, itemWidth: 12, itemHeight: 8 },
    graphic: [{
      type: 'text', left: '24%', top: '44%', style: {
        text: '三产占比\n' + industryList.value[2].value.toFixed(0) + ' 亿',
        fill: '#cfe6ff', fontSize: 13, align: 'center', lineHeight: 20
      }
    }],
    series: [{
      type: 'pie', radius: ['46%', '68%'], center: ['38%', '52%'], avoidLabelOverlap: true,
      itemStyle: { borderColor: 'rgba(3,6,15,0.9)', borderWidth: 2 },
      label: { show: false },
      labelLine: { length: 8, length2: 10, lineStyle: { color: 'rgba(120,180,255,0.4)' } },
      data: industryList.value,
      color: ['#37e0ff', '#1d6fff', '#ffd666']
    }]
  }
})

const regionOption = computed(() => {
  if (!regionList.value.length) return null
  const arr = [...regionList.value].sort((a, b) => a.value - b.value)
  return {
    grid: { left: 66, right: 60, top: 16, bottom: 12 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(6,20,40,0.92)', borderColor: '#1d6fff', textStyle: { color: '#cfe6ff' } },
    xAxis: { type: 'value', ...axisStyle, axisLabel: { show: false }, splitLine: { show: false } },
    yAxis: { type: 'category', data: arr.map((i) => i.name), ...axisStyle, splitLine: { show: false }, axisLabel: { color: '#cfe6ff', fontSize: 13 } },
    series: [{
      type: 'bar', data: arr.map((i) => i.value), barWidth: 16,
      showBackground: true, backgroundStyle: { color: 'rgba(120,180,255,0.07)', borderRadius: 8 },
      itemStyle: {
        borderRadius: 8,
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#1d6fff' }, { offset: 1, color: '#37e0ff' }
        ])
      },
      label: { show: true, position: 'right', color: '#ffd666', fontSize: 12, formatter: (p) => `${arr[p.dataIndex].pct}%` }
    }]
  }
})

const rankOption = computed(() => {
  if (!rankList.value.length) return null
  const arr = [...rankList.value].reverse()
  return {
    grid: { left: 78, right: 74, top: 10, bottom: 10 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(6,20,40,0.92)', borderColor: '#1d6fff', textStyle: { color: '#cfe6ff' } },
    xAxis: { type: 'value', ...axisStyle, axisLabel: { show: false }, splitLine: { show: false } },
    yAxis: { type: 'category', data: arr.map((i) => i.city_name), ...axisStyle, splitLine: { show: false }, axisLabel: { color: '#cfe6ff', fontSize: 12 } },
    series: [{
      type: 'bar', data: arr.map((i) => +i.gdp_yi.toFixed(0)), barWidth: 11,
      itemStyle: {
        borderRadius: 6,
        color: (p) => new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: 'rgba(29,111,255,0.35)' },
          { offset: 1, color: p.dataIndex >= 7 ? '#ffd666' : '#37e0ff' }
        ])
      },
      label: { show: true, position: 'right', color: '#9fd4ff', fontSize: 11, formatter: '{c}' }
    }]
  }
})

const mapOption = computed(() => {
  if (!mapList.value.length || !window.__gdReady) return null
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(6,20,40,0.92)', borderColor: '#1d6fff', textStyle: { color: '#cfe6ff' },
      formatter: (p) => p.data ? `${p.name}<br/>GDP：${p.data.value[2]} 亿元<br/>人均：${p.data.per_capita} 万元` : p.name
    },
    visualMap: {
      show: false, min: 1000, max: 35000, seriesIndex: 0,
      inRange: { color: ['#0b2a5b', '#14539e', '#2a8fe0', '#37e0ff'] }
    },
    geo: {
      map: 'guangdong', roam: false, layoutCenter: ['48%', '50%'], layoutSize: '102%',
      itemStyle: { areaColor: 'rgba(10,32,66,0.55)', borderColor: 'rgba(64,158,255,0.55)', borderWidth: 1 },
      emphasis: { itemStyle: { areaColor: 'rgba(29,111,255,0.35)' }, label: { color: '#fff' } },
      label: { show: false }
    },
    series: [
      {
        name: 'GDP', type: 'map', map: 'guangdong', geoIndex: 0, data: []
      },
      {
        name: '城市', type: 'effectScatter', coordinateSystem: 'geo',
        data: mapList.value.map((i) => ({ name: i.name, value: [...i.coord, i.value], per_capita: i.per_capita })),
        symbolSize: (v) => Math.max(8, Math.min(24, Math.sqrt(v[2]) / 8)),
        rippleEffect: { scale: 3, brushType: 'stroke' },
        itemStyle: { color: '#ffd666', shadowBlur: 10, shadowColor: 'rgba(255,214,102,0.6)' },
        label: {
          show: true, position: 'right', formatter: '{b}', color: '#cfe6ff', fontSize: 11,
          distance: 4
        },
        emphasis: { label: { show: true, color: '#fff', fontWeight: 'bold' } }
      }
    ]
  }
})

const { } = useChart(trendEl, () => trendOption.value, trendList)
useChart(industryEl, () => industryOption.value, industryList)
useChart(regionEl, () => regionOption.value, regionList)
useChart(rankEl, () => rankOption.value, rankList)
const { chart: mapChart } = useChart(mapEl, () => mapOption.value, mapList)

/* ---------------- 生命周期 ---------------- */
onMounted(async () => {
  fit()
  window.addEventListener('resize', onResize)
  document.addEventListener('visibilitychange', onVisible)

  // 地图 GeoJSON 注册
  try {
    const geo = await fetch('/guangdong.json').then((r) => r.json())
    echarts.registerMap('guangdong', geo)
    window.__gdReady = true
    // 地图数据到达后补一次渲染
    setTimeout(() => {
      if (mapChart.value) mapChart.value.setOption(mapOption.value, true)
    }, 50)
  } catch (e) {
    console.warn('地图数据加载失败', e)
  }

  await loadAll()
  startPoll()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  document.removeEventListener('visibilitychange', onVisible)
  clearInterval(clockTimer)
  stopPoll()
})
</script>

<style scoped>
.viewport {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(29, 111, 255, 0.22), transparent 70%),
    #03060f;
}
.screen {
  width: 1920px;
  height: 1080px;
  transform-origin: left top;
  display: flex;
  flex-direction: column;
  padding: 0 24px 20px;
}

/* 顶部 */
.topbar {
  flex: none;
  height: 92px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  background: linear-gradient(180deg, rgba(29, 111, 255, 0.22), rgba(3, 6, 15, 0));
  border-bottom: 1px solid rgba(64, 158, 255, 0.25);
}
.topbar__title {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 6px;
  color: #eaf6ff;
  text-shadow: 0 0 22px rgba(55, 224, 255, 0.75), 0 0 60px rgba(29, 111, 255, 0.55);
}
.topbar__left { display: flex; align-items: center; gap: 8px; }
.topbar__meta { font-size: 12px; color: #6f9dc9; letter-spacing: 0.5px; }
.dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #37e0ff; box-shadow: 0 0 10px #37e0ff;
}
.topbar__right { display: flex; align-items: center; justify-content: flex-end; gap: 14px; }
.clock { font-size: 14px; color: #9fd4ff; letter-spacing: 1px; font-variant-numeric: tabular-nums; }
.status {
  font-size: 12px; color: #37e0ff; padding: 3px 10px;
  border: 1px solid rgba(55, 224, 255, 0.45); border-radius: 10px;
  background: rgba(55, 224, 255, 0.08);
}
.status--warn { color: #ffb45c; border-color: rgba(255, 180, 92, 0.5); background: rgba(255, 180, 92, 0.1); }

/* 三列布局 */
.grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 460px 1fr 460px;
  gap: 16px;
  padding-top: 16px;
}
.col { display: flex; flex-direction: column; gap: 16px; min-height: 0; }
.cell { flex: 1; min-height: 0; }
.cell--h44 { flex: 0 0 44%; }
.cell--h56 { flex: 1; }
.cell--h52 { flex: 0 0 52%; }
.cell--h48 { flex: 1; }
.chart { width: 100%; height: 100%; }

/* KPI */
.kpis {
  flex: none;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.kpi {
  position: relative;
  padding: 12px 14px;
  background: linear-gradient(180deg, rgba(20, 48, 96, 0.85), rgba(8, 18, 38, 0.65));
  border: 1px solid rgba(64, 158, 255, 0.28);
  border-radius: 4px;
  overflow: hidden;
}
.kpi::after {
  content: '';
  position: absolute; left: 0; top: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, #37e0ff, transparent);
}
.kpi__label { font-size: 12px; color: #7fa9d0; letter-spacing: 0.5px; }
.kpi__value { display: flex; align-items: baseline; gap: 6px; margin: 6px 0 2px; }
.num {
  font-size: 30px; font-weight: 700; color: #37e0ff; line-height: 1;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 18px rgba(55, 224, 255, 0.45);
}
.unit { font-size: 12px; color: #8fb6dc; }
.kpi__foot { font-size: 11px; color: #5b84ad; }

.map-cell { flex: 1; min-height: 0; }
</style>
