<template>
  <div class="settings-container">
    <!-- 设置页面头部 -->
    <div class="settings-header">
      <h1 class="settings-title">系统设置</h1>
      <div class="settings-actions">
        <el-button
            type="primary"
            :icon="Refresh"
            @click="handleRefresh"
            :loading="refreshing"
        >
          刷新配置
        </el-button>
        <el-button
            type="success"
            :icon="Check"
            @click="handleSaveAll"
            :loading="saving"
        >
          保存所有更改
        </el-button>
      </div>
    </div>

    <!-- 设置标签页 -->
    <div class="settings-tabs">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本设置 -->
        <el-tab-pane label="基本设置" name="basic">
          <basic-settings
              ref="basicSettingsRef"
              :config="basicConfig"
              @change="handleBasicChange"
          />
        </el-tab-pane>

        <!-- 定时任务 -->
        <el-tab-pane label="定时任务" name="scheduler">
          <scheduler-settings
              ref="schedulerSettingsRef"
              :config="schedulerConfig"
              @change="handleSchedulerChange"
          />
        </el-tab-pane>

        <!-- 执行器配置 -->
        <el-tab-pane label="执行器配置" name="executor">
          <executor-settings
              ref="executorSettingsRef"
              :config="executorConfig"
              @change="handleExecutorChange"
          />
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane label="通知设置" name="notification">
          <notification-settings
              ref="notificationSettingsRef"
              :config="notificationConfig"
              @change="handleNotificationChange"
          />
        </el-tab-pane>

        <!-- 存储设置 -->
        <el-tab-pane label="存储设置" name="storage">
          <storage-settings
              ref="storageSettingsRef"
              :config="storageConfig"
              @change="handleStorageChange"
          />
        </el-tab-pane>

        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <user-management
              ref="userManagementRef"
              @change="handleUsersChange"
          />
        </el-tab-pane>

        <!-- 系统信息 -->
        <el-tab-pane label="系统信息" name="system">
          <system-info
              :system-info="systemInfo"
              @refresh="fetchSystemInfo"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 保存提示 -->
    <div v-if="hasChanges" class="changes-notice">
      <el-alert
          title="有未保存的更改"
          type="warning"
          :closable="false"
          show-icon
      >
        <template #append>
          <el-button type="primary" size="small" @click="handleSaveAll">
            保存更改
          </el-button>
          <el-button type="info" size="small" @click="handleDiscard">
            放弃更改
          </el-button>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'
import api from '../api'

// 组件引用
import BasicSettings from '../components/settings/BasicSettings.vue'
import SchedulerSettings from '../components/settings/SchedulerSettings.vue'
import ExecutorSettings from '../components/settings/ExecutorSettings.vue'
import NotificationSettings from '../components/settings/NotificationSettings.vue'
import StorageSettings from '../components/settings/StorageSettings.vue'
import UserManagement from '../components/settings/UserManagement.vue'
import SystemInfo from '../components/settings/SystemInfo.vue'

// 数据状态
const activeTab = ref('basic')
const refreshing = ref(false)
const saving = ref(false)

// 配置数据
const basicConfig = reactive({})
const schedulerConfig = reactive({})
const executorConfig = reactive({})
const notificationConfig = reactive({})
const storageConfig = reactive({})
const systemInfo = reactive({})

// 变更跟踪
const configChanges = reactive({
  basic: false,
  scheduler: false,
  executor: false,
  notification: false,
  storage: false,
  users: false
})

// 组件引用
const basicSettingsRef = ref()
const schedulerSettingsRef = ref()
const executorSettingsRef = ref()
const notificationSettingsRef = ref()
const storageSettingsRef = ref()
const userManagementRef = ref()

// 计算是否有未保存的更改
const hasChanges = computed(() => {
  return Object.values(configChanges).some(hasChange => hasChange)
})

// 获取系统配置
const fetchSystemConfig = async () => {
  try {
    refreshing.value = true

    // 模拟API调用，实际项目中需要根据后端API调整
    // 这里我们使用模拟数据
    await Promise.all([
      fetchBasicConfig(),
      fetchSchedulerConfig(),
      fetchExecutorConfig(),
      fetchNotificationConfig(),
      fetchStorageConfig(),
      fetchSystemInfo()
    ])

    // 重置变更状态
    resetChanges()

    ElMessage.success('配置加载完成')
  } catch (error) {
    console.error('获取系统配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    refreshing.value = false
  }
}

// 获取基本配置
const fetchBasicConfig = async () => {
  // 模拟数据
  Object.assign(basicConfig, {
    system_name: '自动化测试平台',
    system_version: '1.0.0',
    test_case_root: '/data/test_cases',
    watchdog_enabled: true,
    auto_scan_interval: 300,
    max_history_days: 30,
    default_language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    enable_audit_log: true
  })
}

// 获取定时任务配置
const fetchSchedulerConfig = async () => {
  // 模拟数据
  Object.assign(schedulerConfig, {
    enabled: true,
    schedule_time: '23:00',
    schedule_days: ['1', '2', '3', '4', '5', '6', '0'],
    max_parallel_plans: 3,
    auto_retry_failed: true,
    retry_count: 3,
    timeout_hours: 8,
    notify_on_complete: true
  })
}

// 获取执行器配置
const fetchExecutorConfig = async () => {
  // 模拟数据
  Object.assign(executorConfig, {
    executor_type: 'local',
    max_workers: 4,
    task_timeout: 1800,
    memory_limit: '2G',
    cpu_limit: '50%',
    enable_cache: true,
    cache_ttl: 3600,
    log_level: 'INFO',
    log_retention: '30d'
  })
}

// 获取通知配置
const fetchNotificationConfig = async () => {
  // 模拟数据
  Object.assign(notificationConfig, {
    email_enabled: false,
    email_host: 'smtp.example.com',
    email_port: 587,
    email_username: '',
    email_password: '',
    email_from: '',
    email_to: [],
    webhook_enabled: true,
    webhook_url: '',
    notify_on_failure: true,
    notify_on_success: false,
    notify_on_timeout: true,
    dingtalk_enabled: false,
    dingtalk_webhook: '',
    dingtalk_secret: ''
  })
}

// 获取存储配置
const fetchStorageConfig = async () => {
  // 模拟数据
  Object.assign(storageConfig, {
    database_type: 'sqlite',
    database_url: 'sqlite:///test.db',
    backup_enabled: true,
    backup_interval: 24,
    backup_retention: 7,
    file_storage_path: '/data/storage',
    max_storage_size: '10G',
    cleanup_enabled: true,
    cleanup_schedule: '0 2 * * *'
  })
}

// 获取系统信息
const fetchSystemInfo = async () => {
  try {
    // 这里可以调用系统信息API
    // 模拟数据
    Object.assign(systemInfo, {
      platform: process.platform,
      arch: process.arch,
      node_version: process.version,
      uptime: Math.floor(process.uptime()),
      memory_usage: process.memoryUsage(),
      cpu_count: navigator.hardwareConcurrency || 4,
      hostname: window.location.hostname,
      environment: process.env.NODE_ENV || 'development',
      flask_version: '2.0.0',
      python_version: '3.9.0',
      database_version: 'SQLite 3.35.0'
    })
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

// 处理基本设置变更
const handleBasicChange = (hasChange) => {
  configChanges.basic = hasChange
}

// 处理定时任务变更
const handleSchedulerChange = (hasChange) => {
  configChanges.scheduler = hasChange
}

// 处理执行器变更
const handleExecutorChange = (hasChange) => {
  configChanges.executor = hasChange
}

// 处理通知变更
const handleNotificationChange = (hasChange) => {
  configChanges.notification = hasChange
}

// 处理存储变更
const handleStorageChange = (hasChange) => {
  configChanges.storage = hasChange
}

// 处理用户管理变更
const handleUsersChange = (hasChange) => {
  configChanges.users = hasChange
}

// 刷新配置
const handleRefresh = async () => {
  await ElMessageBox.confirm(
      '确定要刷新配置吗？未保存的更改将会丢失。',
      '刷新确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
  )
  await fetchSystemConfig()
}

// 保存所有更改
const handleSaveAll = async () => {
  try {
    saving.value = true

    // 验证并保存各个配置
    const savePromises = []

    if (configChanges.basic && basicSettingsRef.value) {
      savePromises.push(basicSettingsRef.value.save())
    }

    if (configChanges.scheduler && schedulerSettingsRef.value) {
      savePromises.push(schedulerSettingsRef.value.save())
    }

    if (configChanges.executor && executorSettingsRef.value) {
      savePromises.push(executorSettingsRef.value.save())
    }

    if (configChanges.notification && notificationSettingsRef.value) {
      savePromises.push(notificationSettingsRef.value.save())
    }

    if (configChanges.storage && storageSettingsRef.value) {
      savePromises.push(storageSettingsRef.value.save())
    }

    if (configChanges.users && userManagementRef.value) {
      savePromises.push(userManagementRef.value.save())
    }

    await Promise.all(savePromises)

    // 重置变更状态
    resetChanges()

    ElMessage.success('所有配置已保存')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 放弃更改
const handleDiscard = async () => {
  try {
    await ElMessageBox.confirm(
        '确定要放弃所有未保存的更改吗？',
        '放弃更改',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    // 重新加载配置
    await fetchSystemConfig()

    ElMessage.success('已放弃更改')
  } catch (error) {
    // 用户取消
  }
}

// 重置变更状态
const resetChanges = () => {
  Object.keys(configChanges).forEach(key => {
    configChanges[key] = false
  })
}

// 组件挂载
onMounted(() => {
  fetchSystemConfig()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.settings-title {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.settings-actions {
  display: flex;
  gap: 12px;
}

.settings-tabs {
  min-height: 600px;
}

.changes-notice {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px;
  z-index: 1000;
}

.changes-notice :deep(.el-alert) {
  padding: 12px 16px;
}

.changes-notice :deep(.el-alert__append) {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .settings-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .settings-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .changes-notice :deep(.el-alert__append) {
    flex-direction: column;
  }
}
</style>
