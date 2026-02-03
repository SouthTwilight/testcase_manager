<template>
  <div class="dashboard-container">
    <!-- 统计卡片区域 -->
    <div class="stat-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <stat-card
              title="总用例数"
              :value="stats.total_cases"
              icon="Document"
              color="#1890ff"
              :loading="loading"
          >
            <template #footer>
              今日新增 <span class="highlight">{{ stats?.today_cases || 0 }}</span> 个
            </template>
          </stat-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <stat-card
              title="通过用例"
              :value="stats.passed_cases"
              icon="CircleCheck"
              color="#52c41a"
              :loading="loading"
          >
            <template #footer>
              成功率 <span class="highlight">{{ stats?.success_rate || 0 }}%</span>
            </template>
          </stat-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <stat-card
              title="失败用例"
              :value="stats.failed_cases"
              icon="CircleClose"
              color="#f5222d"
              :loading="loading"
          >
            <template #footer>
              占比 <span class="highlight">{{ failureRate || 0 }}%</span>
            </template>
          </stat-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <stat-card
              title="未执行用例"
              :value="stats.not_executed_cases"
              icon="Clock"
              color="#faad14"
              :loading="loading"
          >
            <template #footer>
              最近执行 <span class="highlight">{{ stats?.recent_executions || 0}}</span> 次
            </template>
          </stat-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="chart-area">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="24" :md="16" :lg="16">
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <span>用例状态分布</span>
                <div class="chart-actions">
                  <el-radio-group v-model="chartType" size="small">
                    <el-radio-button label="pie">饼图</el-radio-button>
                    <el-radio-button label="bar">柱状图</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
            </template>
            <div v-loading="chartLoading" class="chart-container">
              <test-case-chart
                  :type="chartType"
                  :data="chartData"
                  height="350px"
              />
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="24" :md="8" :lg="8">
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <span>目录统计</span>
              </div>
            </template>
            <div v-loading="categoryLoading" class="category-container">
              <category-stats :data="categoryStats" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 快速操作和最近执行 -->
    <div class="quick-area">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="quick-card">
            <template #header>
              <div class="card-header">
                <span>快速操作</span>
              </div>
            </template>
            <div class="quick-actions">
              <el-button
                  type="primary"
                  :icon="Refresh"
                  :loading="scanLoading"
                  @click="handleScanCases"
              >
                扫描用例
              </el-button>
              <el-button
                  type="success"
                  :icon="VideoPlay"
                  @click="handleExecutePlan"
              >
                执行计划
              </el-button>
              <el-button
                  type="warning"
                  :icon="Bell"
                  @click="handleCheckFailures"
              >
                查看失败用例
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="quick-card">
            <template #header>
              <div class="card-header">
                <span>最近执行记录</span>
                <el-button type="text" @click="gotoHistory">查看全部</el-button>
              </div>
            </template>
            <recent-executions :data="recentExecutions" />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 执行计划弹窗 -->
    <execute-plan-dialog
        v-model="planDialogVisible"
        @success="handlePlanSuccess"
    />
  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch, onUnmounted} from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  VideoPlay,
  Bell
} from '@element-plus/icons-vue'
import api from '../api'
import StatCard from '../components/dashboard/StatCard.vue'
import TestCaseChart from '../components/dashboard/TestCaseChart.vue'
import CategoryStats from '../components/dashboard/CategoryStats.vue'
import RecentExecutions from '../components/dashboard/RecentExecutions.vue'
import ExecutePlanDialog from '../components/plan/ExecutePlanDialog.vue'

const router = useRouter()

// 数据状态
const loading = ref(true)
const chartLoading = ref(true)
const categoryLoading = ref(true)
const scanLoading = ref(false)
const planDialogVisible = ref(false)

// 图表数据
const chartType = ref('pie')

// 关键修改：确保 stats 始终有默认值
const stats = ref({
  total_cases: 0,
  passed_cases: 0,
  failed_cases: 0,
  not_executed_cases: 0,
  executing_cases: 0,
  today_cases: 0,
  recent_executions: 0,
  success_rate: 0
})

const chartData = ref([])
const categoryStats = ref([])
const recentExecutions = ref([])

// 计算失败率 - 添加防御性检查
const failureRate = computed(() => {
  const total = stats.value.total_cases
  const failed = stats.value.failed_cases
  if (total === 0) return '0.00'
  const rate = (failed / total * 100).toFixed(2)
  return rate === '0.00' ? '0' : rate
})

// 获取仪表板数据 - 改进错误处理
const fetchDashboardData = async () => {
  try {
    loading.value = true
    chartLoading.value = true
    categoryLoading.value = true

    // 获取统计数据
    const [statsRes, categoryRes, historyRes] = await Promise.all([
      api.getDashboardStats().catch(err => {
        console.error('获取统计数据失败:', err)
        return { success: false, data: null }
      }),
      api.getTestCaseStats().catch(err => {
        console.error('获取分类统计失败:', err)
        return { success: false, data: null }
      }),
      api.getExecutionHistory({ page: 1, per_page: 5 }).catch(err => {
        console.error('获取执行历史失败:', err)
        return { success: false, data: null }
      })
    ])

    // 更新统计数据
    if (statsRes?.success) {
      // 只更新存在的字段，保持默认值
      stats.value = {
        ...stats.value,  // 保留默认值
        ...statsRes // 用 API 数据覆盖
      }
    }

    // 更新分类统计
    if (categoryRes?.success) {
      categoryStats.value = categoryRes.stats || []
    }

    // 更新执行历史
    if (historyRes?.success) {
      recentExecutions.value = historyRes.history || []
    }

    // 准备图表数据
    prepareChartData()

  } catch (error) {
    console.error('获取仪表板数据失败:', error)
    ElMessage.error('获取数据失败，请检查网络连接')
  } finally {
    loading.value = false
    chartLoading.value = false
    categoryLoading.value = false
  }
}

// 准备图表数据 - 添加防御性检查
const prepareChartData = () => {
  // 确保 stats.value 存在
  if (!stats.value) return

  chartData.value = [
    {
      name: '通过',
      value: stats.value.passed_cases || 0,
      color: '#52c41a'
    },
    {
      name: '失败',
      value: stats.value.failed_cases || 0,
      color: '#f5222d'
    },
    {
      name: '未执行',
      value: stats.value.not_executed_cases || 0,
      color: '#faad14'
    },
    {
      name: '执行中',
      value: stats.value.executing_cases || 0,
      color: '#1890ff'
    }
  ].filter(item => item.value > 0)
}

// 其他方法保持不变...

// 组件挂载时加载数据
onMounted(() => {
  fetchDashboardData()

  // 设置定时刷新 - 添加清理
  const intervalId = setInterval(fetchDashboardData, 60000 * 30)

  // 组件销毁时清理定时器
  onUnmounted(() => {
    clearInterval(intervalId)
  })
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-cards {
  margin-bottom: 20px;
}

.chart-area {
  margin-bottom: 20px;
}

.quick-area {
  margin-bottom: 20px;
}

.chart-card {
  height: 100%;
  min-height: 400px;
}

.quick-card {
  height: 100%;
  min-height: 200px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 350px;
}

.category-container {
  height: 350px;
  overflow-y: auto;
}

.quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.highlight {
  font-weight: bold;
  color: #1890ff;
}

@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }

  .category-container {
    height: 300px;
  }
}
</style>
