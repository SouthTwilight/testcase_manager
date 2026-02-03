<template>
  <el-drawer
      v-model="drawerVisible"
      title="用例详情"
      :size="isMobile ? '90%' : '50%'"
      direction="rtl"
      destroy-on-close
  >
    <div v-loading="loading" class="case-detail">
      <div v-if="caseData" class="detail-content">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h3 class="section-title">基本信息</h3>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="用例名称">
              <span class="case-name">{{ caseData.name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="用例Hash">
              <el-tag size="small" type="info">
                {{ caseData.case_hash }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="路径">
              <div class="path-display">
                <el-icon><Folder /></el-icon>
                <span>{{ caseData.relative_path }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="文件修改时间">
              {{ formatTime(caseData.file_mtime) }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(caseData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后修改时间">
              {{ formatTime(caseData.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 执行状态 -->
        <div class="detail-section">
          <h3 class="section-title">执行状态</h3>
          <div class="status-display">
            <div class="status-card">
              <div class="status-header">
                <status-tag :status="caseData.status" size="large" />
                <el-button
                    v-if="caseData.status === 'failed'"
                    type="primary"
                    size="small"
                    @click="handleRerun"
                    :loading="rerunning"
                >
                  重新执行
                </el-button>
              </div>

              <div class="status-details">
                <div class="detail-item">
                  <span class="label">最后执行时间:</span>
                  <span class="value">
                    {{ caseData.last_execution_time ? formatTime(caseData.last_execution_time) : '从未执行' }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="label">执行次数:</span>
                  <span class="value">{{ caseData.total_executions }}</span>
                </div>
                <div v-if="caseData.avg_duration" class="detail-item">
                  <span class="label">平均耗时:</span>
                  <span class="value">{{ formatDuration(caseData.avg_duration) }}</span>
                </div>
                <div v-if="caseData.execution_duration" class="detail-item">
                  <span class="label">最近耗时:</span>
                  <span class="value">{{ formatDuration(caseData.execution_duration) }}</span>
                </div>
                <div v-if="caseData.verified_by" class="detail-item">
                  <span class="label">校验人:</span>
                  <span class="value verified">{{ caseData.verified_by }}</span>
                </div>
                <div v-if="caseData.verified_at" class="detail-item">
                  <span class="label">校验时间:</span>
                  <span class="value">{{ formatTime(caseData.verified_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 校验信息 -->
        <div v-if="caseData.verification_notes || caseData.result_details" class="detail-section">
          <h3 class="section-title">校验信息</h3>
          <div class="verification-info">
            <div v-if="caseData.verification_notes" class="notes">
              <h4>校验说明</h4>
              <el-card class="notes-card">
                <div class="notes-content">{{ caseData.verification_notes }}</div>
              </el-card>
            </div>
            <div v-if="caseData.result_details" class="details">
              <h4>详细结果</h4>
              <el-card class="details-card">
                <div class="details-content">
                  <pre>{{ formatResultDetails(caseData.result_details) }}</pre>
                </div>
              </el-card>
            </div>
          </div>
        </div>

        <!-- 执行历史 -->
        <div class="detail-section">
          <h3 class="section-title">执行历史</h3>
          <execution-history :case-hash="caseData.case_hash" />
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
              type="warning"
              :icon="Edit"
              @click="handleEdit"
          >
            人工校验
          </el-button>
          <el-button
              type="primary"
              :icon="VideoPlay"
              @click="handleExecute"
              :loading="executing"
          >
            执行用例
          </el-button>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="未找到用例信息" />
      </div>
    </div>
  </el-drawer>

  <!-- 编辑弹窗 -->
  <edit-case-dialog
      v-model="editDialogVisible"
      :case-data="caseData"
      @success="handleEditSuccess"
  />
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, Edit, VideoPlay } from '@element-plus/icons-vue'
import api from '../../api'
import StatusTag from './StatusTag.vue'
import ExecutionHistory from '../../views/ExecutionHistory.vue'
import EditCaseDialog from './EditCaseDialog.vue'
import { formatTime, formatDuration } from '@/utils/formatter'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  caseId: {
    type: Number,
    default: null
  },
  caseName: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 响应式数据
const loading = ref(false)
const caseData = ref(null)
const rerunning = ref(false)
const executing = ref(false)
const editDialogVisible = ref(false)

// 移动端检测
const isMobile = computed(() => {
  return window.innerWidth <= 768
})

// 格式化结果详情
const formatResultDetails = (details) => {
  try {
    if (typeof details === 'string') {
      details = JSON.parse(details)
    }
    return JSON.stringify(details, null, 2)
  } catch (e) {
    return details
  }
}

// 获取用例详情
const fetchCaseDetail = async () => {
  if (!props.caseId) return

  try {
    loading.value = true
    // 这里需要添加获取单个用例详情的API
    // 暂时通过获取列表然后过滤的方式
    const response = await api.getTestCases({
      per_page: 1000,
      search: `${props.caseName}`
    })

    if (response.success && response.cases.length > 0) {
      caseData.value = response.cases[0]
    }
  } catch (error) {
    console.error('获取用例详情失败:', error)
    ElMessage.error('获取用例详情失败')
  } finally {
    loading.value = false
  }
}

// 重新执行
const handleRerun = async () => {
  try {
    rerunning.value = true
    await api.executeTestPlan({
      name: `重新执行: ${caseData.value.name}`,
      include_paths: [caseData.value.relative_path],
      distributed: false
    })
    ElMessage.success('用例已加入执行队列')
    // 更新状态为执行中
    caseData.value.status = 'executing'
    emit('refresh')
  } catch (error) {
    console.error('重新执行失败:', error)
    ElMessage.error('重新执行失败')
  } finally {
    rerunning.value = false
  }
}

// 执行用例
const handleExecute = async () => {
  try {
    executing.value = true
    await api.executeTestPlan({
      name: `执行: ${caseData.value.name}`,
      include_paths: [caseData.value.relative_path],
      distributed: false
    })
    ElMessage.success('用例已加入执行队列')
    caseData.value.status = 'executing'
    emit('refresh')
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error('执行失败')
  } finally {
    executing.value = false
  }
}

// 编辑用例
const handleEdit = () => {
  editDialogVisible.value = true
}

// 编辑成功
const handleEditSuccess = () => {
  fetchCaseDetail()
  emit('refresh')
  ElMessage.success('用例已更新')
}

// 监听caseId变化
watch(() => props.caseId, () => {
  if (props.caseId) {
    fetchCaseDetail()
  } else {
    caseData.value = null
  }
}, { immediate: true })

// 监听抽屉显示状态
watch(drawerVisible, (val) => {
  if (val && props.caseId) {
    fetchCaseDetail()
  }
})
</script>

<style scoped>
.case-detail {
  height: 100%;
  padding: 0 16px;
  overflow-y: auto;
}

.detail-content {
  max-width: 800px;
  margin: 0 auto;
}

.detail-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  color: #333;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.case-name {
  font-weight: bold;
  color: #1890ff;
}

.path-display {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
}

.status-display {
  margin-top: 12px;
}

.status-card {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.status-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item .label {
  font-size: 12px;
  color: #999;
}

.detail-item .value {
  font-size: 14px;
  color: #333;
}

.detail-item .value.verified {
  color: #52c41a;
  font-weight: 500;
}

.verification-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.verification-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.notes-card,
.details-card {
  background: #fafafa;
  border: none;
}

.notes-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.details-content {
  max-height: 300px;
  overflow-y: auto;
}

.details-content pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

@media (max-width: 768px) {
  .status-details {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
