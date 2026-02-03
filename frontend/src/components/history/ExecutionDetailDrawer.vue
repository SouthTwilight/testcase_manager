<template>
  <el-drawer
      v-model="drawerVisible"
      title="执行详情"
      :size="isMobile ? '90%' : '50%'"
      direction="rtl"
      destroy-on-close
  >
    <div v-loading="loading" class="execution-detail">
      <div v-if="executionData" class="detail-content">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <status-tag :status="executionData.status" size="small" />
            </div>
          </template>

          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="执行ID">
              {{ executionData.id }}
            </el-descriptions-item>
            <el-descriptions-item label="用例Hash">
              <el-tag size="small" type="info">
                {{ executionData.case_hash }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="用例名称">
              {{ executionData.case_name || '未知用例' }}
            </el-descriptions-item>
            <el-descriptions-item label="执行时间">
              {{ formatTime(executionData.execution_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="执行人">
              <div class="executor-info">
                <el-avatar :size="24" class="executor-avatar">
                  {{ getAvatarText(executionData.executed_by) }}
                </el-avatar>
                <span>{{ executionData.executed_by || '系统' }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="执行机器">
              <div v-if="executionData.machine_id" class="machine-info">
                <el-icon><Monitor /></el-icon>
                <span>{{ executionData.machine_id }}</span>
              </div>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="执行耗时">
              {{ formatDuration(executionData.duration) }}
            </el-descriptions-item>
            <el-descriptions-item label="所属计划">
              <div v-if="executionData.plan_id" class="plan-info">
                <el-tag
                    size="small"
                    type="info"
                    @click="handleViewPlan(executionData.plan_id)"
                    class="plan-link"
                >
                  {{ executionData.plan_name || `计划 ${executionData.plan_id}` }}
                </el-tag>
              </div>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 执行结果 -->
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>执行结果</span>
            </div>
          </template>

          <div class="result-content">
            <div class="result-status">
              <div class="status-display">
                <status-tag :status="executionData.status" size="large" />
                <div class="status-time">
                  执行于 {{ formatRelativeTime(executionData.execution_time) }}
                </div>
              </div>

              <div v-if="executionData.error_message" class="error-message">
                <h4>错误信息</h4>
                <el-alert
                    :title="executionData.error_message"
                    type="error"
                    :closable="false"
                    show-icon
                />
              </div>

              <div v-if="executionData.stack_trace" class="stack-trace">
                <h4>堆栈跟踪</h4>
                <el-input
                    type="textarea"
                    :value="executionData.stack_trace"
                    :rows="6"
                    readonly
                    resize="none"
                />
              </div>
            </div>

            <div v-if="executionData.result_details" class="result-details">
              <h4>详细结果</h4>
              <el-message
                  :value="parsedResultDetails"
                  :expand-depth="2"
                  copyable
                  boxed
              />
            </div>
          </div>
        </el-card>

        <!-- 执行日志 -->
        <el-card class="logs-card">
          <template #header>
            <div class="card-header">
              <span>执行日志</span>
              <el-button
                  type="text"
                  :icon="Download"
                  @click="handleDownloadLogs"
              >
                下载日志
              </el-button>
            </div>
          </template>

          <div class="logs-content">
            <div v-if="executionData.logs && executionData.logs.length > 0" class="log-entries">
              <div
                  v-for="(log, index) in executionData.logs"
                  :key="index"
                  :class="['log-entry', log.level.toLowerCase()]"
              >
                <div class="log-time">{{ formatTime(log.time, 'HH:mm:ss') }}</div>
                <div class="log-level">{{ log.level }}</div>
                <div class="log-message">{{ log.message }}</div>
              </div>
            </div>
            <div v-else class="empty-logs">
              <el-empty description="暂无执行日志" :image-size="60" />
            </div>
          </div>
        </el-card>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
              type="primary"
              :icon="VideoPlay"
              @click="handleReexecute"
              :loading="reexecuting"
          >
            重新执行
          </el-button>
          <el-button
              type="warning"
              :icon="Edit"
              @click="handleMarkAsVerified"
          >
            标记为已验证
          </el-button>
          <el-button
              v-if="executionData.status === 'failed'"
              type="success"
              :icon="CircleCheck"
              @click="handleMarkAsFixed"
          >
            标记为已修复
          </el-button>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="未找到执行详情" />
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Edit, CircleCheck, Download, Monitor } from '@element-plus/icons-vue'
import StatusTag from '../cases/StatusTag.vue'
import { formatTime, formatRelativeTime, formatDuration } from '@/utils/formatter'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  executionId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const router = useRouter()

// 数据状态
const loading = ref(false)
const executionData = ref(null)
const reexecuting = ref(false)

// 移动端检测
const isMobile = computed(() => {
  return window.innerWidth <= 768
})

// 解析结果详情
const parsedResultDetails = computed(() => {
  if (!executionData.value?.result_details) return {}

  try {
    if (typeof executionData.value.result_details === 'string') {
      return JSON.parse(executionData.value.result_details)
    }
    return executionData.value.result_details
  } catch (e) {
    return { raw: executionData.value.result_details }
  }
})

// 获取头像文本
const getAvatarText = (name) => {
  if (!name) return 'S'
  return name.charAt(0).toUpperCase()
}

// 获取执行详情
const fetchExecutionDetail = async () => {
  if (!props.executionId) return

  try {
    loading.value = true

    // 模拟数据，实际项目中应该调用API
    executionData.value = {
      id: props.executionId,
      case_hash: 'abc123def456',
      case_name: '测试登录功能',
      status: 'failed',
      execution_time: new Date().toISOString(),
      executed_by: 'admin',
      machine_id: 'machine-01',
      duration: 1200,
      plan_id: 1,
      plan_name: '日常回归测试',
      error_message: 'AssertionError: Expected "Welcome" but got "Login failed"',
      stack_trace: 'File "test_login.py", line 45, in test_login\n    assert response.text == "Welcome"',
      result_details: JSON.stringify({
        request: {
          method: 'POST',
          url: '/login',
          data: { username: 'admin', password: 'admin123' }
        },
        response: {
          status_code: 200,
          text: 'Login failed',
          cookies: {}
        },
        screenshots: ['/screenshots/login_failed.png']
      }, null, 2),
      logs: [
        { time: new Date(Date.now() - 3000).toISOString(), level: 'INFO', message: '开始执行测试用例' },
        { time: new Date(Date.now() - 2000).toISOString(), level: 'INFO', message: '发送登录请求' },
        { time: new Date(Date.now() - 1000).toISOString(), level: 'ERROR', message: '登录失败: AssertionError' },
        { time: new Date().toISOString(), level: 'INFO', message: '保存失败截图' }
      ]
    }
  } catch (error) {
    console.error('获取执行详情失败:', error)
    ElMessage.error('获取执行详情失败')
  } finally {
    loading.value = false
  }
}

// 查看计划
const handleViewPlan = (planId) => {
  router.push({
    path: '/test-plans',
    query: { plan_id: planId }
  })
  drawerVisible.value = false
}

// 重新执行
const handleReexecute = async () => {
  try {
    reexecuting.value = true

    // 调用重新执行API
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success('用例已加入执行队列')
  } catch (error) {
    console.error('重新执行失败:', error)
    ElMessage.error('重新执行失败')
  } finally {
    reexecuting.value = false
  }
}

// 标记为已验证
const handleMarkAsVerified = async () => {
  try {
    // 调用验证API
    await new Promise(resolve => setTimeout(resolve, 500))

    executionData.value.status = 'passed'
    ElMessage.success('已标记为已验证')
  } catch (error) {
    console.error('标记失败:', error)
    ElMessage.error('标记失败')
  }
}

// 标记为已修复
const handleMarkAsFixed = async () => {
  try {
    // 调用修复API
    await new Promise(resolve => setTimeout(resolve, 500))

    executionData.value.status = 'passed'
    ElMessage.success('已标记为已修复')
  } catch (error) {
    console.error('标记失败:', error)
    ElMessage.error('标记失败')
  }
}

// 下载日志
const handleDownloadLogs = () => {
  ElMessage.success('日志下载已开始')
}

// 监听executionId变化
watch(() => props.executionId, () => {
  if (props.executionId) {
    fetchExecutionDetail()
  } else {
    executionData.value = null
  }
}, { immediate: true })

// 监听抽屉显示状态
watch(drawerVisible, (val) => {
  if (val && props.executionId) {
    fetchExecutionDetail()
  }
})
</script>

<style scoped>
.execution-detail {
  height: 100%;
  padding: 0 8px;
  overflow-y: auto;
}

.detail-content {
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 80px;
}

.info-card,
.result-card,
.logs-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.executor-info {
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

.machine-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.machine-info .el-icon {
  color: #666;
  font-size: 14px;
}

.plan-info {
  display: flex;
}

.plan-link {
  cursor: pointer;
}

.plan-link:hover {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.result-content {
  padding: 8px 0;
}

.status-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.status-time {
  font-size: 12px;
  color: #666;
}

.error-message {
  margin-bottom: 16px;
}

.error-message h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.stack-trace {
  margin-bottom: 16px;
}

.stack-trace h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.result-details {
  margin-top: 16px;
}

.result-details h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.logs-content {
  padding: 8px 0;
}

.log-entries {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.log-entry {
  padding: 8px 12px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  display: grid;
  grid-template-columns: 80px 60px 1fr;
  gap: 8px;
  align-items: center;
}

.log-entry.info {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.log-entry.warning {
  background: #fffbe6;
  border-left: 3px solid #faad14;
}

.log-entry.error {
  background: #fff2f0;
  border-left: 3px solid #f5222d;
}

.log-entry.debug {
  background: #fafafa;
  border-left: 3px solid #666;
}

.log-time {
  color: #666;
}

.log-level {
  font-weight: bold;
  text-align: center;
}

.log-entry.info .log-level {
  color: #1890ff;
}

.log-entry.warning .log-level {
  color: #faad14;
}

.log-entry.error .log-level {
  color: #f5222d;
}

.log-entry.debug .log-level {
  color: #666;
}

.log-message {
  color: #333;
  word-break: break-all;
}

.empty-logs {
  padding: 20px;
  text-align: center;
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
  .status-display {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .log-entry {
    grid-template-columns: 70px 50px 1fr;
    font-size: 11px;
  }

  .action-buttons {
    flex-direction: column;
    width: calc(100% - 32px);
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
