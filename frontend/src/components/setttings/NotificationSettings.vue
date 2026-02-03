<template>
  <div class="notification-settings">
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="180px"
        label-position="left"
        :disabled="loading"
    >
      <!-- 邮件通知 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">邮件通知</h3>
            <el-switch
                v-model="form.email_enabled"
                active-text="启用"
                inactive-text="禁用"
            />
          </div>
        </template>

        <div v-if="form.email_enabled">
          <el-form-item label="SMTP服务器" prop="email_host">
            <el-input
                v-model="form.email_host"
                placeholder="smtp.example.com"
                style="width: 300px"
            />
          </el-form-item>

          <el-form-item label="SMTP端口" prop="email_port">
            <el-input-number
                v-model="form.email_port"
                :min="1"
                :max="65535"
                :step="1"
                style="width: 150px"
            />
          </el-form-item>

          <el-form-item label="SMTP用户名" prop="email_username">
            <el-input
                v-model="form.email_username"
                placeholder="user@example.com"
                style="width: 300px"
            />
          </el-form-item>

          <el-form-item label="SMTP密码" prop="email_password">
            <el-input
                v-model="form.email_password"
                type="password"
                placeholder="请输入密码"
                style="width: 300px"
                show-password
            />
          </el-form-item>

          <el-form-item label="发件人邮箱" prop="email_from">
            <el-input
                v-model="form.email_from"
                placeholder="noreply@example.com"
                style="width: 300px"
            />
          </el-form-item>

          <el-form-item label="收件人列表" prop="email_to">
            <el-select
                v-model="form.email_to"
                multiple
                filterable
                allow-create
                placeholder="输入邮箱地址"
                style="width: 400px"
            >
              <el-option label="admin@example.com" value="admin@example.com" />
              <el-option label="qa@example.com" value="qa@example.com" />
            </el-select>
            <div class="form-tip">
              多个收件人用逗号分隔
            </div>
          </el-form-item>

          <el-form-item label="邮件主题模板">
            <el-input
                v-model="form.email_subject_template"
                placeholder="测试执行结果 - {{status}} - {{plan_name}}"
                style="width: 400px"
            />
            <div class="form-tip">
              支持变量：{{status}}、{{plan_name}}、{{time}}等
            </div>
          </el-form-item>

          <el-form-item label="测试邮件">
            <el-button
                type="primary"
                :icon="Message"
                @click="handleTestEmail"
            >
              发送测试邮件
            </el-button>
          </el-form-item>
        </div>

        <div v-else class="disabled-section">
          <el-empty description="邮件通知已禁用" :image-size="60" />
        </div>
      </el-card>

      <!-- Webhook通知 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">Webhook通知</h3>
            <el-switch
                v-model="form.webhook_enabled"
                active-text="启用"
                inactive-text="禁用"
            />
          </div>
        </template>

        <div v-if="form.webhook_enabled">
          <el-form-item label="Webhook URL" prop="webhook_url">
            <el-input
                v-model="form.webhook_url"
                placeholder="https://hooks.slack.com/services/..."
                style="width: 400px"
            />
          </el-form-item>

          <el-form-item label="请求方法">
            <el-radio-group v-model="form.webhook_method">
              <el-radio label="POST">POST</el-radio>
              <el-radio label="GET">GET</el-radio>
              <el-radio label="PUT">PUT</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="请求头">
            <div class="webhook-headers">
              <div v-for="(header, index) in form.webhook_headers" :key="index" class="header-item">
                <el-input
                    v-model="header.name"
                    placeholder="Header名称"
                    style="width: 180px; margin-right: 8px;"
                />
                <el-input
                    v-model="header.value"
                    placeholder="Header值"
                    style="width: 180px; margin-right: 8px;"
                />
                <el-button
                    type="danger"
                    :icon="Delete"
                    circle
                    @click="removeWebhookHeader(index)"
                />
              </div>
              <el-button
                  type="primary"
                  :icon="Plus"
                  @click="addWebhookHeader"
              >
                添加请求头
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="请求体模板">
            <el-input
                v-model="form.webhook_body_template"
                type="textarea"
                :rows="6"
                placeholder="JSON格式的请求体模板"
            />
            <div class="form-tip">
              支持变量：{{status}}、{{plan_name}}、{{success_count}}、{{failed_count}}等
            </div>
          </el-form-item>

          <el-form-item label="测试Webhook">
            <el-button
                type="primary"
                :icon="Link"
                @click="handleTestWebhook"
            >
              测试Webhook
            </el-button>
          </el-form-item>
        </div>

        <div v-else class="disabled-section">
          <el-empty description="Webhook通知已禁用" :image-size="60" />
        </div>
      </el-card>

      <!-- 钉钉通知 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">钉钉机器人通知</h3>
            <el-switch
                v-model="form.dingtalk_enabled"
                active-text="启用"
                inactive-text="禁用"
            />
          </div>
        </template>

        <div v-if="form.dingtalk_enabled">
          <el-form-item label="Webhook地址" prop="dingtalk_webhook">
            <el-input
                v-model="form.dingtalk_webhook"
                placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                style="width: 400px"
            />
          </el-form-item>

          <el-form-item label="加签密钥">
            <el-input
                v-model="form.dingtalk_secret"
                type="password"
                placeholder="请输入加签密钥"
                style="width: 300px"
                show-password
            />
            <div class="form-tip">
              安全设置中选择"加签"时填写
            </div>
          </el-form-item>

          <el-form-item label="@用户手机号">
            <el-select
                v-model="form.dingtalk_at_mobiles"
                multiple
                filterable
                allow-create
                placeholder="输入手机号"
                style="width: 300px"
            >
              <el-option label="13800138000" value="13800138000" />
              <el-option label="13900139000" value="13900139000" />
            </el-select>
          </el-form-item>

          <el-form-item label="消息模板">
            <el-input
                v-model="form.dingtalk_template"
                type="textarea"
                :rows="4"
                placeholder="钉钉消息模板"
            />
            <div class="form-tip">
              支持Markdown格式，变量：{{status}}、{{plan_name}}、{{result_summary}}等
            </div>
          </el-form-item>
        </div>

        <div v-else class="disabled-section">
          <el-empty description="钉钉通知已禁用" :image-size="60" />
        </div>
      </el-card>

      <!-- 通知策略 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">通知策略</h3>
          </div>
        </template>

        <el-form-item label="通知触发条件">
          <el-checkbox-group v-model="form.notify_triggers">
            <el-checkbox label="failure">执行失败时</el-checkbox>
            <el-checkbox label="success">执行成功时</el-checkbox>
            <el-checkbox label="timeout">执行超时时</el-checkbox>
            <el-checkbox label="new_case">新增用例时</el-checkbox>
            <el-checkbox label="system_error">系统异常时</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="通知频率限制">
          <el-input-number
              v-model="form.notify_cooldown"
              :min="1"
              :max="60"
              :step="1"
              style="width: 150px; margin-right: 8px;"
          />
          <span class="unit-label">分钟</span>
          <div class="form-tip">
            相同类型的通知在此时间内只发送一次
          </div>
        </el-form-item>

        <el-form-item label="紧急通知重试">
          <el-input-number
              v-model="form.notify_retry_count"
              :min="0"
              :max="5"
              :step="1"
              style="width: 150px; margin-right: 8px;"
          />
          <span class="unit-label">次</span>
          <div class="form-tip">
            紧急通知发送失败时的重试次数
          </div>
        </el-form-item>
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
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh, Message, Link, Plus, Delete } from '@element-plus/icons-vue'

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

// 表单数据
const form = reactive({
  email_enabled: false,
  email_host: 'smtp.example.com',
  email_port: 587,
  email_username: '',
  email_password: '',
  email_from: '',
  email_to: [],
  email_subject_template: '测试执行结果 - {{status}} - {{plan_name}}',
  webhook_enabled: true,
  webhook_url: '',
  webhook_method: 'POST',
  webhook_headers: [
    { name: 'Content-Type', value: 'application/json' }
  ],
  webhook_body_template: JSON.stringify({
    text: '测试计划 {{plan_name}} 执行完成',
    status: '{{status}}',
    success_count: '{{success_count}}',
    failed_count: '{{failed_count}}',
    time: '{{time}}'
  }, null, 2),
  dingtalk_enabled: false,
  dingtalk_webhook: '',
  dingtalk_secret: '',
  dingtalk_at_mobiles: [],
  dingtalk_template: '#### 测试计划通知\n\n**计划名称:** {{plan_name}}\n\n**执行状态:** {{status}}\n\n**执行结果:** 成功 {{success_count}} / 失败 {{failed_count}}\n\n**执行时间:** {{time}}',
  notify_triggers: ['failure', 'timeout', 'system_error'],
  notify_cooldown: 5,
  notify_retry_count: 3
})

// 验证规则
const rules = {
  email_host: [
    { required: true, message: '请输入SMTP服务器', trigger: 'blur' }
  ],
  email_port: [
    { required: true, message: '请输入SMTP端口', trigger: 'blur' }
  ],
  email_from: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
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

// 添加Webhook请求头
const addWebhookHeader = () => {
  form.webhook_headers.push({
    name: '',
    value: ''
  })
}

// 移除Webhook请求头
const removeWebhookHeader = (index) => {
  form.webhook_headers.splice(index, 1)
}

// 测试邮件
const handleTestEmail = () => {
  ElMessage.info('测试邮件已发送，请查收')
}

// 测试Webhook
const handleTestWebhook = () => {
  ElMessage.info('Webhook测试已发送，请查看目标系统')
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

    ElMessage.success('通知设置已保存')
  } catch (error) {
    console.error('保存通知设置失败:', error)
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

// 暴露保存方法供父组件调用
const save = async () => {
  await handleSave()
  return true
}

defineExpose({ save })
</script>

<style scoped>
.notification-settings {
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

.disabled-section {
  padding: 40px 0;
  text-align: center;
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

.webhook-headers {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header-item {
  display: flex;
  align-items: center;
  gap: 8px;
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

  .header-item {
    flex-direction: column;
    align-items: stretch;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
