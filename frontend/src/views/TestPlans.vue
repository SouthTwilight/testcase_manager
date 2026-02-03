<template>
  <div class="test-plans-container">
    <!-- 创建计划工具栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar-content">
        <div class="toolbar-left">
          <el-button
              type="primary"
              :icon="Plus"
              @click="handleCreatePlan"
          >
            创建测试计划
          </el-button>
          <el-button
              type="success"
              :icon="VideoPlay"
              @click="handleExecuteAll"
              :disabled="selectedPlans.length === 0"
          >
            执行选中计划
          </el-button>
        </div>

        <div class="toolbar-right">
          <el-input
              v-model="filterForm.search"
              placeholder="搜索计划名称"
              prefix-icon="Search"
              style="width: 200px"
              @keyup.enter="handleSearch"
          />
          <el-button
              type="info"
              :icon="Refresh"
              @click="handleRefresh"
              :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 计划统计 - 添加 wrapper -->
    <div class="stats-wrapper">
      <el-row :gutter="16" class="stats-row">
        <el-col
            v-for="(stat, index) in statItems"
            :key="index"
            :xs="12"
            :sm="6"
            :md="4"
            :lg="4"
            class="stat-col"
        >
          <div
              class="stat-item"
              :class="stat.type"
              @click="stat.clickHandler"
          >
            <div class="stat-icon">
              <el-icon>
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 计划表格 -->
    <el-card class="table-card">
      <div class="table-container">
        <el-table
            v-loading="loading"
            :data="tableData"
            style="width: 100%"
            @selection-change="handleSelectionChange"
            @row-click="handleRowClick"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column type="index" label="序号" width="60" />

          <el-table-column prop="name" label="计划名称" min-width="200">
            <template #default="{ row }">
              <div class="plan-name-cell">
                <el-tag
                    v-if="row.plan_type === 'scheduled'"
                    size="small"
                    type="warning"
                    class="plan-type-tag"
                >
                  定时
                </el-tag>
                <el-tag
                    v-else-if="row.plan_type === 'manual'"
                    size="small"
                    type="info"
                    class="plan-type-tag"
                >
                  手动
                </el-tag>
                <el-tag
                    v-else-if="row.plan_type === 'auto'"
                    size="small"
                    type="success"
                    class="plan-type-tag"
                >
                  自动
                </el-tag>
                <span class="plan-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <plan-status-tag :status="row.status" />
            </template>
          </el-table-column>

          <el-table-column prop="progress" label="进度" width="180">
            <template #default="{ row }">
              <plan-progress :plan="row" />
            </template>
          </el-table-column>

          <el-table-column prop="created_by" label="创建人" width="120">
            <template #default="{ row }">
              <div class="creator-cell">
                <el-avatar :size="24" class="creator-avatar">
                  {{ row.created_by?.charAt(0) || 'U' }}
                </el-avatar>
                <span class="creator-name">{{ row.created_by || '-' }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="160" sortable>
            <template #default="{ row }">
              <div class="time-cell">
                {{ formatTime(row.created_at, 'MM-DD HH:mm') }}
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="last_execution_time" label="最后执行" width="160" sortable>
            <template #default="{ row }">
              <div v-if="row.last_execution_time" class="time-cell">
                {{ formatRelativeTime(row.last_execution_time) }}
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="execution_stats" label="执行统计" width="180">
            <template #default="{ row }">
              <div class="stats-cell">
                <span class="stat-passed">{{ row.passed_cases || 0 }}</span>
                <span class="stat-separator">/</span>
                <span class="stat-failed">{{ row.failed_cases || 0 }}</span>
                <span class="stat-separator">/</span>
                <span class="stat-total">{{ row.total_cases || 0 }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                    v-if="row.status === 'waiting' || row.status === 'failed'"
                    type="primary"
                    size="small"
                    :icon="VideoPlay"
                    @click.stop="handleExecutePlan(row)"
                    :loading="executingPlan === row.id"
                >
                  执行
                </el-button>
                <el-button
                    type="warning"
                    size="small"
                    :icon="View"
                    @click.stop="handleViewDetail(row)"
                >
                  详情
                </el-button>
                <el-button
                    v-if="row.status === 'waiting'"
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click.stop="handleDeletePlan(row)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
              v-model:current-page="pagination.current"
              v-model:page-size="pagination.size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 创建计划对话框 -->
    <create-plan-dialog
        v-model="createDialogVisible"
        @success="handleCreateSuccess"
    />

    <!-- 计划详情抽屉 -->
    <plan-detail-drawer
        v-model="detailDrawerVisible"
        :plan-id="selectedPlanId"
        @refresh="handleRefresh"
    />

    <!-- 批量执行确认 -->
    <batch-execute-confirm
        v-model="batchConfirmVisible"
        :plans="selectedPlans"
        @success="handleBatchExecuteSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  VideoPlay,
  Refresh,
  Search,
  List,
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
  AlarmClock,
  View,
  Delete
} from '@element-plus/icons-vue'
import api from '../api'
import PlanStatusTag from '../components/plans/PlanStatusTag.vue'
import PlanProgress from '../components/plans/PlanProgress.vue'
import CreatePlanDialog from '../components/plans/CreatePlanDialog.vue'
import PlanDetailDrawer from '../components/plans/PlanDetailDrawer.vue'
import BatchExecuteConfirm from '../components/plans/BatchExecuteConfirm.vue'
import { formatTime, formatRelativeTime } from '@/utils/formatter'

// 数据状态
const loading = ref(false)
const tableData = ref([])
const selectedPlans = ref([])
const executingPlan = ref(null)

// 分页
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 筛选表单
const filterForm = reactive({
  search: '',
  status: '',
  plan_type: ''
})

// 统计信息
const stats = reactive({
  total: 0,
  running: 0,
  completed: 0,
  failed: 0,
  waiting: 0,
  scheduled: 0
})

// 对话框状态
const createDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const batchConfirmVisible = ref(false)
const selectedPlanId = ref(null)

// 组织统计项数据
const statItems = computed(() => [
  {
    type: 'total',
    icon: List,
    value: stats.total,
    label: '总计划数',
    clickHandler: () => filterByStatus('')
  },
  {
    type: 'running',
    icon: Loading,
    value: stats.running,
    label: '执行中',
    clickHandler: () => filterByStatus('running')
  },
  {
    type: 'completed',
    icon: CircleCheck,
    value: stats.completed,
    label: '已完成',
    clickHandler: () => filterByStatus('completed')
  },
  {
    type: 'failed',
    icon: CircleClose,
    value: stats.failed,
    label: '已失败',
    clickHandler: () => filterByStatus('failed')
  },
  {
    type: 'waiting',
    icon: Clock,
    value: stats.waiting,
    label: '等待中',
    clickHandler: () => filterByStatus('waiting')
  },
  {
    type: 'scheduled',
    icon: AlarmClock,
    value: stats.scheduled,
    label: '定时计划',
    clickHandler: () => filterByType('scheduled')
  }
])

// 获取测试计划列表
const fetchTestPlans = async () => {
  try {
    loading.value = true

    const params = {
      page: pagination.current,
      per_page: pagination.size,
      ...filterForm
    }

    const response = await api.getTestPlans(params)

    if (response.success) {
      tableData.value = response.plans
      pagination.total = response.total

      // 更新统计信息
      updateStats(response.plans)
    }
  } catch (error) {
    console.error('获取测试计划失败:', error)
    ElMessage.error('获取计划列表失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStats = (plans) => {
  // 重置统计
  Object.keys(stats).forEach(key => {
    stats[key] = 0
  })

  // 重新统计
  plans.forEach(plan => {
    stats.total++

    // 按状态统计
    if (stats.hasOwnProperty(plan.status)) {
      stats[plan.status]++
    }

    // 按类型统计
    if (plan.plan_type === 'scheduled') {
      stats.scheduled++
    }
  })
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  fetchTestPlans()
}

// 刷新
const handleRefresh = () => {
  fetchTestPlans()
}

// 按状态筛选
const filterByStatus = (status) => {
  filterForm.status = status
  handleSearch()
}

// 按类型筛选
const filterByType = (plan_type) => {
  filterForm.plan_type = plan_type
  handleSearch()
}

// 选择变化
const handleSelectionChange = (val) => {
  selectedPlans.value = val
}

// 表格行点击
const handleRowClick = (row) => {
  selectedPlanId.value = row.id
  detailDrawerVisible.value = true
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  fetchTestPlans()
}

// 当前页变化
const handleCurrentChange = (page) => {
  pagination.current = page
  fetchTestPlans()
}

// 创建计划
const handleCreatePlan = () => {
  createDialogVisible.value = true
}

// 创建成功回调
const handleCreateSuccess = () => {
  fetchTestPlans()
  ElMessage.success('测试计划创建成功')
}

// 执行单个计划
const handleExecutePlan = async (plan) => {
  try {
    executingPlan.value = plan.id

    await ElMessageBox.confirm(
        `确定要执行计划 "${plan.name}" 吗？`,
        '执行确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    // 这里调用执行计划的API
    // 由于后端API目前只支持创建和执行自定义计划，需要调整
    // 我们先更新计划状态为执行中
    const index = tableData.value.findIndex(item => item.id === plan.id)
    if (index !== -1) {
      tableData.value[index].status = 'running'
    }

    // 在实际项目中，这里应该调用执行计划的API
    ElMessage.success('计划已开始执行')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行计划失败:', error)
      ElMessage.error('执行计划失败')
    }
  } finally {
    executingPlan.value = null
  }
}

// 查看详情
const handleViewDetail = (row) => {
  selectedPlanId.value = row.id
  detailDrawerVisible.value = true
}

// 删除计划
const handleDeletePlan = async (plan) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除计划 "${plan.name}" 吗？删除后无法恢复。`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'error'
        }
    )

    // 这里调用删除计划的API
    // 由于后端API目前没有删除计划，我们先模拟删除
    const index = tableData.value.findIndex(item => item.id === plan.id)
    if (index !== -1) {
      tableData.value.splice(index, 1)
      pagination.total--
      ElMessage.success('计划删除成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除计划失败:', error)
      ElMessage.error('删除计划失败')
    }
  }
}

// 批量执行
const handleExecuteAll = () => {
  if (selectedPlans.value.length === 0) {
    ElMessage.warning('请先选择要执行的计划')
    return
  }

  batchConfirmVisible.value = true
}

// 批量执行成功回调
const handleBatchExecuteSuccess = () => {
  fetchTestPlans()
  selectedPlans.value = []
  ElMessage.success('批量执行已开始')
}

// 组件挂载
onMounted(() => {
  fetchTestPlans()
})
</script>

<style scoped>
.test-plans-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 40px);
  box-sizing: border-box;
}

.toolbar-card {
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统计区域修复 */
.stats-wrapper {
  margin-bottom: 24px;
  padding: 0 4px; /* 补偿栅格系统的 gutter */
}

.stats-row {
  margin: 0 !important; /* 重置 Element Plus 的默认 margin */
  display: flex;
  flex-wrap: wrap;
}

.stat-col {
  display: flex;
  margin-bottom: 16px;
  box-sizing: border-box;
}

.stat-col > .stat-item {
  width: 100%;
}

.stat-item {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100px; /* 固定高度 */
  box-sizing: border-box;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #409eff;
}

/* 统计图标样式 */
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}

/* 不同类型的统计图标背景色 */
.total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.running .stat-icon {
  background: linear-gradient(135deg, #1890ff 0%, #69c0ff 100%);
}

.completed .stat-icon {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
}

.failed .stat-icon {
  background: linear-gradient(135deg, #f5222d 0%, #ff4d4f 100%);
}

.waiting .stat-icon {
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
}

.scheduled .stat-icon {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

/* 统计信息样式 */
.stat-info {
  flex: 1;
  min-width: 0; /* 防止文本溢出 */
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  line-height: 1.2;
}

/* 表格区域 */
.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  position: relative;
  z-index: 1; /* 确保在统计区域之上 */
}

.table-container {
  position: relative;
  min-height: 400px;
}

/* 表格单元格样式 */
.plan-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.plan-type-tag {
  min-width: 40px;
  text-align: center;
}

.plan-name {
  font-weight: 500;
  color: #1890ff;
  cursor: pointer;
}

.plan-name:hover {
  text-decoration: underline;
}

.creator-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.creator-avatar {
  background: #1890ff;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.creator-name {
  font-size: 14px;
  color: #333;
}

.time-cell {
  font-size: 12px;
  color: #666;
}

.stats-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.stat-passed {
  color: #52c41a;
  font-weight: bold;
}

.stat-failed {
  color: #f5222d;
  font-weight: bold;
}

.stat-total {
  color: #1890ff;
  font-weight: bold;
}

.stat-separator {
  color: #999;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .stat-col {
    width: 25% !important;
    flex: 0 0 auto;
  }
}

@media (max-width: 992px) {
  .stat-col {
    width: 33.3333% !important;
  }

  .stat-item {
    padding: 16px;
    height: 90px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-value {
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  .test-plans-container {
    padding: 12px;
  }

  .toolbar-content {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
    width: 100%;
  }

  .stat-col {
    width: 50% !important;
  }

  .stat-item {
    padding: 12px;
    height: 85px;
    gap: 12px;
  }

  .stat-icon {
    width: 44px;
    height: 44px;
  }

  .stat-icon .el-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stat-col {
    width: 100% !important;
  }

  .toolbar-left,
  .toolbar-right {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left .el-button,
  .toolbar-right .el-button {
    width: 100%;
  }

  .toolbar-right .el-input {
    width: 100% !important;
  }
}
</style>
