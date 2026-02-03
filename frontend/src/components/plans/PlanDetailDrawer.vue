<template>
  <el-drawer
      v-model="drawerVisible"
      :title="planData ? planData.name : '计划详情'"
      :size="isMobile ? '90%' : '60%'"
      direction="rtl"
      destroy-on-close
  >
    <div v-loading="loading" class="plan-detail">
      <div v-if="planData" class="detail-content">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <plan-status-tag :status="planData.status" size="small" />
            </div>
          </template>

          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="计划ID">
              {{ planData.id }}
            </el-descriptions-item>
            <el-descriptions-item label="计划类型">
              <el-tag :type="planTypeTagType" size="small">
                {{ planData.plan_type === 'scheduled' ? '定时' : planData.plan_type === 'manual' ? '手动' : '自动' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建人">
              {{ planData.created_by || '系统' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(planData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后执行">
              {{ planData.last_execution_time ? formatRelativeTime(planData.last_execution_time) : '从未执行' }}
            </el-descriptions-item>
            <el-descriptions-item label="执行方式">
              {{ planData.distributed ? '分布式' : '本地' }}
            </el-descriptions-item>
            <el-descriptions-item v-if="planData.schedule_type" label="调度设置" :span="2">
              {{ getScheduleDescription() }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 执行统计 -->
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>执行统计</span>
            </div>
          </template>

          <div class="stats-content">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">总用例数</div>
                <div class="stat-value">{{ planData.total_cases || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">已执行</div>
                <div class="stat-value">{{ planData.executed_cases || 0 }}</div>
                <div class="stat-percent">
                  {{ totalPercent(planData.executed_cases) }}%
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">通过</div>
                <div class="stat-value success">{{ planData.passed_cases || 0 }}</div>
                <div class="stat-percent">
                  {{ totalPercent(planData.passed_cases) }}%
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">失败</div>
                <div class="stat-value failed">{{ planData.failed_cases || 0 }}</div>
                <div class="stat-percent">
                  {{ totalPercent(planData.failed_cases) }}%
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">执行中</div>
                <div class="stat-value">{{ planData.executing_cases || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">未执行</div>
                <div class="stat-value">{{ (planData.total_cases || 0) - (planData.executed_cases || 0) }}</div>
              </div>
            </div>

            <div class="progress-section">
              <div class="progress-label">总体进度</div>
              <el-progress
                  :percentage="totalPercent(planData.executed_cases)"
                  :color="progressColor"
                  :stroke-width="12"
                  :show-text="false"
              />
              <div class="progress-bar-details">
                <div class="progress-segment passed" :style="{ width: totalPercent(planData.passed_cases) + '%' }"></div>
                <div class="progress-segment failed" :style="{ width: totalPercent(planData.failed_cases) + '%' }"></div>
                <div class="progress-segment executing" :style="{ width: totalPercent(planData.executing_cases) + '%' }"></div>
              </div>
              <div class="progress-legend">
                <div class="legend-item">
                  <span class="legend-color passed"></span>
                  <span class="legend-label">通过</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color failed"></span>
                  <span class="legend-label">失败</span>
                </div>

                <div class="legend-item">
                  <span class="legend-color executing"></span>
                  <span class="legend-label">执行中</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 执行历史 -->
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>执行历史</span>
              <el-button link @click="viewAllHistory" type="primary">查看全部</el-button>
            </div>
          </template>

<!--          <el-message :plan-id="planId" :limit="5" />-->
          <el-empty description="当前不支持查看，等待后续版本实现" />
        </el-card>

        <!-- 包含用例 -->
        <el-card class="cases-card">
          <template #header>
            <div class="card-header">
              <span>包含用例</span>
              <div class="case-filter">
                <el-select
                    v-model="caseFilter.status"
                    placeholder="按状态筛选"
                    size="small"
                    style="width: 120px"
                >
                  <el-option label="全部" value="" />
                  <el-option label="通过" value="passed" />
                  <el-option label="失败" value="failed" />
                  <el-option label="执行中" value="executing" />
                  <el-option label="未执行" value="not_executed" />
                </el-select>
              </div>
            </div>
          </template>

          <el-empty description="当前不支持查看，等待后续版本实现" />
        </el-card>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
              v-if="planData.status === 'waiting' || planData.status === 'failed'"
              type="primary"
              :icon="VideoPlay"
              @click="handleExecute"
              :loading="executing"
          >
            立即执行
          </el-button>
          <el-button
              v-if="planData.status === 'running'"
              type="warning"
              :icon="Pause"
              @click="handlePause"
              :loading="pausing"
          >
            暂停执行
          </el-button>
          <el-button
              v-if="planData.status === 'paused'"
              type="success"
              :icon="VideoPlay"
              @click="handleResume"
              :loading="resuming"
          >
            继续执行
          </el-button>
          <el-button
              v-if="planData.status === 'waiting'"
              type="danger"
              :icon="Delete"
              @click="handleDelete"
          >
            删除计划
          </el-button>
          <el-button
              type="info"
              :icon="Download"
              @click="handleExport"
          >
            导出结果
          </el-button>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="未找到计划信息" />
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPlay,
  Pause,
  Delete,
  Download
} from '@element-plus/icons-vue'
import api from '../../api'
import PlanStatusTag from './PlanStatusTag.vue'
import { formatTime, formatRelativeTime } from '@/utils/formatter'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  planId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const router = useRouter()

// 数据状态
const loading = ref(false)
const planData = ref(null)
const executing = ref(false)
const pausing = ref(false)
const resuming = ref(false)

// 用例筛选
const caseFilter = ref({
  status: ''
})
const caseFilterKey = ref(0)

// 移动端检测
const isMobile = computed(() => {
  return window.innerWidth <= 768
})

// 计算属性
const planTypeTagType = computed(() => {
  switch (planData.value?.plan_type) {
    case 'scheduled': return 'warning'
    case 'manual': return 'info'
    case 'auto': return 'success'
    default: return 'info'
  }
})

const progressColor = computed(() => {
  switch (planData.value?.status) {
    case 'completed': return '#52c41a'
    case 'failed': return '#f5222d'
    case 'running': return '#1890ff'
    default: return '#faad14'
  }
})

// 计算百分比
const totalPercent = (value) => {
  if (!planData.value?.total_cases || planData.value.total_cases === 0) {
    return 0
  }
  return Math.round((value || 0) / planData.value.total_cases * 100)
}

// 获取调度描述
const getScheduleDescription = () => {
  if (!planData.value?.schedule_type) return ''

  if (planData.value.schedule_type === 'daily') {
    return `每天 ${planData.value.schedule_time} 执行`
  } else if (planData.value.schedule_type === 'weekly') {
    const dayMap = { '0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六' }
    const days = planData.value.week_days?.map(day => `周${dayMap[day]}`).join('、') || ''
    return `每周${days} ${planData.value.schedule_time} 执行`
  } else if (planData.value.schedule_type === 'cron') {
    return `Cron表达式: ${planData.value.cron_expression}`
  }
  return ''
}

// 获取计划详情
const fetchPlanDetail = async () => {
  if (!props.planId) return

  try {
    loading.value = true

    // 由于后端API没有获取单个计划的接口，我们通过列表筛选获取
    const response = await api.getTestPlans({
      page: 1,
      per_page: 1,
      search: `id:${props.planId}`,
      status: `${planData?.value?.status || ""}`,
    })

    if (response.success && response.plans.length > 0) {
      planData.value = response.plans[0]
    }
  } catch (error) {
    console.error('获取计划详情失败:', error)
    ElMessage.error('获取计划详情失败')
  } finally {
    loading.value = false
  }
}

// 执行计划
const handleExecute = async () => {
  try {
    executing.value = true
    await api.executeTestPlan({
      name: `执行: ${planData.value.name}`,
      include_paths: planData.value.include_paths || [],
      distributed: planData.value.distributed || false
    })

    ElMessage.success('计划已开始执行')
    planData.value.status = 'running'
    emit('refresh')
  } catch (error) {
    console.error('执行计划失败:', error)
    ElMessage.error('执行计划失败')
  } finally {
    executing.value = false
  }
}

// 暂停计划
const handlePause = async () => {
  try {
    pausing.value = true
    // 这里调用暂停API
    // 由于没有暂停API，我们模拟一下
    await new Promise(resolve => setTimeout(resolve, 1000))
    planData.value.status = 'paused'
    await fetchPlanDetail()
    ElMessage.success('计划已暂停')
    emit('refresh')
  } catch (error) {
    console.error('暂停计划失败:', error)
    ElMessage.error('暂停计划失败')
  } finally {
    pausing.value = false
  }
}

// 继续执行
const handleResume = async () => {
  try {
    resuming.value = true
    // 这里调用继续执行API
    await new Promise(resolve => setTimeout(resolve, 1000))
    planData.value.status = 'running'
    await fetchPlanDetail()
    ElMessage.success('计划已继续执行')
    emit('refresh')
  } catch (error) {
    console.error('继续执行失败:', error)
    ElMessage.error('继续执行失败')
  } finally {
    resuming.value = false
  }
}

// 删除计划
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
        `确定要删除计划 "${planData.value.name}" 吗？删除后无法恢复。`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'error'
        }
    )

    // 这里调用删除API
    // 由于没有删除API，我们模拟删除
    ElMessage.success('计划已删除')
    drawerVisible.value = false
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除计划失败:', error)
      ElMessage.error('删除计划失败')
    }
  }
}

// 导出结果
const handleExport = async () => {
  try {
    // 这里调用导出API
    ElMessage.success('导出任务已开始，请稍后查看下载')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 查看全部历史
const viewAllHistory = () => {
  router.push({
    path: '/execution-history',
    query: { plan_id: props.planId }
  })
}

// 监听planId变化
watch(() => props.planId, () => {
  if (props.planId) {
    fetchPlanDetail()
  } else {
    planData.value = null
  }
}, { immediate: true })

// 监听筛选变化
watch(caseFilter, () => {
  caseFilterKey.value++
}, { deep: true })

// 监听抽屉显示状态
watch(drawerVisible, (val) => {
  if (val && props.planId) {
    fetchPlanDetail()
  }
})
</script>

<style scoped>
.plan-detail {
  height: 100%;
  padding: 0 8px;
  overflow-y: auto;
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
  padding-bottom: 80px;
}

.info-card,
.stats-card,
.history-card,
.cases-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-content {
  padding: 8px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: #fafafa;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-value.success {
  color: #52c41a;
}

.stat-value.failed {
  color: #f5222d;
}

.stat-percent {
  font-size: 12px;
  color: #999;
}

.progress-section {
  margin-top: 24px;
}

.progress-label {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.progress-bar-details {
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  margin-top: 4px;
}

.progress-segment {
  height: 100%;
}

.progress-segment.passed {
  background: #52c41a;
}

.progress-segment.failed {
  background: #f5222d;
}

.progress-segment.executing {
  background: #1890ff;
}

.progress-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.passed {
  background: #52c41a;
}

.legend-color.failed {
  background: #f5222d;
}

.legend-color.executing {
  background: #1890ff;
}

.legend-label {
  font-size: 12px;
  color: #666;
}

.case-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-buttons {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-buttons {
    flex-wrap: wrap;
    justify-content: center;
    width: calc(100% - 32px);
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
