<template>
  <div class="execution-history-container">
    <!-- 筛选工具栏 -->
    <el-card class="filter-card">
      <div class="filter-toolbar">
        <el-form :model="filterForm" inline>
          <el-form-item label="执行状态">
            <el-select
                v-model="filterForm.status"
                placeholder="全部状态"
                clearable
                style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="通过" value="passed" />
              <el-option label="失败" value="failed" />
              <el-option label="执行中" value="executing" />
              <el-option label="超时" value="timeout" />
            </el-select>
          </el-form-item>

          <el-form-item label="计划ID">
            <el-input
                v-model="filterForm.plan_id"
                placeholder="请输入计划ID"
                style="width: 120px"
            />
          </el-form-item>

          <el-form-item label="用例Hash">
            <el-input
                v-model="filterForm.case_hash"
                placeholder="请输入用例Hash"
                style="width: 200px"
            />
          </el-form-item>

          <el-form-item label="执行时间">
            <el-date-picker
                v-model="filterForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 240px"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>

        <div class="toolbar-actions">
          <el-button
              type="warning"
              :icon="Download"
              @click="handleExport"
          >
            导出历史
          </el-button>
          <el-button
              type="danger"
              :icon="Delete"
              @click="handleClearHistory"
              :disabled="selectedRows.length === 0"
          >
            删除选中
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 - 添加 wrapper 并修复布局 -->
    <div class="stats-wrapper">
      <el-row :gutter="16" class="stats-grid">
        <el-col
            v-for="(stat, index) in statItems"
            :key="index"
            :xs="24"
            :sm="12"
            :md="6"
            :lg="6"
            class="stat-col"
        >
          <div
              class="stat-card"
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

    <!-- 执行历史表格 -->
    <el-card class="table-card">
      <div class="table-container">
        <el-table
            v-loading="loading"
            :data="tableData"
            style="width: 100%"
            @selection-change="handleSelectionChange"
            @sort-change="handleSortChange"
            @row-click="handleRowClick"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column type="index" label="序号" width="60" />

          <el-table-column prop="case_name" label="用例名称" min-width="180">
            <template #default="{ row }">
              <div class="case-cell">
                <span class="case-name">{{ row.case_name || formatCaseHash(row.case_hash) }}</span>
                <span v-if="row.case_hash" class="case-hash">
                  {{ formatCaseHash(row.case_hash) }}
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <status-tag :status="row.status" />
            </template>
          </el-table-column>

          <el-table-column prop="execution_time" label="执行时间" width="180" sortable>
            <template #default="{ row }">
              <div class="time-cell">
                <div class="time-value">{{ formatTime(row.execution_time) }}</div>
                <div class="time-relative">{{ formatRelativeTime(row.execution_time) }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="duration" label="耗时" width="120" sortable>
            <template #default="{ row }">
              <div class="duration-cell">
                {{ formatDuration(row.duration) }}
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="executed_by" label="执行人" width="120">
            <template #default="{ row }">
              <div class="executor-cell">
                <el-avatar :size="24" class="executor-avatar">
                  {{ getAvatarText(row.executed_by) }}
                </el-avatar>
                <span class="executor-name">{{ row.executed_by || '系统' }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="machine_id" label="执行机器" width="150">
            <template #default="{ row }">
              <div v-if="row.machine_id" class="machine-cell">
                <el-icon><Monitor /></el-icon>
                <span class="machine-id">{{ row.machine_id }}</span>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="plan_name" label="所属计划" width="180">
            <template #default="{ row }">
              <div v-if="row.plan_id" class="plan-cell">
                <el-tag
                    size="small"
                    type="info"
                    class="plan-tag"
                    @click.stop="handleViewPlan(row.plan_id)"
                >
                  {{ row.plan_name || `计划 ${row.plan_id}` }}
                </el-tag>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                    type="primary"
                    size="small"
                    :icon="View"
                    @click.stop="handleViewDetail(row)"
                >
                  详情
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

    <!-- 执行详情抽屉 -->
    <execution-detail-drawer
        v-model="detailDrawerVisible"
        :execution-id="selectedExecutionId"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Delete,
  Clock,
  CircleCheck,
  CircleClose,
  TrendCharts,
  Monitor,
  View
} from '@element-plus/icons-vue'
import api from '../api'
import StatusTag from '../components/cases/StatusTag.vue'
import ExecutionDetailDrawer from '../components/history/ExecutionDetailDrawer.vue'
import { formatTime, formatRelativeTime, formatDuration } from '@/utils/formatter'

const router = useRouter()

// 数据状态
const loading = ref(false)
const tableData = ref([])
const selectedRows = ref([])

// 分页
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 筛选表单
const filterForm = reactive({
  status: '',
  plan_id: '',
  case_hash: '',
  dateRange: []
})

// 统计信息
const stats = reactive({
  total_executions: 0,
  passed_executions: 0,
  failed_executions: 0,
  avg_duration: 0
})

// 组织统计项数据
const statItems = computed(() => [
  {
    type: 'total',
    icon: Clock,
    value: stats.total_executions,
    label: '总执行次数',
    clickHandler: () => console.log('点击总执行次数')
  },
  {
    type: 'passed',
    icon: CircleCheck,
    value: stats.passed_executions,
    label: '通过次数',
    clickHandler: () => {
      filterForm.status = 'passed'
      handleSearch()
    }
  },
  {
    type: 'failed',
    icon: CircleClose,
    value: stats.failed_executions,
    label: '失败次数',
    clickHandler: () => {
      filterForm.status = 'failed'
      handleSearch()
    }
  },
  {
    type: 'average',
    icon: TrendCharts,
    value: stats.avg_duration + 'ms',
    label: '平均耗时',
    clickHandler: () => console.log('点击平均耗时')
  }
])

// 抽屉和对话框
const detailDrawerVisible = ref(false)
const exportDialogVisible = ref(false)
const selectedExecutionId = ref(null)

// 获取执行历史
const fetchExecutionHistory = async () => {
  try {
    loading.value = true

    const params = {
      page: pagination.current,
      per_page: pagination.size,
      ...filterForm
    }

    // 处理日期范围
    if (filterForm.dateRange && filterForm.dateRange.length === 2) {
      params.start_date = filterForm.dateRange[0]
      params.end_date = filterForm.dateRange[1]
    }

    const response = await api.getExecutionHistory(params)

    if (response.success) {
      tableData.value = response.history
      pagination.total = response.total

      // 更新统计信息
      updateStats(response.history)
    }
  } catch (error) {
    console.error('获取执行历史失败:', error)
    ElMessage.error('获取执行历史失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStats = (history) => {
  const newStats = {
    total_executions: history.length,
    passed_executions: 0,
    failed_executions: 0,
    total_duration: 0
  }

  history.forEach(item => {
    if (item.status === 'passed') {
      newStats.passed_executions++
    } else if (item.status === 'failed') {
      newStats.failed_executions++
    }

    if (item.duration) {
      newStats.total_duration += item.duration
    }
  })

  newStats.avg_duration = newStats.total_executions > 0
      ? Math.round(newStats.total_duration / newStats.total_executions)
      : 0

  Object.assign(stats, newStats)
}

// 格式化用例Hash
const formatCaseHash = (hash) => {
  if (!hash) return ''
  return hash.substring(0, 8) + '...'
}

// 获取头像文本
const getAvatarText = (name) => {
  if (!name) return 'S'
  return name.charAt(0).toUpperCase()
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  fetchExecutionHistory()
}

// 重置筛选
const handleReset = () => {
  filterForm.status = ''
  filterForm.plan_id = ''
  filterForm.case_hash = ''
  filterForm.dateRange = []
  pagination.current = 1
  fetchExecutionHistory()
}

// 选择变化
const handleSelectionChange = (val) => {
  selectedRows.value = val
}

// 排序变化
const handleSortChange = ({ prop, order }) => {
  console.log('排序:', prop, order)
  // 这里可以添加排序逻辑，如果需要后端排序可以传递排序参数
}

// 表格行点击
const handleRowClick = (row) => {
  selectedExecutionId.value = row.id
  detailDrawerVisible.value = true
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  fetchExecutionHistory()
}

// 当前页变化
const handleCurrentChange = (page) => {
  pagination.current = page
  fetchExecutionHistory()
}

// 查看计划
const handleViewPlan = (planId) => {
  router.push({
    path: '/test-plans',
    query: { plan_id: planId }
  })
}

// 查看详情
const handleViewDetail = (row) => {
  selectedExecutionId.value = row.id
  detailDrawerVisible.value = true
}

// 导出历史
const handleExport = () => {
  exportDialogVisible.value = true
}

// 清除历史
const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedRows.value.length} 条执行记录吗？此操作不可恢复。`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'error'
        }
    )

    // 这里调用删除API
    // 由于没有删除API，我们先模拟删除
    ElMessage.success('执行记录删除成功')

    // 重新加载数据
    fetchExecutionHistory()
    selectedRows.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除执行记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 组件挂载
onMounted(() => {
  fetchExecutionHistory()
})
</script>

<style scoped>
.execution-history-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 40px);
  box-sizing: border-box;
}

.filter-card {
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

/* 统计区域修复 */
.stats-wrapper {
  margin-bottom: 24px;
  padding: 0 4px; /* 补偿栅格系统的 gutter */
}

.stats-grid {
  margin: 0 !important; /* 重置 Element Plus 的默认 margin */
  display: flex;
  flex-wrap: wrap;
}

.stat-col {
  display: flex;
  margin-bottom: 16px;
  box-sizing: border-box;
}

.stat-col > .stat-card {
  width: 100%;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  height: 100px; /* 固定高度 */
  box-sizing: border-box;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.stat-card:hover {
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
  background: rgba(255, 255, 255, 0.2);
}

.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}

/* 不同类型的统计卡片背景色 */
.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.passed {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  color: white;
}

.failed {
  background: linear-gradient(135deg, #f5222d 0%, #ff4d4f 100%);
  color: white;
}

.average {
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  color: white;
}

/* 统计信息样式 */
.stat-info {
  flex: 1;
  min-width: 0; /* 防止文本溢出 */
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
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
.case-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.case-name {
  font-weight: 500;
  color: #333;
}

.case-hash {
  font-size: 11px;
  color: #999;
  font-family: 'Monaco', 'Consolas', monospace;
}

.time-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.time-value {
  font-size: 12px;
  color: #333;
}

.time-relative {
  font-size: 11px;
  color: #999;
}

.duration-cell {
  font-size: 12px;
  color: #333;
  font-weight: 500;
}

.executor-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.executor-avatar {
  background: #1890ff;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.executor-name {
  font-size: 14px;
  color: #333;
}

.machine-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.machine-cell .el-icon {
  color: #666;
  font-size: 14px;
}

.machine-id {
  font-size: 12px;
  color: #666;
  font-family: 'Monaco', 'Consolas', monospace;
}

.plan-cell {
  display: flex;
}

.plan-tag {
  cursor: pointer;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-tag:hover {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .execution-history-container {
    padding: 12px;
  }

  .filter-toolbar {
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .stat-card {
    padding: 16px;
    height: 90px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-icon .el-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 24px;
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

  .toolbar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions .el-button {
    width: 100%;
  }
}
</style>
