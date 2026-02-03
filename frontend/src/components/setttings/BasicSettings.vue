<template>
  <div class="basic-settings">
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="180px"
        label-position="left"
        :disabled="loading"
    >
      <!-- 系统基本信息 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">系统基本信息</h3>
          </div>
        </template>

        <el-form-item label="系统名称" prop="system_name">
          <el-input
              v-model="form.system_name"
              placeholder="请输入系统名称"
              style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="系统版本" prop="system_version">
          <el-input
              v-model="form.system_version"
              placeholder="请输入系统版本"
              style="width: 200px"
              disabled
          />
        </el-form-item>

        <el-form-item label="测试用例根目录" prop="test_case_root">
          <el-input
              v-model="form.test_case_root"
              placeholder="请输入测试用例根目录"
              style="width: 400px"
          >
            <template #append>
              <el-button :icon="FolderOpened" @click="handleBrowseDirectory">
                浏览
              </el-button>
            </template>
          </el-input>
          <div class="form-tip">
            测试用例文件所在的根目录，系统会自动监控此目录下的文件变化
          </div>
        </el-form-item>

        <el-form-item label="启用文件监控" prop="watchdog_enabled">
          <el-switch
              v-model="form.watchdog_enabled"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            启用后系统会自动监控测试用例文件的创建、修改和删除
          </div>
        </el-form-item>

        <el-form-item v-if="form.watchdog_enabled" label="自动扫描间隔(秒)" prop="auto_scan_interval">
          <el-input-number
              v-model="form.auto_scan_interval"
              :min="60"
              :max="3600"
              :step="60"
              style="width: 150px"
          />
          <span class="unit-label">秒</span>
          <div class="form-tip">
            自动扫描文件变化的间隔时间，默认300秒（5分钟）
          </div>
        </el-form-item>
      </el-card>

      <!-- 数据保留设置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">数据保留设置</h3>
          </div>
        </template>

        <el-form-item label="执行历史保留天数" prop="max_history_days">
          <el-input-number
              v-model="form.max_history_days"
              :min="7"
              :max="365"
              :step="1"
              style="width: 150px"
          />
          <span class="unit-label">天</span>
          <div class="form-tip">
            执行历史记录保留的最大天数，超过此天数的记录会被自动清理
          </div>
        </el-form-item>

        <el-form-item label="启用审计日志" prop="enable_audit_log">
          <el-switch
              v-model="form.enable_audit_log"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            记录用户操作日志，用于审计和安全分析
          </div>
        </el-form-item>
      </el-card>

      <!-- 国际化设置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">国际化设置</h3>
          </div>
        </template>

        <el-form-item label="默认语言" prop="default_language">
          <el-select
              v-model="form.default_language"
              placeholder="请选择默认语言"
              style="width: 200px"
          >
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
            <el-option label="日本語" value="ja-JP" />
          </el-select>
        </el-form-item>

        <el-form-item label="系统时区" prop="timezone">
          <el-select
              v-model="form.timezone"
              placeholder="请选择系统时区"
              style="width: 200px"
          >
            <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
            <el-option label="Asia/Tokyo (UTC+9)" value="Asia/Tokyo" />
            <el-option label="America/New_York (UTC-5)" value="America/New_York" />
            <el-option label="Europe/London (UTC+0)" value="Europe/London" />
          </el-select>
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
import { FolderOpened, Check, Refresh } from '@element-plus/icons-vue'

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
const form = reactive({})

// 验证规则
const rules = {
  system_name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在2到50个字符', trigger: 'blur' }
  ],
  test_case_root: [
    { required: true, message: '请输入测试用例根目录', trigger: 'blur' }
  ],
  auto_scan_interval: [
    { required: true, message: '请输入扫描间隔', trigger: 'blur' }
  ],
  max_history_days: [
    { required: true, message: '请输入历史保留天数', trigger: 'blur' }
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
    return form[key] !== props.config[key]
  })
}

// 浏览目录
const handleBrowseDirectory = () => {
  ElMessage.info('在真实环境中，这里会打开文件选择对话框')
  // 在实际项目中，这里可以通过Electron或后端API选择目录
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

    ElMessage.success('基本设置已保存')
  } catch (error) {
    console.error('保存基本设置失败:', error)
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
.basic-settings {
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

.form-actions {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
  text-align: center;
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
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}
</style>
