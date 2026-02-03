<template>
  <el-dialog
      v-model="dialogVisible"
      title="执行测试计划"
      width="600px"
      :before-close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
    >
      <el-form-item label="计划名称" prop="name">
        <el-input
            v-model="form.name"
            placeholder="请输入计划名称"
            :prefix-icon="Document"
        />
      </el-form-item>

      <el-form-item label="包含路径" prop="include_paths">
        <el-select
            v-model="form.include_paths"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入包含的路径"
            style="width: 100%"
        >
          <el-option
              v-for="category in categories"
              :key="category"
              :label="category"
              :value="category"
          />
        </el-select>
        <div class="form-tip">留空表示包含所有路径</div>
      </el-form-item>

      <el-form-item label="排除路径" prop="exclude_paths">
        <el-select
            v-model="form.exclude_paths"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入排除的路径"
            style="width: 100%"
        >
          <el-option
              v-for="category in categories"
              :key="category"
              :label="category"
              :value="category"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="执行方式">
        <el-radio-group v-model="form.distributed">
          <el-radio :label="false">本地执行</el-radio>
          <el-radio :label="true">分布式执行</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="优先级设置">
        <el-checkbox-group v-model="form.priorities">
          <el-checkbox label="failed">优先执行失败用例</el-checkbox>
          <el-checkbox label="not_executed">优先执行未执行用例</el-checkbox>
          <el-checkbox label="recently_modified">优先执行最近修改用例</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        开始执行
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import api from '../../api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = ref(props.modelValue)
const loading = ref(false)
const formRef = ref()
const categories = ref([])

const form = reactive({
  name: `测试计划 ${new Date().toLocaleString()}`,
  include_paths: [],
  exclude_paths: [],
  distributed: false,
  priorities: ['failed', 'not_executed']
})

const rules = {
  name: [
    { required: true, message: '请输入计划名称', trigger: 'blur' }
  ]
}

// 获取目录列表
const fetchCategories = async () => {
  try {
    const response = await api.getTestCaseStats()
    if (response.success) {
      categories.value = response.data.stats.map(item => item.category)
    }
  } catch (error) {
    console.error('获取目录列表失败:', error)
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const submitData = {
      ...form,
      include_paths: form.include_paths.filter(path => path.trim()),
      exclude_paths: form.exclude_paths.filter(path => path.trim())
    }

    const response = await api.executeTestPlan(submitData)

    if (response.success) {
      ElMessage.success(response.message)
      emit('success')
      handleClose()

      // 重置表单
      formRef.value.resetFields()
      form.include_paths = []
      form.exclude_paths = []
      form.distributed = false
      form.priorities = ['failed', 'not_executed']
    }
  } catch (error) {
    console.error('提交计划失败:', error)
  } finally {
    loading.value = false
  }
}

// 监听modelValue变化
watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
  if (val) {
    fetchCategories()
  }
})

// 监听dialogVisible变化
watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
