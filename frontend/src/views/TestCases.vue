<template>
  <div class="test-cases-container">
    <!-- 筛选工具栏 -->
    <el-card class="filter-card">
      <div class="filter-toolbar">
        <el-form :model="filterForm" inline>
          <el-form-item label="用例状态">
            <el-select
                v-model="filterForm.status"
                placeholder="全部状态"
                clearable
                style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="通过" value="passed" />
              <el-option label="失败" value="failed" />
              <el-option label="未执行" value="not_executed" />
              <el-option label="执行中" value="executing" />
            </el-select>
          </el-form-item>

<!--          <el-form-item label="路径筛选">-->
<!--            <el-cascader-->
<!--                v-model="filterForm.path"-->
<!--                :options="directoryTree"-->
<!--                :props="cascaderProps"-->
<!--                placeholder="选择目录"-->
<!--                clearable-->
<!--                style="width: 200px"-->
<!--            />-->
<!--          </el-form-item>-->

          <el-form-item>
            <el-input
                v-model="filterForm.search"
                placeholder="搜索用例名称或路径"
                prefix-icon="Search"
                style="width: 250px"
                @keyup.enter="handleSearch"
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
              type="success"
              :icon="VideoPlay"
              @click="handleBatchExecute"
              :disabled="selection.length === 0"
          >
            批量执行
          </el-button>
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

    <!-- 统计信息 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-item total" @click="filterByStatus('')">
            <span class="stat-label">总用例数</span>
            <span class="stat-value">{{ total }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item passed" @click="filterByStatus('passed')">
            <span class="stat-label">通过</span>
            <span class="stat-value">{{ statCount.passed }}</span>
            <span class="stat-percent">{{ statPercent.passed }}%</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item failed" @click="filterByStatus('failed')">
            <span class="stat-label">失败</span>
            <span class="stat-value">{{ statCount.failed }}</span>
            <span class="stat-percent">{{ statPercent.failed }}%</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item not-executed" @click="filterByStatus('not_executed')">
            <span class="stat-label">未执行</span>
            <span class="stat-value">{{ statCount.not_executed }}</span>
            <span class="stat-percent">{{ statPercent.not_executed }}%</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 用例表格 -->
    <el-card>
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
              <status-tag :status="row.status" />
            </template>
          </el-table-column>

          <el-table-column prop="avg_duration" label="平均耗时" width="120" sortable>
            <template #default="{ row }">
              <div v-if="row.avg_duration" class="duration-cell">
                {{ formatDuration(row.avg_duration) }}
                <span v-if="row.execution_duration" class="last-duration">
                  (最近: {{ formatDuration(row.execution_duration) }})
                </span>
              </div>
              <span v-else>-</span>
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

          <el-table-column prop="last_modify_time" label="最后修改时间" width="180" sortable>
            <template #default="{ row }">
              <div v-if="row.last_modify_time" class="time-cell">
                {{ formatTime(row.last_modify_time) }}
              </div>
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

          <el-table-column prop="verified_by" label="校验人" width="120">
            <template #default="{ row }">
              <span v-if="row.verified_by" class="verified-by">
                {{ row.verified_by }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                    type="primary"
                    size="small"
                    :icon="VideoPlay"
                    @click.stop="handleExecute(row)"
                    :loading="executingCase === row.id"
                >
                  执行
                </el-button>
                <el-button
                    type="warning"
                    size="small"
                    :icon="Edit"
                    @click.stop="handleEdit(row)"
                >
                  校验
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

    <!-- 用例详情抽屉 -->
    <case-detail-drawer
        v-model="detailDrawerVisible"
        :case-id="selectedCaseId"
        :case-name="selectedCaseName"
        @refresh="handleRefresh"
    />

    <!-- 批量执行对话框 -->
    <batch-execute-dialog
        v-model="batchDialogVisible"
        :selected-cases="selection"
        @success="handleBatchSuccess"
    />

    <!-- 编辑校验对话框 -->
    <edit-case-dialog
        v-model="editDialogVisible"
        :case-data="editingCase"
        @success="handleEditSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  VideoPlay,
  Edit,
  Folder
} from '@element-plus/icons-vue'
import api from '../api'
import StatusTag from '../components/cases/StatusTag.vue'
import CaseDetailDrawer from '../components/cases/CaseDetailDrawer.vue'
import BatchExecuteDialog from '../components/cases/BatchExecuteDialog.vue'
import EditCaseDialog from '../components/cases/EditCaseDialog.vue'
import { formatTime, formatDuration } from '@/utils/formatter'

const route = useRoute()
const router = useRouter()

// 数据状态
const loading = ref(false)
const tableData = ref([])
const directoryTree = ref([])
const selection = ref([])
const executingCase = ref(null)

// 分页
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 筛选表单
const filterForm = reactive({
  status: '',
  path: '',
  search: ''
})

// 统计信息
const statCount = reactive({
  passed: 0,
  failed: 0,
  not_executed: 0,
  executing: 0
})

// 详情抽屉
const detailDrawerVisible = ref(false)
const selectedCaseId = ref(null)
const selectedCaseName = ref(null)

// 批量执行对话框
const batchDialogVisible = ref(false)

// 编辑对话框
const editDialogVisible = ref(false)
const editingCase = ref(null)

// 级联选择器配置
const cascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  checkStrictly: true,
  emitPath: false
}

// 计算统计百分比
const statPercent = computed(() => {
  const total = pagination.total
  return {
    passed: total > 0 ? ((statCount.passed / total) * 100).toFixed(1) : '0',
    failed: total > 0 ? ((statCount.failed / total) * 100).toFixed(1) : '0',
    not_executed: total > 0 ? ((statCount.not_executed / total) * 100).toFixed(1) : '0'
  }
})

// 格式化路径显示
const formatPath = (path) => {
  if (!path) return ''
  const parts = path.split('/')
  if (parts.length > 3) {
    return `.../${parts.slice(-2).join('/')}`
  }
  return path
}

// 获取测试用例列表
const fetchTestCases = async () => {
  try {
    loading.value = true

    const params = {
      page: pagination.current,
      per_page: pagination.size,
      ...filterForm
    }

    // 如果path是数组，取最后一个值
    if (Array.isArray(params.path)) {
      params.path = params.path[params.path.length - 1]
    }

    const response = await api.getTestCases(params)

    if (response.success) {
      tableData.value = response.cases
      pagination.total = response.total

      // 更新统计信息
      updateStats(response)
    }
  } catch (error) {
    console.error('获取测试用例失败:', error)
    ElMessage.error('获取用例列表失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStats = (response) => {
  // 重置统计
  Object.keys(statCount).forEach(key => {
    statCount[key] = 0
  })

  // 重新统计
  statCount.not_executed = response.not_executed
  statCount.failed = response.failed
  statCount.passed = response.passed
  statCount.executing = response.executing
}

// 获取目录树
const fetchDirectoryTree = async () => {
  try {
    const response = await api.getTestCaseStats()
    if (response.success) {
      buildDirectoryTree(response.stats)
    }
  } catch (error) {
    console.error('获取目录树失败:', error)
  }
}

// 构建目录树
const buildDirectoryTree = (stats) => {
  const tree = []
  const pathMap = {}

  stats.forEach(stat => {
    if (!stat.category) return

    const parts = stat.category.split('/')
    let currentPath = ''
    let parentNode = null

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part

      if (!pathMap[currentPath]) {
        const node = {
          value: currentPath,
          label: part,
          children: []
        }

        if (parentNode) {
          parentNode.children.push(node)
        } else {
          tree.push(node)
        }

        pathMap[currentPath] = node
      }

      parentNode = pathMap[currentPath]
    })
  })

  directoryTree.value = tree
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  fetchTestCases()
}

// 重置筛选
const handleReset = () => {
  filterForm.status = ''
  filterForm.path = ''
  filterForm.search = ''
  pagination.current = 1
  fetchTestCases()
}

// 按状态筛选
const filterByStatus = (status) => {
  filterForm.status = status
  handleSearch()
}

// 表格行点击
const handleRowClick = (row) => {
  selectedCaseId.value = row.id
  selectedCaseName.value = row.name
  detailDrawerVisible.value = true
}

// 选择变化
const handleSelectionChange = (val) => {
  selection.value = val
}

// 排序变化
const handleSortChange = ({ prop, order }) => {
  console.log('排序:', prop, order)
  // 这里可以添加排序逻辑，如果需要后端排序可以传递排序参数
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  fetchTestCases()
}

// 当前页变化
const handleCurrentChange = (page) => {
  pagination.current = page
  fetchTestCases()
}

// 刷新
const handleRefresh = () => {
  fetchTestCases()
  fetchDirectoryTree()
}

// 执行单个用例
const handleExecute = async (row) => {
  try {
    executingCase.value = row.id

    await ElMessageBox.confirm(
        `确定要执行用例 "${row.name}" 吗？`,
        '执行确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    // 这里调用执行单个用例的API
    // 由于后端目前只支持批量执行，这里可以创建一个只包含该用例的计划
    const response = await api.executeTestPlan({
      name: `执行用例: ${row.name}`,
      include_paths: [row.relative_path],
      distributed: false
    })

    if (response.success) {
      ElMessage.success('用例已加入执行队列')
      // 更新用例状态为执行中
      const index = tableData.value.findIndex(item => item.id === row.id)
      if (index !== -1) {
        tableData.value[index].status = 'executing'
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行用例失败:', error)
      ElMessage.error('执行用例失败')
    }
  } finally {
    executingCase.value = null
  }
}

// 编辑用例（人工校验）
const handleEdit = (row) => {
  editingCase.value = { ...row }
  editDialogVisible.value = true
}

// 编辑成功回调
const handleEditSuccess = () => {
  fetchTestCases()
  ElMessage.success('用例已更新')
}

// 批量执行
const handleBatchExecute = () => {
  batchDialogVisible.value = true
}

// 批量执行成功回调
const handleBatchSuccess = () => {
  fetchTestCases()
  selection.value = []
  ElMessage.success('批量执行已开始')
}

// 监听路由参数
watch(
    () => route.query,
    (newQuery) => {
      if (newQuery.status) {
        filterForm.status = newQuery.status
      }
      if (newQuery.path) {
        filterForm.path = newQuery.path
      }
      handleSearch()
    },
    { immediate: true }
)

// 组件挂载
onMounted(() => {
  fetchDirectoryTree()
})
</script>

<style scoped>
.test-cases-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 16px;
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

.stats-overview {
  margin-bottom: 16px;
}

.stat-item {
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-item.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-item.passed {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  color: white;
}

.stat-item.failed {
  background: linear-gradient(135deg, #f5222d 0%, #ff4d4f 100%);
  color: white;
}

.stat-item.not-executed {
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  color: white;
}

.stat-label {
  display: block;
  font-size: 14px;
  margin-bottom: 4px;
  opacity: 0.9;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-percent {
  font-size: 12px;
  opacity: 0.8;
}

.table-container {
  position: relative;
  min-height: 400px;
}

.case-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modified-icon {
  color: #faad14;
  font-size: 14px;
}

.case-name {
  font-weight: 500;
  color: #1890ff;
  cursor: pointer;
}

.case-name:hover {
  text-decoration: underline;
}

.path-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
}

.path-icon {
  color: #ffa940;
  font-size: 14px;
}

.path-text {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.duration-cell {
  font-size: 12px;
}

.last-duration {
  color: #999;
  font-size: 11px;
  margin-left: 4px;
}

.time-cell {
  font-size: 12px;
  color: #666;
}

.verified-by {
  color: #52c41a;
  font-weight: 500;
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

@media (max-width: 768px) {
  .filter-toolbar {
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .stat-item {
    margin-bottom: 8px;
  }
}
</style>
