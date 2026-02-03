<template>
  <div class="path-selection">
    <!-- 筛选工具栏 -->
    <el-card class="filter-card">
      <div class="filter-toolbar">
        <el-form :model="filterForm" inline class="compact-form">
          <el-form-item label="用例状态">
            <el-select
                v-model="filterForm.status"
                placeholder="全部状态"
                clearable
                style="width: 100px"
            >
            <el-option label="全部" value="" />
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
            <el-option label="未执行" value="not_executed" />
            <el-option label="执行中" value="executing" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-input
                v-model="filterForm.search"
                placeholder="搜索用例"
                prefix-icon="Search"
                style="width: 180px"
            @keyup.enter="handleSearch"
            size="small"
            />
          </el-form-item>

          <el-form-item class="form-buttons">
            <el-button
                type="primary"
                @click="handleSearch"
                size="small"
                style="padding: 5px 10px; min-width: 60px"
            >
              <el-icon size="14"><Search /></el-icon>
              搜索
            </el-button>
            <el-button
                @click="handleReset"
                size="small"
                style="padding: 5px 10px; min-width: 60px"
            >
              <el-icon size="14"><Refresh /></el-icon>
              重置
            </el-button>
            <el-button
                type="info"
                @click="handleRefresh"
                :loading="loading"
                size="small"
                style="padding: 5px 10px; min-width: 60px"
            >
              <el-icon size="14"><Refresh /></el-icon>
              刷新
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 用例表格 -->
    <el-card class="table-card">
      <div class="table-container">
        <el-table
            v-loading="loading"
            :data="tableData"
            style="width: 100%"
            row-key="id"
            @selection-change="handleSelectionChange"
            @sort-change="handleSortChange"
            @row-click="handleRowClick"
            ref="tableRef"
        >
          <el-table-column
              type="selection"
              width="55"
              :reserve-selection="true"
          />
          <el-table-column type="index" label="序号" width="60" />

          <el-table-column prop="name" label="用例名称" min-width="200">
            <template #default="{ row }">
              <div class="case-name-cell">
                <el-icon v-if="row.is_manually_modified" class="modified-icon">
                  <Edit />
                </el-icon>
                <span class="case-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="relative_path" label="路径" min-width="200">
            <template #default="{ row }">
              <div class="path-cell">
                <el-icon class="path-icon"><Folder /></el-icon>
                <span class="path-text" :title="row.relative_path">
                  {{ formatPath(row.relative_path) }}
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="last_execution_time" label="最后执行时间" width="180" sortable>
            <template #default="{ row }">
              <div v-if="row.last_execution_time" class="time-cell">
                {{ formatTime(row.last_execution_time) }}
              </div>
              <span v-else>从未执行</span>
            </template>
          </el-table-column>

          <el-table-column prop="total_executions" label="执行次数" width="100" sortable>
            <template #default="{ row }">
              <el-tag v-if="row.total_executions > 0" type="info">
                {{ row.total_executions }}
              </el-tag>
              <span v-else>0</span>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, defineEmits, defineProps, watch, nextTick } from 'vue'
import { Search, Refresh, Edit, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from "@/api"
import { formatTime, formatDuration } from '@/utils/formatter'
const props = defineProps({
  // 外部传入的已选用例（用于恢复选中状态）
  externalSelectedCases: {
    type: Array,
    default: () => []
  }
})
const emit = defineEmits([
  'update:selected-cases',
  'search',
  'reset',
  'refresh',
  'execute',
  'edit',
  'batch-execute'
])
// 表格引用
const tableRef = ref()
// 筛选表单
const filterForm = reactive({
  status: '',
  search: ''
})
// 加载状态
const loading = ref(false)
// 用例数据
const tableData = ref([])
// 分页
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})
// 统计信息
const statCount = reactive({
  passed: 0,
  failed: 0,
  not_executed: 0,
  executing: 0
})
// 【核心修改】全局维护的选中用例列表（不仅限于当前页）
const selection = ref([])
// 状态映射
const statusMap = {
  'passed': { text: '通过', type: 'success' },
  'failed': { text: '失败', type: 'danger' },
  'not_executed': { text: '未执行', type: 'info' },
  'executing': { text: '执行中', type: 'warning' }
}
// 获取状态标签类型
const getStatusTagType = (status) => {
  return statusMap[status]?.type || 'info'
}
// 获取状态文本
const getStatusText = (status) => {
  return statusMap[status]?.text || status
}
// 格式化路径显示
const formatPath = (path) => {
  if (!path) return ''
  const parts = path.split('/')
  if (parts.length > 3) {
    return `.../${parts.slice(-2).join('/')}`
  }
  return path
}
// 防抖标志，用于处理selection-change多次触发问题
let isSelectionChanging = false
// 加载测试用例
const loadTestCases = async (params = {}) => {
  try {
    loading.value = true
    const requestParams = {
      page: pagination.current,
      per_page: pagination.size,
      status: filterForm.status || '',
      search: filterForm.search || '',
      ...params
    }
    const response = await api.getTestCases(requestParams)
    if (response.success) {
      tableData.value = response.cases || []
      pagination.total = response.total || 0
      // 更新统计信息
      if (response) {
        statCount.passed = response.passed || 0
        statCount.failed = response.failed || 0
        statCount.not_executed = response.not_executed || 0
        statCount.executing = response.executing || 0
      }
      // 【关键修改】
      // 移除了这里的 restoreSelection() 调用
      // 因为开启了 reserve-selection，el-table 会自动根据 row-key 处理翻页时的勾选状态。
      // 手动调用 clearSelection 会破坏表格内部的跨页选中记忆。
    }
  } catch (error) {
    console.error('获取测试用例失败:', error)
    ElMessage.error('获取用例列表失败')
  } finally {
    loading.value = false
  }
}
// 恢复选中状态（仅用于外部数据强制同步时，如父组件点击“清除”）
const restoreSelection = async () => {
  await nextTick()
  if (tableRef.value && tableRef.value.clearSelection) {
    try {
      // 设置标志，避免触发handleSelectionChange
      isSelectionChanging = true
      // 清空当前表格 UI 选中状态
      tableRef.value.clearSelection()
      // 根据 selection (全局列表) 重新设置当前页的选中状态
      if (selection.value.length > 0) {
        tableData.value.forEach(row => {
          // 检查当前行是否在全局选中列表中
          const isSelected = selection.value.some(item => item.id === row.id)
          if (isSelected) {
            tableRef.value.toggleRowSelection(row, true)
          }
        })
      }
    } catch (error) {
      console.warn('恢复选中状态时出错:', error)
    } finally {
      // 恢复标志
      setTimeout(() => {
        isSelectionChanging = false
      }, 100)
    }
  }
}
// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  loadTestCases()
}
// 处理重置
const handleReset = () => {
  filterForm.status = ''
  filterForm.search = ''
  pagination.current = 1
  loadTestCases()
}
// 表格行点击
const handleRowClick = (row) => {
  emit('view-case', row)
}
// 【核心修复】选择变化处理
const handleSelectionChange = (val) => {
  // 如果是恢复选中状态期间触发的，忽略
  if (isSelectionChanging) {
    return
  }
  // 防抖处理，避免短时间内多次触发
  clearTimeout(window.selectionChangeTimer)
  window.selectionChangeTimer = setTimeout(() => {
    // 1. 获取当前页所有数据的 ID 集合
    const currentPageIds = new Set(tableData.value.map(row => row.id))
    // 2. 从旧的全局 selection 中，剔除掉当前页的所有数据
    //    因为 val (当前页选中项) 代表了当前页最新的选择状态
    const otherPagesSelection = selection.value.filter(item => !currentPageIds.has(item.id))
    // 3. 合并：不在当前页的旧数据 + 当前页新选中的数据
    const newSelection = [...otherPagesSelection, ...val]
    // 4. 更新全局状态
    selection.value = newSelection
    // 5. 通知父组件
    emit('update:selected-cases', newSelection)
  }, 50)
}
// 排序变化
const handleSortChange = ({ prop, order }) => {
  console.log('排序:', prop, order)
  // 这里可以添加排序逻辑
}
// 分页大小变化
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  loadTestCases()
}
// 当前页变化
const handleCurrentChange = (page) => {
  pagination.current = page
  loadTestCases()
}
// 刷新
const handleRefresh = () => {
  loadTestCases()
}
// 设置选中的用例（供父组件调用）
const setSelectedCases = (cases) => {
  selection.value = cases
  restoreSelection()
}
// 清空选中（供父组件调用）
const clearSelection = () => {
  selection.value = []
  if (tableRef.value && tableRef.value.clearSelection) {
    tableRef.value.clearSelection()
  }
}
// 初始化
const init = () => {
  loadTestCases()
}
// 【关键修改】监听外部传入的已选用例
// 只有当父组件主动改变数据（如点击清空按钮）时，这里才会触发并同步 UI
watch(() => props.externalSelectedCases, (newCases) => {
  // 简单的深比较，避免不必要的重复赋值（如果引用未变但内容变了，deep: true 会捕捉）
  // 如果外部传入的数组与当前 selection 不一致，则同步
  if (JSON.stringify(newCases) !== JSON.stringify(selection.value)) {
    selection.value = newCases
    restoreSelection()
  }
}, { deep: true })
// 组件挂载
onMounted(() => {
  init()
})
defineExpose({
  init,
  handleSearch,
  handleReset,
  handleRefresh,
  setSelectedCases,
  clearSelection
})
</script>

<style scoped>
.path-selection {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.filter-card {
  margin-bottom: 8px;
  flex-shrink: 0;
}

.filter-card :deep(.el-card__body) {
  padding: 12px 16px !important;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.compact-form {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  width: 100%;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
  flex-shrink: 0;
}

.compact-form :deep(.el-form-item__label) {
  padding: 0 8px 0 0;
  height: 32px;
  line-height: 32px;
  font-size: 13px;
}

.form-buttons {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* 调整按钮间距和大小 */
.form-buttons :deep(.el-button) {
  padding: 6px 12px;
  font-size: 12px;
  min-width: 60px;
}

/* 调整图标大小 */
.form-buttons :deep(.el-icon) {
  margin-right: 4px;
  font-size: 14px;
}

/* 表格卡片样式保持不变 */
.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 0;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 修改表格容器高度控制 */
:deep(.el-table) {
  flex: 1;
  overflow: hidden;
  height: calc(100% - 40px);
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  height: calc(100% - 20px);
}

:deep(.el-card__body) {
  padding: 12px !important;
}

:deep(.el-table__body) {
  min-width: 100%;
}

/* 确保分页器始终可见 */
:deep(.el-pagination) {
  padding: 10px 0;
}

.pagination-container {
  margin-top: 12px;
  flex-shrink: 0;
  padding: 8px 0;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

.case-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modified-icon {
  color: #e6a23c;
}

.path-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.path-icon {
  color: #409eff;
}

.path-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.duration-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.last-duration {
  font-size: 12px;
  color: #909399;
}

.time-cell {
  font-size: 13px;
  color: #606266;
}

.verified-by {
  color: #409eff;
  font-weight: 500;
}

/* 调整搜索输入框样式 */
:deep(.el-input) {
  font-size: 13px;
}

:deep(.el-input__wrapper) {
  padding: 0 11px;
}
</style>
