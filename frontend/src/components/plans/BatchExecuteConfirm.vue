<template>
  <el-dialog
      v-model="dialogVisible"
      title="批量执行确认"
      width="600px"
      :before-close="handleClose"
  >
    <div v-loading="loading" class="batch-execute-confirm">
      <!-- 执行计划列表 -->
      <div class="selected-plans">
        <h4 class="section-title">选中的测试计划</h4>
        <div class="plans-list">
          <div v-for="plan in selectedPlans" :key="plan.id" class="plan-item">
            <div class="plan-info">
              <div class="plan-name">
                <el-tag
                    size="small"
                    :type="getPlanTypeTagType(plan.plan_type)"
                    class="plan-type-tag"
                >
                  {{ planTypeText(plan.plan_type) }}
                </el-tag>
                <span>{{ plan.name }}</span>
              </div>
              <div class="plan-status">
                <plan-status-tag :status="plan.status" size="small" />
              </div>
            </div>
            <div class="plan-details">
              <span class="detail-item">用例: {{ plan.total_cases || 0 }}</span>
              <span class="detail-item">状态: {{ plan.passed_cases || 0 }}/{{ plan.failed_cases || 0 }}</span>
            </div>
          </div>
        </div>
        <div class="plan-count">共 {{ selectedPlans.length }} 个测试计划</div>
      </div>

      <!-- 执行配置 -->
      <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          class="execute-config"
      >
        <el-form-item label="执行方式" prop="execution_mode">
          <el-radio-group v-model="form.execution_mode">
            <el-radio label="sequential">顺序执行</el-radio>
            <el-radio label="parallel">并行执行</el-radio>
            <el-radio label="distributed">分布式执行</el-radio>
          </el-radio-group>
          <div class="form-tip">
            {{ executionModeTips[form.execution_mode] }}
          </div>
        </el-form-item>

        <el-form-item v-if="form.execution_mode === 'parallel'" label="并发数量" prop="concurrency">
          <el-slider
              v-model="form.concurrency"
              :min="1"
              :max="Math.min(selectedPlans.length, 10)"
              :step="1"
              show-stops
              :marks="concurrencyMarks"
          />
          <div class="slider-value">{{ form.concurrency }} 个计划</div>
        </el-form-item>

        <el-form-item v-if="form.execution_mode === 'distributed'" label="分发策略">
          <el-radio-group v-model="form.distribution_strategy">
            <el-radio label="round_robin">轮询分配</el-radio>
            <el-radio label="load_balance">负载均衡</el-radio>
            <el-radio label="priority">按优先级分配</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="失败处理" prop="failure_handling">
          <el-radio-group v-model="form.failure_handling">
            <el-radio label="continue">继续执行</el-radio>
            <el-radio label="stop">停止执行</el-radio>
            <el-radio label="retry">重试失败计划</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.failure_handling === 'retry'" label="重试次数" prop="retry_count">
          <el-input-number
              v-model="form.retry_count"
              :min="1"
              :max="3"
              :step="1"
              style="width: 100px"
          />
        </el-form-item>

        <el-form-item label="执行超时(分钟)" prop="timeout_minutes">
          <el-input-number
              v-model="form.timeout_minutes"
              :min="0"
              :max="480"
              :step="30"
              style="width: 150px"
          />
          <span class="unit-label">分钟</span>
          <div class="form-tip">设置为0表示不超时</div>
        </el-form-item>

        <el-form-item label="执行优先级">
          <el-select v-model="form.priority_order" placeholder="选择执行顺序" style="width: 200px">
            <el-option label="按创建时间（先创建先执行）" value="created_asc" />
            <el-option label="按计划类型（定时计划优先）" value="type_priority" />
            <el-option label="按用例数量（用例少的优先）" value="cases_count" />
            <el-option label="随机顺序" value="random" />
          </el-select>
        </el-form-item>

        <el-form-item label="执行描述">
          <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入批量执行的描述信息（可选）"
          />
        </el-form-item>

        <el-form-item label="通知设置">
          <el-checkbox-group v-model="form.notify_settings">
            <el-checkbox label="start">开始时通知</el-checkbox>
            <el-checkbox label="complete">完成时通知</el-checkbox>
            <el-checkbox label="failure">失败时通知</el-checkbox>
            <el-checkbox label="summary">发送汇总报告</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <!-- 执行预览 -->
      <div class="execution-preview">
        <h4 class="section-title">执行预览</h4>
        <div class="preview-content">
          <div class="preview-item">
            <span class="label">执行方式:</span>
            <span class="value">{{ executionModeText }}</span>
          </div>
          <div class="preview-item">
            <span class="label">预计总耗时:</span>
            <span class="value">{{ estimatedDuration }}</span>
          </div>
          <div class="preview-item">
            <span class="label">预计开始时间:</span>
            <span class="value">{{ formatTime(estimatedStartTime) }}</span>
          </div>
          <div v-if="form.execution_mode === 'parallel'" class="preview-item">
            <span class="label">并发执行:</span>
            <span class="value">{{ form.concurrency }} 个计划同时执行</span>
          </div>
          <div class="preview-item">
            <span class="label">失败处理:</span>
            <span class="value">{{ failureHandlingText }}</span>
          </div>
        </div>
      </div>

      <!-- 警告信息 -->
      <div v-if="hasRunningPlans" class="warning-section">
        <el-alert
            title="警告"
            type="warning"
            :closable="false"
            show-icon
        >
          <p>选中的计划中包含正在执行的状态，批量执行可能会影响当前执行。</p>
          <p>建议等待当前计划执行完成后再进行批量操作。</p>
        </el-alert>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button
          type="primary"
          @click="handleConfirm"
          :loading="executing"
          :disabled="hasRunningPlans && !forceExecute"
      >
        {{ executing ? '执行中...' : '确认执行' }}
      </el-button>
      <el-button
          v-if="hasRunningPlans"
          type="warning"
          @click="handleForceExecute"
          :loading="executing"
      >
        强制执行
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import PlanStatusTag from './PlanStatusTag.vue'
import { formatTime } from '../../utils/formatter'
import api from "@/api";

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  plans: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 状态管理
const loading = ref(false)
const executing = ref(false)
const forceExecute = ref(false)
const formRef = ref()

// 表单数据
const form = reactive({
  execution_mode: 'sequential',
  concurrency: 1,
  distribution_strategy: 'round_robin',
  failure_handling: 'continue',
  retry_count: 1,
  timeout_minutes: 0,
  priority_order: 'created_asc',
  description: '',
  notify_settings: ['complete', 'failure']
})

// 验证规则
const rules = {
  concurrency: [
    { required: true, message: '请选择并发数量', trigger: 'blur' }
  ],
  retry_count: [
    { required: true, message: '请输入重试次数', trigger: 'blur' }
  ]
}

// 计算选中的计划
const selectedPlans = computed(() => {
  return props.plans
})

// 并发数标记
const concurrencyMarks = computed(() => {
  const marks = {}
  const max = Math.min(selectedPlans.value.length, 10)
  marks[1] = '1'
  if (max >= 3) marks[3] = '3'
  if (max >= 5) marks[5] = '5'
  if (max >= 8) marks[8] = '8'
  marks[max] = max.toString()
  return marks
})

// 执行方式提示
const executionModeTips = {
  sequential: '按顺序依次执行每个计划，适用于资源受限或需要严格顺序的场景',
  parallel: '同时执行多个计划，提高效率但需要更多资源',
  distributed: '将计划分发到多台机器执行，适合大规模测试'
}

// 计算是否有正在执行的计划
const hasRunningPlans = computed(() => {
  return selectedPlans.value.some(plan => plan.status === 'running')
})

// 获取计划类型标签样式
const getPlanTypeTagType = (planType) => {
  switch (planType) {
    case 'scheduled': return 'warning'
    case 'manual': return 'info'
    case 'auto': return 'success'
    default: return 'info'
  }
}

// 计划类型文本
const planTypeText = (planType) => {
  switch (planType) {
    case 'scheduled': return '定时'
    case 'manual': return '手动'
    case 'auto': return '自动'
    default: return planType
  }
}

// 执行方式文本
const executionModeText = computed(() => {
  switch (form.execution_mode) {
    case 'sequential': return '顺序执行'
    case 'parallel': return `并行执行（${form.concurrency}并发）`
    case 'distributed': return `分布式执行（${form.distribution_strategy}）`
    default: return form.execution_mode
  }
})

// 失败处理文本
const failureHandlingText = computed(() => {
  switch (form.failure_handling) {
    case 'continue': return '继续执行后续计划'
    case 'stop': return '停止执行所有计划'
    case 'retry': return `重试失败计划（最多${form.retry_count}次）`
    default: return form.failure_handling
  }
})

// 预计开始时间
const estimatedStartTime = computed(() => {
  return new Date()
})

// 预计总耗时（简单估算）
const estimatedDuration = computed(() => {
  const avgCaseTime = 10 // 每个用例平均10秒
  const totalCases = selectedPlans.value.reduce((sum, plan) => sum + (plan.total_cases || 0), 0)
  const totalSeconds = totalCases * avgCaseTime

  if (form.execution_mode === 'parallel' && form.concurrency > 1) {
    const parallelSeconds = totalSeconds / form.concurrency
    return formatDuration(Math.max(parallelSeconds, 60)) // 最少1分钟
  }

  return formatDuration(Math.max(totalSeconds, 60))
})

// 格式化持续时间
const formatDuration = (seconds) => {
  if (seconds < 60) return `${Math.round(seconds)}秒`

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60

  if (minutes < 60) {
    return `${minutes}分钟${remainingSeconds > 0 ? `${Math.round(remainingSeconds)}秒` : ''}`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  return `${hours}小时${remainingMinutes > 0 ? `${remainingMinutes}分钟` : ''}`
}

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
}

// 强制执行
const handleForceExecute = () => {
  forceExecute.value = true
  handleConfirm()
}

// 确认执行
const handleConfirm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    executing.value = true

    // 准备批量执行的数据
    const executeData = {
      plan_ids: selectedPlans.value.map(plan => plan.id),
      execution_config: {
        ...form,
        force_execute: forceExecute.value
      },
      description: form.description || `批量执行 ${selectedPlans.value.length} 个测试计划`
    }

    // 调用批量执行API
    // 这里需要根据后端API调整
    await executeBatchPlans(executeData)

    ElMessage.success('批量执行已开始')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('批量执行失败:', error)
    ElMessage.error('批量执行失败')
  } finally {
    executing.value = false
    forceExecute.value = false
  }
}

// 批量执行计划（模拟实现）
const executeBatchPlans = async (data) => {
  // 模拟API调用延迟
  // await new Promise(resolve => setTimeout(resolve, 1500))

  // 在实际项目中，这里应该调用后端API
  await api.batchExecutePlans(data)

  console.log('批量执行数据:', data)
  return { success: true, message: '批量执行已提交' }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(form, {
    execution_mode: 'sequential',
    concurrency: 1,
    distribution_strategy: 'round_robin',
    failure_handling: 'continue',
    retry_count: 1,
    timeout_minutes: 0,
    priority_order: 'created_asc',
    description: '',
    notify_settings: ['complete', 'failure']
  })
  forceExecute.value = false
}

// 监听对话框状态
watch(dialogVisible, (val) => {
  if (val) {
    // 根据选中的计划数量设置默认并发数
    const planCount = selectedPlans.value.length
    if (planCount > 1) {
      form.concurrency = Math.min(Math.floor(planCount / 2), 5)
    }

    // 自动生成本次执行的描述
    if (!form.description) {
      form.description = `批量执行 ${planCount} 个测试计划，包含：${selectedPlans.value.map(p => p.name).join('、')}`
    }
  } else {
    resetForm()
  }
})
</script>

<style scoped>
.batch-execute-confirm {
  padding: 8px 0;
}

.section-title {
  font-size: 14px;
  color: #333;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.selected-plans {
  margin-bottom: 20px;
}

.plans-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
  background: #fafafa;
  margin-bottom: 12px;
}

.plan-item {
  padding: 8px;
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.3s;
}

.plan-item:hover {
  background-color: #f5f5f5;
}

.plan-item:last-child {
  border-bottom: none;
}

.plan-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.plan-name {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.plan-name span {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-type-tag {
  flex-shrink: 0;
}

.plan-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.detail-item {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 2px;
}

.plan-count {
  text-align: right;
  font-size: 12px;
  color: #999;
}

.execute-config {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}

.unit-label {
  margin-left: 8px;
  color: #666;
  font-size: 14px;
}

.slider-value {
  text-align: center;
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

.execution-preview {
  margin-bottom: 20px;
}

.preview-content {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}

.preview-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-item .label {
  width: 100px;
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
}

.preview-item .value {
  flex: 1;
  font-size: 12px;
  color: #333;
  font-weight: 500;
}

.warning-section {
  margin-bottom: 20px;
}

.warning-section :deep(.el-alert) {
  padding: 12px 16px;
}

.warning-section p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

:deep(.el-slider__marks-text) {
  font-size: 10px;
  color: #999;
}
</style>
