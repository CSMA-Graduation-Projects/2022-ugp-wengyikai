<template>
  <div class="task-graph-wrapper">
    <div ref="chart" class="task-graph"></div>

    <div v-if="tasks && tasks.length" class="graph-tip">
      <span class="tip-item"><i class="dot dot-story"></i> 用户故事</span>
      <span class="tip-item"><i class="dot dot-frontend"></i> 前端任务</span>
      <span class="tip-item"><i class="dot dot-backend"></i> 后端任务</span>
      <span class="tip-item"><i class="dot dot-database"></i> 数据库任务</span>
    </div>

    <el-empty
      v-if="!tasks || !tasks.length"
      description="暂无任务依赖图数据"
      :image-size="90"
    />
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'TaskGraph',
  props: {
    tasks: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      chart: null
    }
  },
  watch: {
    tasks: {
      handler() {
        this.$nextTick(() => {
          this.renderChart()
        })
      },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    this.initChart()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    initChart() {
      if (this.$refs.chart && !this.chart) {
        this.chart = echarts.init(this.$refs.chart)
      }
      this.renderChart()
    },

    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },

    getCategoryIndex(type) {
      if (type === 'frontend') return 1
      if (type === 'backend') return 2
      if (type === 'database') return 3
      return 4
    },

    buildGraphData() {
      const colors = {
        story: '#409EFF',
        frontend: '#67C23A',
        backend: '#E6A23C',
        database: '#F56C6C',
        other: '#909399'
      }

      const nodes = []
      const links = []

      const storySet = new Set()
      const taskNodeMap = new Map()

      // 故事节点 + 任务节点 + 故事到任务
      this.tasks.forEach(task => {
        const taskNodeName = `${task.id || ''} ${task.name || ''}`.trim()
        const storyName = task.story || '未归类故事'
        const taskType = task.type || 'other'

        if (!storySet.has(storyName)) {
          nodes.push({
            name: storyName,
            value: storyName,
            category: 0,
            symbolSize: 60,
            draggable: true,
            itemStyle: {
              color: colors.story
            },
            label: {
              show: true,
              fontSize: 12,
              lineHeight: 16
            }
          })
          storySet.add(storyName)
        }

        if (!taskNodeMap.has(task.id)) {
          nodes.push({
            name: taskNodeName,
            value: task.id,
            category: this.getCategoryIndex(taskType),
            symbolSize: 42,
            draggable: true,
            itemStyle: {
              color: colors[taskType] || colors.other
            },
            label: {
              show: true,
              fontSize: 12
            },
            taskId: task.id,
            story: storyName,
            taskType
          })
          taskNodeMap.set(task.id, taskNodeName)
        }

        links.push({
          source: storyName,
          target: taskNodeName,
          lineStyle: {
            color: '#C0C4CC',
            width: 1.2,
            type: 'dashed'
          }
        })
      })

      // 任务依赖连线
      this.tasks.forEach(task => {
        const currentTaskNodeName = taskNodeMap.get(task.id)
        const dependsOn = Array.isArray(task.depends_on) ? task.depends_on : []

        dependsOn.forEach(depId => {
          const depTaskNodeName = taskNodeMap.get(depId)
          if (depTaskNodeName && currentTaskNodeName) {
            links.push({
              source: depTaskNodeName,
              target: currentTaskNodeName,
              lineStyle: {
                color: '#606266',
                width: 2
              }
            })
          }
        })
      })

      return { nodes, links }
    },

    renderChart() {
      if (!this.chart) {
        if (this.$refs.chart) {
          this.chart = echarts.init(this.$refs.chart)
        } else {
          return
        }
      }

      if (!this.tasks || !this.tasks.length) {
        this.chart.clear()
        return
      }

      const { nodes, links } = this.buildGraphData()

      const option = {
        backgroundColor: '#ffffff',
        tooltip: {
          trigger: 'item',
          formatter: params => {
            const data = params.data || {}

            if (data.category === 0) {
              return `
                <div style="max-width: 320px; white-space: normal; line-height: 1.6;">
                  <strong>用户故事</strong><br/>
                  ${data.name}
                </div>
              `
            }

            return `
              <div style="max-width: 320px; white-space: normal; line-height: 1.6;">
                <strong>任务节点</strong><br/>
                名称：${data.name || ''}<br/>
                ID：${data.taskId || ''}<br/>
                类型：${data.taskType || ''}<br/>
                所属故事：${data.story || ''}
              </div>
            `
          }
        },
        legend: {
          top: 10,
          data: ['用户故事', '前端任务', '后端任务', '数据库任务']
        },
        animationDuration: 800,
        animationEasingUpdate: 'quinticInOut',
        series: [
          {
            type: 'graph',
            layout: 'force',
            roam: true,
            draggable: true,
            focusNodeAdjacency: true,
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: [4, 10],
            force: {
              repulsion: 900,
              gravity: 0.08,
              edgeLength: 180
            },
            data: nodes,
            links,
            categories: [
              { name: '用户故事' },
              { name: '前端任务' },
              { name: '后端任务' },
              { name: '数据库任务' },
              { name: '其他任务' }
            ],
            lineStyle: {
              opacity: 0.9,
              curveness: 0.08
            },
            label: {
              show: true,
              position: 'right',
              formatter: value => {
                const text = value.name || ''
                return text.length > 20 ? text.slice(0, 20) + '...' : text
              }
            },
            emphasis: {
              scale: true,
              lineStyle: {
                width: 3
              }
            }
          }
        ]
      }

      this.chart.setOption(option, true)
      this.bindChartEvents()
      this.chart.resize()
    },

    bindChartEvents() {
      if (!this.chart) return

      this.chart.off('click')
      this.chart.on('click', params => {
        const data = params.data || {}

        if (data.category === 0) {
          this.$emit('select-story', data.name)
          return
        }

        if (data.story) {
          this.$emit('select-story', data.story)
        }
      })
    }
  }
}
</script>

<style scoped>
.task-graph-wrapper {
  width: 100%;
}

.task-graph {
  width: 100%;
  height: 500px;
  background: #fff;
  border-radius: 8px;
}

.graph-tip {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  color: #606266;
}

.tip-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-story {
  background: #409EFF;
}

.dot-frontend {
  background: #67C23A;
}

.dot-backend {
  background: #E6A23C;
}

.dot-database {
  background: #F56C6C;
}
</style>