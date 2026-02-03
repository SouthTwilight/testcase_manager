<template>
  <div class="executor-settings">
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="180px"
        label-position="left"
        :disabled="loading"
    >
      <!-- 执行器类型 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">执行器类型</h3>
          </div>
        </template>

        <el-form-item label="执行器类型" prop="executor_type">
          <el-radio-group v-model="form.executor_type">
            <el-radio label="local">本地执行器</el-radio>
            <el-radio label="distributed">分布式执行器</el-radio>
            <el-radio label="docker">Docker执行器</el-radio>
          </el-radio-group>
          <div class="form-tip">
            本地执行器：在本地服务器执行测试<br>
            分布式执行器：在多台机器上并行执行<br>
            Docker执行器：在Docker容器中隔离执行
          </div>
        </el-form-item>

        <el-form-item v-if="form.executor_type === 'distributed'" label="工作节点列表">
          <div class="worker-nodes">
            <div v-for="(node, index) in form.worker_nodes" :key="index" class="node-item">
              <el-input
                  v-model="node.host"
                  placeholder="节点地址"
                  style="width: 200px; margin-right: 8px;"
              />
              <el-input
                  v-model="node.port"
                  placeholder="端口"
                  style="width: 100px; margin-right: 8px;"
              />
              <el-input
                  v-model="node.weight"
                  placeholder="权重"
                  style="width: 100px; margin-right: 8px;"
              />
              <el-button
                  type="danger"
                  :icon="Delete"
                  circle
                  @click="removeWorkerNode(index)"
              />
            </div>
            <el-button
                type="primary"
                :icon="Plus"
                @click="addWorkerNode"
            >
              添加节点
            </el-button>
          </div>
        </el-form-item>

        <el-form-item v-if="form.executor_type === 'docker'" label="Docker配置">
          <el-input
              v-model="form.docker_image"
              placeholder="Docker镜像名称"
              style="width: 300px; margin-bottom: 12px;"
          />
          <el-input
              v-model="form.docker_registry"
              placeholder="镜像仓库地址"
              style="width: 300px;"
          />
        </el-form-item>
      </el-card>

      <!-- 资源限制 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">资源限制</h3>
          </div>
        </template>

        <el-form-item label="最大工作进程数" prop="max_workers">
          <el-input-number
              v-model="form.max_workers"
              :min="1"
              :max="form.executor_type === 'local' ? 8 : 32"
              :step="1"
              style="width: 150px"
          />
          <div class="form-tip">
            同时执行测试的最大进程数，根据执行器类型调整
          </div>
        </el-form-item>

        <el-form-item label="任务超时时间(秒)" prop="task_timeout">
          <el-input-number
              v-model="form.task_timeout"
              :min="60"
              :max="7200"
              :step="60"
              style="width: 150px"
          />
          <span class="unit-label">秒</span>
          <div class="form-tip">
            单个测试用例执行的最大时间，超时将被终止
          </div>
        </el-form-item>

        <el-form-item label="内存限制" prop="memory_limit">
          <el-input
              v-model="form.memory_limit"
              placeholder="如: 2G, 512M"
              style="width: 150px"
          />
          <div class="form-tip">
            每个测试进程的最大内存使用量
          </div>
        </el-form-item>

        <el-form-item label="CPU限制" prop="cpu_limit">
          <el-input
              v-model="form.cpu_limit"
              placeholder="如: 50%, 1.5"
              style="width: 150px"
          />
          <div class="form-tip">
            CPU使用限制，可以是百分比或核心数
          </div>
        </el-form-item>
      </el-card>

      <!-- 缓存配置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">缓存配置</h3>
          </div>
        </template>

        <el-form-item label="启用缓存" prop="enable_cache">
          <el-switch
              v-model="form.enable_cache"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            缓存测试结果和中间数据，提升重复执行效率
          </div>
        </el-form-item>

        <el-form-item v-if="form.enable_cache" label="缓存TTL(秒)" prop="cache_ttl">
          <el-input-number
              v-model="form.cache_ttl"
              :min="60"
              :max="86400"
              :step="300"
              style="width: 150px"
          />
          <span class="unit-label">秒</span>
          <div class="form-tip">
            缓存的有效时间，过期后自动清理
          </div>
        </el-form-item>

        <el-form-item v-if="form.enable_cache" label="最大缓存大小">
          <el-input
              v-model="form.max_cache_size"
              placeholder="如: 1G, 512M"
              style="width: 150px"
          />
          <div class="form-tip">
            缓存最大占用空间
          </div>
        </el-form-item>
      </el-card>

      <!-- 日志配置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">日志配置</h3>
          </div>
        </template>

        <el-form-item label="日志级别" prop="log_level">
          <el-select
              v-model="form.log_level"
              placeholder="请选择日志级别"
              style="width: 150px"
          >
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
          <div class="form-tip">
            记录日志的详细程度，DEBUG最详细，ERROR最简略
          </div>
        </el-form-item>

        <el-form-item label="日志保留时间" prop="log_retention">
          <el-input
              v-model="form.log_retention"
              placeholder="如: 30d, 6M, 1y"
              style="width: 150px"
          />
          <div class="form-tip">
            日志文件保留的时间，过期自动清理
          </div>
        </el-form-item>

        <el-form-item label="启用详细日志" prop="enable_verbose_log">
          <el-switch
              v-model="form.enable_verbose_log"
              active-text="启用"
              inactive-text="禁用"
          />
          <div class="form-tip">
            记录详细的执行过程日志，用于调试
          </div>
        </el-form-item>
      </el-card>

      <!-- 高级配置 -->
      <el-card class="settings-section">
        <template #header>
          <div class="section-header">
            <h3 class="section-title">高级配置</h3>
            <el-button type="text" @click="toggleAdvanced">
              {{ showAdvanced ? '隐藏' : '显示' }}高级选项
            </el-button>
          </div>
        </template>

        <div v-if="showAdvanced" class="advanced-config">
          <el-form-item label="执行环境变量">
            <div class="env-vars">
              <div v-for="(env, index) in form.env_vars" :key="index" class="env-item">
                <el-input
                    v-model="env.name"
                    placeholder="变量名"
                    style="width: 180px; margin-right: 8px;"
                />
                <el-input
                    v-model="env.value"
                    placeholder="变量值"
                    style="width: 180px; margin-right: 8px;"
                />
                <el-button
                    type="danger"
                    :icon="Delete"
                    circle
                    @click="removeEnvVar(index)"
                />
              </div>
              <el-button
                  type="primary"
                  :icon="Plus"
                  @click="addEnvVar"
              >
                添加环境变量
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="预执行脚本">
            <el-input
                v-model="form.pre_exec_script"
                type="textarea"
                :rows="4"
                placeholder="执行测试前运行的脚本"
            />
          </el-form-item>

          <el-form-item label="后执行脚本">
            <el-input
                v-model="form.post_exec_script"
                type="textarea"
                :rows="4"
                placeholder="执行测试后运行的脚本"
            />
          </el-form-item>
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
            :icon="VideoPlay"
            @click="handleTestExecutor"
        >
          测试执行器
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh, VideoPlay, Plus, Delete } from '@element-plus/icons-vue'

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
const showAdvanced = ref(false)

// 表单数据
const form = reactive({
  executor_type: 'local',
  worker_nodes: [
    { host: 'localhost', port: '5001', weight: '1' }
  ],
  docker_image: 'python:3.9-slim',
  docker_registry: '',
  max_workers: 4,
  task_timeout: 1800,
  memory_limit: '2G',
  cpu_limit: '50%',
  enable_cache: true,
  cache_ttl: 3600,
  max_cache_size: '1G',
  log_level: 'INFO',
  log_retention: '30d',
  enable_verbose_log: false,
  env_vars: [
    { name: 'PYTHONPATH', value: '/app' }
  ],
  pre_exec_script: '',
  post_exec_script: ''
})

// 验证规则
const rules = {
  executor_type: [
    { required: true, message: '请选择执行器类型', trigger: 'change' }
  ],
  max_workers: [
    { required: true, message: '请输入最大工作进程数', trigger: 'blur' }
  ],
  task_timeout: [
    { required: true, message: '请输入任务超时时间', trigger: 'blur' }
  ],
  log_level: [
    { required: true, message: '请选择日志级别', trigger: 'change' }
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

// 添加工作节点
const addWorkerNode = () => {
  form.worker_nodes.push({
    host: '',
    port: '5001',
    weight: '1'
  })
}

// 移除工作节点
const removeWorkerNode = (index) => {
  form.worker_nodes.splice(index, 1)
}

// 添加环境变量
const addEnvVar = () => {
  form.env_vars.push({
    name: '',
    value: ''
  })
}

// 移除环境变量
const removeEnvVar = (index) => {
  form.env_vars.splice(index, 1)
}

// 切换高级配置显示
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value
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

    ElMessage.success('执行器配置已保存')
  } catch (error) {
    console.error('保存执行器配置失败:', error)
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

// 测试执行器
const handleTestExecutor = () => {
  ElMessage.info('执行器测试已开始，请查看执行日志')
}

// 暴露保存方法供父组件调用
const save = async () => {
  await handleSave()
  return true
}

defineExpose({ save })
</script>

<style scoped>
.executor-settings {
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

.worker-nodes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-vars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.env-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.advanced-config {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

  .node-item,
  .env-item {
    flex-direction: column;
    align-items: stretch;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
