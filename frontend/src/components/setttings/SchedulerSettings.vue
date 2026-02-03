<template>
  <div class="scheduler-settings">
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="200px"
        label-position="left"
        :disabled="loading"
    >
      <!-- 定时任务开关 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">定时任务开关</h3>
          </div>
        </template>

        <el-form-item label="启用定时任务" prop="enabled">
          <el-switch
              v-model="form.enabled"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            启用后系统会根据配置自动执行测试任务
          </div>
        </el-form-item>

        <el-form-item v-if="form.enabled" label="执行时间" required>
          <div class="schedule-time">
            <el-time-picker
                v-model="form.schedule_time"
                placeholder="选择执行时间"
                format="HH:mm"
                value-format="HH:mm"
                style="width: 150px; margin-right: 16px;"
            />
            <span class="time-label">每天</span>
          </div>
          <div class="form-tip">
            建议设置在业务低峰期，如晚上23:00
          </div>
        </el-form-item>

        <el-form-item v-if="form.enabled" label="执行日期">
          <el-checkbox-group v-model="form.schedule_days">
            <el-checkbox label="1">周一</el-checkbox>
            <el-checkbox label="2">周二</el-checkbox>
            <el-checkbox label="3">周三</el-checkbox>
            <el-checkbox label="4">周四</el-checkbox>
            <el-checkbox label="5">周五</el-checkbox>
            <el-checkbox label="6">周六</el-checkbox>
            <el-checkbox label="0">周日</el-checkbox>
          </el-checkbox-group>
          <div class="form-tip">
            选择每周需要执行的天数，建议工作日执行
          </div>
        </el-form-item>
      </el-card>

      <!-- 任务执行配置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">任务执行配置</h3>
          </div>
        </template>

        <el-form-item label="最大并行计划数" prop="max_parallel_plans">
          <el-input-number
              v-model="form.max_parallel_plans"
              :min="1"
              :max="10"
              :step="1"
              style="width: 150px"
          />
          <div class="form-tip">
            同时执行的最大测试计划数量，避免资源过载
          </div>
        </el-form-item>

        <el-form-item label="失败自动重试" prop="auto_retry_failed">
          <el-switch
              v-model="form.auto_retry_failed"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            自动重试上次失败的用例
          </div>
        </el-form-item>

        <el-form-item v-if="form.auto_retry_failed" label="重试次数" prop="retry_count">
          <el-input-number
              v-model="form.retry_count"
              :min="0"
              :max="5"
              :step="1"
              style="width: 150px"
          />
          <div class="form-tip">
            设置为0表示不重试
          </div>
        </el-form-item>

        <el-form-item label="任务超时时间(小时)" prop="timeout_hours">
          <el-input-number
              v-model="form.timeout_hours"
              :min="1"
              :max="24"
              :step="1"
              style="width: 150px"
          />
          <span class="unit-label">小时</span>
          <div class="form-tip">
            定时任务最大执行时间，超时后自动终止
          </div>
        </el-form-item>

        <el-form-item label="任务完成通知" prop="notify_on_complete">
          <el-switch
              v-model="form.notify_on_complete"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            任务完成后发送通知
          </div>
        </el-form-item>
      </el-card>

      <!-- 执行策略 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">执行策略</h3>
            <el-button type="text" @click="showStrategyHelp">
              查看策略说明
            </el-button>
          </div>
        </template>

        <div class="strategy-config">
          <div class="strategy-item">
            <div class="strategy-header">
              <span class="strategy-title">新增用例优先</span>
              <el-switch
                  v-model="form.priorities.new_cases"
                  active-text="启用"
                  inactive-text="禁用"
              />
            </div>
            <div class="strategy-desc">
              优先执行当天新增的测试用例
            </div>
          </div>

          <div class="strategy-item">
            <div class="strategy-header">
              <span class="strategy-title">失败用例优先</span>
              <el-switch
                  v-model="form.priorities.failed_cases"
                  active-text="启用"
                  inactive-text="禁用"
              />
            </div>
            <div class="strategy-desc">
              优先执行上次执行失败的用例
            </div>
          </div>

          <div class="strategy-item">
            <div class="strategy-header">
              <span class="strategy-title">长时间未执行</span>
              <el-switch
                  v-model="form.priorities.long_not_executed"
                  active-text="启用"
                  inactive-text="禁用"
              />
            </div>
            <div class="strategy-desc">
              优先执行长时间未执行的用例
            </div>
          </div>

          <div class="strategy-item">
            <div class="strategy-header">
              <span class="strategy-title">优先目录</span>
              <el-switch
                  v-model="form.priorities.priority_paths"
                  active-text="启用"
                  inactive-text="禁用"
              />
            </div>
            <div class="strategy-desc">
              优先执行指定目录下的用例
            </div>
            <div v-if="form.priorities.priority_paths" class="priority-paths">
              <el-select
                  v-model="form.priority_paths"
                  multiple
                  filterable
                  allow-create
                  placeholder="输入或选择目录路径"
                  style="width: 100%"
              >
                <el-option label="smoke" value="smoke" />
                <el-option label="regression" value="regression" />
                <el-option label="critical" value="critical" />
              </el-select>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button
            type="primary"
            :icon="Check"
            @click="handleSave"
            :loading="saving"
        >
          保存设置
        </el-button>
        <el-button
            :icon="Refresh"
            @click="handleReset"
        >
          重置
        </el-button>
        <el-button
            type="warning"
            :icon="AlarmClock"
            @click="handleTestSchedule"
        >
          测试调度
        </el-button>
      </div>
    </el-form>

    <!-- 策略说明对话框 -->
    <strategy-help-dialog
        v-model="helpDialogVisible"
    />
  </div>
</template>

<script setup>
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh, AlarmClock } from '@element-plus/icons-vue'
import StrategyHelpDialog from './StrategyHelpDialog.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

const emit = defineEmits(['change'])

// 表单引用
const formRef = ref()
const loading = ref(false)
const saving = ref(false)
const helpDialogVisible = ref(false)

// 表单数据
const form = reactive({
  enabled: true,
  schedule_time: '23:00',
  schedule_days: ['1', '2', '3', '4', '5', '6', '0'],
  max_parallel_plans: 3,
  auto_retry_failed: true,
  retry_count: 3,
  timeout_hours: 8,
  notify_on_complete: true,
  priorities: {
    new_cases: true,
    failed_cases: true,
    long_not_executed: true,
    priority_paths: false
  },
  priority_paths: []
})

// 验证规则
const rules = {
  schedule_time: [
    { required: true, message: '请选择执行时间', trigger: 'blur' }
  ]
}

// 初始化表单
const initForm = () => {
  Object.assign(form, props.config)
}

// 监听配置变化
watch(() => props.config, () => {
  initForm()
}, { immediate: true, deep: true })

// 监听表单变化
watch(form, () => {
  const hasChange = checkFormChanges()
  emit('change', hasChange)
}, { deep: true })

// 检查表单是否有变化
const checkFormChanges = () => {
  return Object.keys(form).some(key => {
    return JSON.stringify(form[key]) !== JSON.stringify(props.config[key])
  })
}

// 显示策略说明
const showStrategyHelp = () => {
  helpDialogVisible.value = true
}

// 保存设置
const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    saving.value = true

    // 调用API保存配置
    // 这里模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))

    // 通知父组件配置已保存
    const hasChange = checkFormChanges()
    emit('change', hasChange)

    ElMessage.success('定时任务配置已保存')
  } catch (error) {
    console.error('保存定时任务配置失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 重置表单
const handleReset = () => {
  if (formRef.value) {
    formRef.value.resetFields()
    initForm()
  }
}

// 测试调度
const handleTestSchedule = () => {
  ElMessage.info('调度测试已开始，请查看任务执行情况')
}

// 暴露保存方法供父组件调用
const save = async () => {
  await handleSave()
  return true
}

defineExpose({ save })
</script>

<style scoped>
.scheduler-settings {
  padding: 20px 0;
}

.settings-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 16px;
  color: #333;
  margin: 0;
}

.schedule-time {
  display: flex;
  align-items: center;
}

.time-label {
  color: #666;
  font-size: 14px;
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

.strategy-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strategy-item {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fafafa;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.strategy-title {
  font-weight: 500;
  color: #333;
}

.strategy-desc {
  font-size: 12px;
  color: #666;
}

.priority-paths {
  margin-top: 12px;
}

.form-actions {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 12px;
}

@media (max-width: 768px) {
  :deep(.el-form-item) {
    flex-direction: column;
  }

  :deep(.el-form-item__label) {
    text-align: left;
    margin-bottom: 8px;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
