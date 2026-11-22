import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts/core'
import {
  BarChart, LineChart, PieChart, MapChart, EffectScatterChart, ScatterChart
} from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  GraphicComponent, VisualMapComponent, DatasetComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, LineChart, PieChart, MapChart, EffectScatterChart, ScatterChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  GraphicComponent, VisualMapComponent, DatasetComponent, CanvasRenderer
])

/**
 * 图表实例统一管理：创建 / 配置合并 / resize / 销毁
 * @param {Ref<HTMLElement>} elRef  容器
 * @param {Function} optionFactory  () => option，数据变化时重新取
 * @param {Ref<any>} deps           依赖数据，变化即重绘
 */
export function useChart(elRef, optionFactory, deps) {
  const chart = shallowRef(null)
  const loading = ref(false)

  const render = () => {
    if (!chart.value) return
    const option = optionFactory()
    if (!option) return
    chart.value.setOption(option, true)
  }

  let timer = null
  const onResize = () => {
    clearTimeout(timer)
    timer = setTimeout(() => chart.value?.resize(), 200)
  }

  const dpr = window.devicePixelRatio || 1

  onMounted(() => {
    chart.value = echarts.init(elRef.value, null, { devicePixelRatio: dpr * 2 })
    render()
    window.addEventListener('resize', onResize)
  })

  watch(deps, render, { deep: true })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', onResize)
    clearTimeout(timer)
    chart.value?.dispose()
    chart.value = null
  })

  return { chart, loading, render }
}

export { echarts }
