<template>
  <el-dialog
      v-model="dialogVisible"
      title="批量执行"
      width="500px"
      :before-close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
    >
      <el-form-item label="计划名称" prop="name">
        <el-input
            v-model="form.name"
            placeholder="请输入计划名称"
        />
      </el-form-item>

      <el-form-item label="执行方式">
        <el-radio-group v-model="form.distributed">
          <el-radio :label="false">本地执行</el-radio>
          <el-radio :label="true">分布式执行</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="执行顺序">
        <el-select v-model="form.order_by" placeholder="选择排序方式">
          <el-option label="按状态优先" value="status" />
          <el-option label="按路径排序" value="path" />
          <el-option label="随机顺序" value="random" />
        </el-select>
      </el-form-item>

      <el-form-item label="并发数量" v-if="form.distributed">
        <el-slider
            v-model="form.concurrency"
            :min="1"
            :max="10"
            :step="1"
            show-stops
        />
        <div class="slider-value">{{ form.concurrency }} 台机器</div>
      </el-form-item>

      <el-form-item label="执行描述">
        <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入执行描述（可选）"
        />
      </el-form-item>

      <el-form-item label="选择用例">
        <div class="selected-cases">
          <el-tag
              v-for="item in selectedCases"
              :key="item.id"
              closable
              @close="removeCase(item.id)"
              class="case-tag"
          >
            {{ item.name }}
          </el-tag>
        </div>
        <div class="case-count">已选择 {{ selectedCases.length }} 个用例</div>
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
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  selectedCases: {
    type: Array,
    default: () => []
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
  name: `批量执行 ${new Date().toLocaleString()}`,
  distributed: false,
  order_by: 'status',
  concurrency: 3,
  description: '',
  include_paths: []
})

const rules = {
  name: [
    { required: true, message: '请输入计划名称', trigger: 'blur' }
  ]
}

// 从选中的用例中提取路径
const includePaths = computed(() => {
  const paths = new Set()
  props.selectedCases.forEach(caseItem => {
    if (caseItem.relative_path) {
      // 提取父目录
      const path = caseItem.relative_path.split('/').slice(0, -1).join('/')
      if (path) {
        paths.add(path)
      }
    }
  })
  return Array.from(paths)
})

const handleClose = () => {
  emit('update:modelValue', false)
}

const removeCase = (caseId) => {
  const index = props.selectedCases.findIndex(item => item.id === caseId)
  if (index !== -1) {
    // 这里需要通知父组件更新选中项
    // 实际实现可能需要emit事件
    ElMessage.warning('请在主表格中取消选择')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const submitData = {
      ...form,
      include_paths: includePaths.value,
      exclude_paths: []
    }

    const response = await api.executeTestPlan(submitData)

    if (response.success) {
      ElMessage.success('批量执行计划已创建')
      emit('success')
      handleClose()
    }
  } catch (error) {
    console.error('创建批量执行计划失败:', error)
    ElMessage.error('创建执行计划失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.distributed = false
  form.order_by = 'status'
  form.concurrency = 3
  form.description = ''
  form.include_paths = []
}

// 监听对话框显示状态
watch(dialogVisible, (val) => {
  if (val) {
    form.name = `批量执行 ${new Date().toLocaleString()}`
    form.include_paths = includePaths.value
  } else {
    resetForm()
  }
})
</script>

<style scoped>
.slider-value {
  text-align: center;
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

.selected-cases {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
  background: #fafafa;
}

.case-tag {
  margin: 4px;
}

.case-count {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
  text-align: center;
}
</style>
