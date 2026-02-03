<!-- PlanCreationDialog.vue -->
<template>
  <el-dialog
      v-model="dialogVisible"
      title="创建测试计划"
      width="1000px"
      :before-close="handleClose"
      destroy-on-close
  >
  <el-steps :active="activeStep" finish-status="success" class="plan-steps">
    <el-step title="计划类型" />
    <el-step title="计划配置" />
    <el-step title="用例选择" />
    <el-step title="确认信息" />
  </el-steps>

  <div class="step-content">
    <!-- 步骤1: 计划类型 -->
    <div v-if="activeStep === 0" class="step-panel">
      <h3 class="step-title">选择计划类型</h3>
      <div class="plan-type-options">
        <div
            v-for="type in planTypes"
            :key="type.value"
            :class="['plan-type-card', { active: form.plan_type === type.value }]"
            @click="selectPlanType(type.value)"
        >
          <div class="type-icon">
            <el-icon :size="32" :color="form.plan_type === type.value ? type.color : '#666'">
              <component :is="type.icon" />
            </el-icon>
          </div>
          <div class="type-info">
            <h4 class="type-name">{{ type.name }}</h4>
            <p class="type-desc">{{ type.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤2: 计划配置 -->
    <div v-else-if="activeStep === 1" class="step-panel">
      <h3 class="step-title">计划配置</h3>

      <el-form
          ref="configFormRef"
          :model="form"
          :rules="configRules"
          label-width="120px"
          label-position="top"
      >
        <el-form-item label="计划名称" prop="name">
          <el-input
              v-model="form.name"
              :placeholder="planNamePlaceholder"
          />
        </el-form-item>

        <el-form-item v-if="form.plan_type === 'manual'" label="执行方式" prop="distributed">
          <el-radio-group v-model="form.distributed">
            <el-radio :label="false">本地执行</el-radio>
            <el-radio :label="true">分布式执行</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.plan_type === 'scheduled'" label="定时设置" required>
          <div class="scheduler-settings">
            <el-select v-model="form.schedule_type" placeholder="选择调度类型">
              <el-option label="每天" value="daily" />
              <el-option label="每周" value="weekly" />
              <el-option label="每月" value="monthly" />
              <el-option label="自定义Cron表达式" value="cron" />
            </el-select>

            <div v-if="form.schedule_type === 'daily'" class="time-picker">
              <span class="label">执行时间:</span>
              <el-time-picker
                  v-model="form.schedule_time"
                  placeholder="选择时间"
                  format="HH:mm"
                  value-format="HH:mm"
              />
            </div>

            <div v-if="form.schedule_type === 'weekly'" class="weekly-settings">
              <span class="label">执行时间:</span>
              <el-time-picker
                  v-model="form.schedule_time"
                  placeholder="选择时间"
                  format="HH:mm"
                  value-format="HH:mm"
                  style="margin-right: 16px"
              />
              <el-checkbox-group v-model="form.week_days">
                <el-checkbox label="1">周一</el-checkbox>
                <el-checkbox label="2">周二</el-checkbox>
                <el-checkbox label="3">周三</el-checkbox>
                <el-checkbox label="4">周四</el-checkbox>
                <el-checkbox label="5">周五</el-checkbox>
                <el-checkbox label="6">周六</el-checkbox>
                <el-checkbox label="0">周日</el-checkbox>
              </el-checkbox-group>
            </div>

            <div v-if="form.schedule_type === 'cron'" class="cron-settings">
              <el-input
                  v-model="form.cron_expression"
                  placeholder="输入Cron表达式，如: 0 23 * * *"
              />
              <div class="cron-examples">
                <span class="example-label">示例:</span>
                <el-tag
                    v-for="example in cronExamples"
                    :key="example.value"
                    size="small"
                    type="info"
                    @click="form.cron_expression = example.value"
                    class="cron-example"
                >
                  {{ example.label }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="优先级设置">
          <el-checkbox-group v-model="form.priorities">
            <el-checkbox label="failed">优先执行失败用例</el-checkbox>
            <el-checkbox label="not_executed">优先执行未执行用例</el-checkbox>
            <el-checkbox label="recently_modified">优先执行最近修改用例</el-checkbox>
            <el-checkbox label="new_cases">优先执行新增用例</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="失败重试">
          <el-input-number
              v-model="form.retry_count"
              :min="0"
              :max="3"
              label="失败重试次数"
          />
          <span class="form-tip">设置为0表示不重试</span>
        </el-form-item>

        <el-form-item label="超时设置（分钟）">
          <el-input-number
              v-model="form.timeout_minutes"
              :min="0"
              :max="480"
              label="超时时间"
          />
          <span class="form-tip">设置为0表示不超时</span>
        </el-form-item>
      </el-form>
    </div>

    <!-- 步骤3: 用例选择 -->
    <div v-else-if="activeStep === 2" class="step-panel">
      <h3 class="step-title">选择测试用例</h3>

      <div class="case-selection-container">
        <!-- 左侧：用例选择 -->
        <div class="selection-left">
          <div class="path-selection-wrapper">
            <path-selection
                v-if="activeStep === 2"
                ref="pathSelectionRef"
                :external-selected-cases="selectedCases"
                @update:selected-cases="handleSelectedCasesUpdate"
            />
          </div>
        </div>

        <!-- 右侧：已选用例预览 -->
        <div class="selection-preview">
          <div class="preview-header">
            <h4>已选择用例 ({{ selectedCases.length }})</h4>
            <el-button
                type="text"
                size="small"
                @click="clearSelectedCases"
                :disabled="selectedCases.length === 0"
            >
              清除
            </el-button>
          </div>
          <div class="preview-content">
            <div v-if="selectedCases.length > 0" class="preview-list">
              <el-tag
                  v-for="caseItem in selectedCases"
                  :key="caseItem.id"
                  type="info"
                  size="small"
                  closable
                  @close="removeCase(caseItem.id)"
                  class="preview-tag"
              >
                {{ caseItem.name }}
              </el-tag>
            </div>
            <div v-else class="empty-preview">
              <el-empty description="请选择测试用例" :image-size="60" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤4: 确认信息 -->
    <div v-else-if="activeStep === 3" class="step-panel">
      <h3 class="step-title">确认计划信息</h3>

      <el-descriptions :column="1" border size="small" class="plan-summary">
        <el-descriptions-item label="计划类型">
          <el-tag :type="planTypeTagType">
            {{ planTypeText }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="计划名称">
          {{ form.name }}
        </el-descriptions-item>
        <el-descriptions-item v-if="form.schedule_type" label="调度设置">
          {{ scheduleText }}
        </el-descriptions-item>
        <el-descriptions-item label="执行方式">
          {{ form.distributed ? '分布式执行' : '本地执行' }}
        </el-descriptions-item>
        <el-descriptions-item label="选择用例数">
          {{ selectedCases.length }} 个
        </el-descriptions-item>
        <el-descriptions-item label="优先级设置">
          <el-tag
              v-for="priority in form.priorities"
              :key="priority"
              size="small"
              type="info"
              class="priority-tag"
          >
            {{ priorityLabels[priority] }}
          </el-tag>
          <span v-if="form.priorities.length === 0">无特殊优先级</span>
        </el-descriptions-item>
        <el-descriptions-item label="失败重试">
          {{ form.retry_count }} 次
        </el-descriptions-item>
        <el-descriptions-item label="超时时间">
          {{ form.timeout_minutes ? `${form.timeout_minutes} 分钟` : '无限制' }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>

  <template #footer>
    <div class="dialog-footer">
      <el-button
          v-if="activeStep > 0"
          @click="prevStep"
          :disabled="loading"
      >
        上一步
      </el-button>
      <el-button
          v-if="activeStep < 3"
          type="primary"
          @click="nextStep"
          :loading="stepLoading"
      >
        {{ activeStep === 2 ? '确认选择' : '下一步' }}
      </el-button>
      <el-button
          v-if="activeStep === 3"
          type="primary"
          @click="handleSubmit"
          :loading="loading"
      >
        创建计划
      </el-button>
      <el-button @click="handleClose" :disabled="loading">
        取消
      </el-button>
    </div>
  </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  AlarmClock,
  MagicStick
} from '@element-plus/icons-vue'
import api from '../../api'
import PathSelection from './PathSelection.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 步骤控制
const activeStep = ref(0)
const stepLoading = ref(false)
const loading = ref(false)
const selectionTab = ref('path')

// 表单引用
const configFormRef = ref()
const pathSelectionRef = ref(null)

// 选中的用例
const selectedCases = ref([])

// 计划类型选项
const planTypes = [
  {
    value: 'manual',
    name: '手动计划',
    description: '立即或稍后手动执行的测试计划',
    icon: VideoPlay,
    color: '#1890ff'
  },
  {
    value: 'scheduled',
    name: '定时计划',
    description: '按照预定时间自动执行的测试计划',
    icon: AlarmClock,
    color: '#722ed1'
  },
  {
    value: 'auto',
    name: '自动计划',
    description: '根据条件自动触发执行的测试计划',
    icon: MagicStick,
    color: '#52c41a'
  }
]

// 表单数据
const form = reactive({
  plan_type: 'manual',
  name: '',
  distributed: false,
  schedule_type: 'daily',
  schedule_time: '23:00',
  week_days: ['1', '2', '3', '4', '5'],
  cron_expression: '',
  include_paths: [],
  exclude_paths: [],
  case_statuses: [],
  priorities: ['failed', 'not_executed'],
  retry_count: 0,
  timeout_minutes: 0
})

// 验证规则
const configRules = {
  name: [
    { required: true, message: '请输入计划名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在2到50个字符', trigger: 'blur' }
  ]
}

// Cron表达式示例
const cronExamples = [
  { label: '每天23点', value: '0 23 * * *' },
  { label: '每5分钟', value: '*/5 * * * *' },
  { label: '每周一23点', value: '0 23 * * 1' },
  { label: '每月1号0点', value: '0 0 1 * *' }
]

// 优先级标签
const priorityLabels = {
  failed: '失败用例',
  not_executed: '未执行',
  recently_modified: '最近修改',
  new_cases: '新增用例'
}

// 计算属性
const planNamePlaceholder = computed(() => {
  switch (form.plan_type) {
    case 'manual':
      return '手动计划'
    case 'scheduled':
      return '定时计划'
    case 'auto':
      return '自动计划'
    default:
      return '测试计划'
  }
})

const planTypeText = computed(() => {
  const type = planTypes.find(t => t.value === form.plan_type)
  return type ? type.name : form.plan_type
})

const planTypeTagType = computed(() => {
  switch (form.plan_type) {
    case 'manual': return 'info'
    case 'scheduled': return 'warning'
    case 'auto': return 'success'
    default: return 'info'
  }
})

const scheduleText = computed(() => {
  if (form.schedule_type === 'daily') {
    return `每天 ${form.schedule_time} 执行`
  } else if (form.schedule_type === 'weekly') {
    const days = form.week_days.map(day => {
      const dayMap = { '0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六' }
      return `周${dayMap[day]}`
    }).join('、')
    return `每周${days} ${form.schedule_time} 执行`
  } else if (form.schedule_type === 'cron') {
    return `Cron表达式: ${form.cron_expression}`
  }
  return ''
})

// 处理选中的用例更新
const handleSelectedCasesUpdate = (cases) => {
  selectedCases.value = cases
}

// 移除单个用例
const removeCase = (caseId) => {
  const index = selectedCases.value.findIndex(item => item.id === caseId)
  if (index !== -1) {
    selectedCases.value.splice(index, 1)
  }
}

// 清空所有选中的用例
const clearSelectedCases = () => {
  selectedCases.value = []
  // 同时清空子组件的选中状态
  if (pathSelectionRef.value && pathSelectionRef.value.clearSelection) {
    pathSelectionRef.value.clearSelection()
  }
}

// 选择计划类型
const selectPlanType = (type) => {
  form.plan_type = type
  if (type === 'scheduled') {
    form.name = `定时计划 ${new Date().toLocaleString()}`
  } else {
    form.name = `${planTypes.find(t => t.value === type)?.name || '计划'} ${new Date().toLocaleString()}`
  }
}

// 上一步
const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

// 下一步
const nextStep = async () => {
  // 验证当前步骤
  if (activeStep.value === 0 && !form.plan_type) {
    ElMessage.warning('请选择计划类型')
    return
  }

  if (activeStep.value === 1) {
    if (!await validateConfigStep()) {
      return
    }
  }

  if (activeStep.value === 2 && selectedCases.value.length === 0) {
    ElMessage.warning('请至少选择一个测试用例')
    return
  }

  activeStep.value++
}

// 验证配置步骤
const validateConfigStep = async () => {
  if (!configFormRef.value) return false

  try {
    await configFormRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

const formatPreviewPath = (path) => {
  if (!path) return ''
  const parts = path.split('/')
  if (parts.length > 2) {
    return `.../${parts.slice(-2).join('/')}`
  }
  return path
}

// 提交表单
const handleSubmit = async () => {
  try {
    loading.value = true

    // 准备提交数据
    const submitData = {
      name: form.name,
      plan_type: form.plan_type,
      distributed: form.distributed,
      case_ids: selectedCases.value.map(caseItem => caseItem.id),
      priorities: form.priorities,
      retry_count: form.retry_count,
      timeout_minutes: form.timeout_minutes
    }

    // 添加定时设置
    if (form.plan_type === 'scheduled') {
      submitData.schedule_type = form.schedule_type
      submitData.schedule_time = form.schedule_time

      if (form.schedule_type === 'weekly') {
        submitData.week_days = form.week_days
      } else if (form.schedule_type === 'cron') {
        submitData.cron_expression = form.cron_expression
      }
    }

    // 调用API创建计划
    const response = await api.executeTestPlan(submitData)

    if (response.success) {
      ElMessage.success('测试计划创建成功')
      emit('success')
      resetForm()
      handleClose()
    } else {
      ElMessage.error(response.message || '创建计划失败')
    }
  } catch (error) {
    console.error('创建测试计划失败:', error)
    ElMessage.error('创建计划失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  activeStep.value = 0
  selectionTab.value = 'path'
  selectedCases.value = []

  // 重置PathSelection组件
  if (pathSelectionRef.value && pathSelectionRef.value.clearSelection) {
    pathSelectionRef.value.clearSelection()
  }

  Object.assign(form, {
    plan_type: 'manual',
    name: '',
    distributed: false,
    schedule_type: 'daily',
    schedule_time: '23:00',
    week_days: ['1', '2', '3', '4', '5'],
    cron_expression: '',
    include_paths: [],
    exclude_paths: [],
    case_statuses: [],
    priorities: ['failed', 'not_executed'],
    retry_count: 0,
    timeout_minutes: 0
  })
}

// 当切换到用例选择步骤时，等待DOM更新后初始化组件
watch(() => activeStep.value, async (newStep) => {
  if (newStep === 2) {
    // 等待DOM更新
    await nextTick()
    // 等待PathSelection组件挂载
    await nextTick()

    // 如果PathSelection组件引用存在，初始化它
    if (pathSelectionRef.value && pathSelectionRef.value.init) {
      pathSelectionRef.value.init()
    }
  }
}, { immediate: true })

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
  resetForm()
}

// 监听对话框状态
watch(dialogVisible, (val) => {
  if (!val) {
    resetForm()
  }
})
</script>

<style scoped>
/* 修改 dialog 整体高度 */
:deep(.el-dialog) {
  max-height: 80vh;
}

:deep(.el-dialog__body) {
  max-height: 60vh;
  overflow-y: auto;
}

/* 步骤3: 用例选择 - 修改布局为左右结构 */
.case-selection-container {
  display: flex;
  height: 380px; /* 适当调整高度 */
  gap: 16px;
}

.selection-left {
  flex: 3; /* 左侧占3份 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0; /* 防止 flex 溢出 */
}

.selection-left .path-selection-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 调整子组件的高度分配 */
:deep(.path-selection) {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.path-selection .filter-card) {
  flex-shrink: 0;
  margin-bottom: 6px !important;
  padding: 8px 16px !important;
}

:deep(.path-selection .filter-card .el-card__body) {
  padding: 8px 0 !important;
}

:deep(.path-selection .filter-toolbar .el-form) {
  margin-bottom: 0;
}

:deep(.path-selection .filter-toolbar .el-form-item) {
  margin-bottom: 0;
}

:deep(.path-selection .table-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 0;
}

:deep(.path-selection .table-card .el-card__body) {
  padding: 12px !important;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.path-selection .table-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.path-selection .el-table) {
  flex: 1;
  overflow: auto;
  margin-top: -10px; /* 表格往上提升 */
}

:deep(.path-selection .el-table__body-wrapper) {
  overflow-y: auto;
}

:deep(.path-selection .pagination-container) {
  margin-top: 12px;
  flex-shrink: 0;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
  background-color: #fff;
}

/* 右侧预览区域 */
.selection-preview {
  flex: 1; /* 右侧占1份 */
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  min-width: 280px; /* 最小宽度 */
  max-width: 320px; /* 最大宽度 */
  height: 100%; /* 和左侧一样高 */
}

.preview-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #f5f7fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.preview-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-tag {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
  color: #909399;
}

/* 其他步骤的样式保持不变 */
.step-content {
  min-height: 400px;
}

.step-panel {
  padding: 16px 0;
}

.step-title {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.plan-steps {
  margin-bottom: 24px;
}

.plan-type-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.plan-type-card {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.plan-type-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
}

.plan-type-card.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.type-icon {
  margin-bottom: 12px;
}

.type-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.type-desc {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
}

.scheduler-settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.time-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.weekly-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cron-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cron-examples {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.cron-example {
  cursor: pointer;
}

.cron-example:hover {
  opacity: 0.8;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.plan-summary {
  max-height: 400px;
  overflow-y: auto;
}

.priority-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 滚动条样式优化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
