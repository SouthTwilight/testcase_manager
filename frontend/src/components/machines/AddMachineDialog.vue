<template>
  <el-dialog
      v-model="dialogVisible"
      title="添加机器"
      width="500px"
      :before-close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
    >
      <el-form-item label="机器名称" prop="machine_name">
        <el-input
            v-model="form.machine_name"
            placeholder="请输入机器名称"
        />
      </el-form-item>

      <el-form-item label="IP地址" prop="machine_ip">
        <el-input
            v-model="form.machine_ip"
            placeholder="请输入IP地址"
        />
        <div class="form-tip">
          机器的IP地址或主机名
        </div>
      </el-form-item>

      <el-form-item label="端口号" prop="machine_port">
        <el-input-number
            v-model="form.machine_port"
            :min="1"
            :max="65535"
            :step="1"
            style="width: 150px"
        />
      </el-form-item>

      <el-form-item label="最大任务数" prop="max_tasks">
        <el-input-number
            v-model="form.max_tasks"
            :min="1"
            :max="50"
            :step="1"
            style="width: 150px"
        />
        <div class="form-tip">
          机器能同时执行的最大任务数
        </div>
      </el-form-item>

      <el-form-item label="机器类型" prop="machine_type">
        <el-select
            v-model="form.machine_type"
            placeholder="请选择机器类型"
            style="width: 200px"
        >
          <el-option label="本地执行器" value="local" />
          <el-option label="远程执行器" value="remote" />
          <el-option label="Docker执行器" value="docker" />
          <el-option label="虚拟机" value="vm" />
        </el-select>
      </el-form-item>

      <el-form-item v-if="form.machine_type === 'docker'" label="Docker镜像">
        <el-input
            v-model="form.docker_image"
            placeholder="请输入Docker镜像名称"
        />
      </el-form-item>

      <el-form-item v-if="form.machine_type === 'remote'" label="认证方式">
        <el-radio-group v-model="form.auth_type">
          <el-radio label="ssh_key">SSH密钥</el-radio>
          <el-radio label="password">密码</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.auth_type === 'ssh_key'" label="SSH私钥">
        <el-input
            v-model="form.ssh_private_key"
            type="textarea"
            :rows="4"
            placeholder="请输入SSH私钥"
        />
      </el-form-item>

      <el-form-item v-if="form.auth_type === 'password'" label="密码">
        <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
        />
      </el-form-item>

      <el-form-item label="标签">
        <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="输入或选择标签"
            style="width: 100%"
        >
          <el-option label="linux" value="linux" />
          <el-option label="windows" value="windows" />
          <el-option label="macos" value="macos" />
          <el-option label="docker" value="docker" />
          <el-option label="ci" value="ci" />
        </el-select>
        <div class="form-tip">
          用于机器分组和筛选
        </div>
      </el-form-item>

      <el-form-item label="启用监控" prop="monitor_enabled">
        <el-switch
            v-model="form.monitor_enabled"
            active-text="启用"
            inactive-text="禁用"
        />
        <div class="form-tip">
          启用后系统会监控机器的资源使用情况
        </div>
      </el-form-item>

      <el-form-item v-if="form.monitor_enabled" label="心跳间隔(秒)" prop="heartbeat_interval">
        <el-input-number
            v-model="form.heartbeat_interval"
            :min="10"
            :max="300"
            :step="10"
            style="width: 150px"
        />
        <div class="form-tip">
          机器发送心跳的时间间隔
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        添加机器
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'

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

const loading = ref(false)
const formRef = ref()

const form = reactive({
  machine_name: '',
  machine_ip: '',
  machine_port: 5001,
  max_tasks: 5,
  machine_type: 'remote',
  docker_image: 'python:3.9-slim',
  auth_type: 'ssh_key',
  ssh_private_key: '',
  password: '',
  tags: ['linux'],
  monitor_enabled: true,
  heartbeat_interval: 30
})

const rules = {
  machine_name: [
    { required: true, message: '请输入机器名称', trigger: 'blur' }
  ],
  machine_ip: [
    { required: true, message: '请输入IP地址', trigger: 'blur' }
  ],
  max_tasks: [
    { required: true, message: '请输入最大任务数', trigger: 'blur' }
  ]
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 调用API添加机器
    // 这里模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success('机器添加成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('添加机器失败:', error)
    ElMessage.error('添加失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(form, {
    machine_name: '',
    machine_ip: '',
    machine_port: 5001,
    max_tasks: 5,
    machine_type: 'remote',
    docker_image: 'python:3.9-slim',
    auth_type: 'ssh_key',
    ssh_private_key: '',
    password: '',
    tags: ['linux'],
    monitor_enabled: true,
    heartbeat_interval: 30
  })
}

// 监听对话框状态
watch(dialogVisible, (val) => {
  if (!val) {
    resetForm()
  }
})
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
