<template>
  <el-dialog
      v-model="dialogVisible"
      :title="`人工校验 - ${caseData?.name || ''}`"
      width="600px"
      :before-close="handleClose"
  >
    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        v-loading="loading"
    >
      <el-form-item label="用例名称">
        <el-input v-model="caseData.name" disabled />
      </el-form-item>

      <el-form-item label="当前状态">
        <status-tag :status="caseData.status" />
      </el-form-item>

      <el-form-item label="更新状态" prop="status">
        <el-radio-group v-model="form.status">
          <el-radio label="passed">通过</el-radio>
          <el-radio label="failed">失败</el-radio>
          <el-radio label="not_executed">未执行</el-radio>
          <el-radio label="blocked">阻塞</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="校验说明" prop="verification_notes">
        <el-input
            v-model="form.verification_notes"
            type="textarea"
            :rows="4"
            placeholder="请输入校验说明，例如：人工验证通过、已知问题等"
        />
      </el-form-item>

      <el-form-item label="详细结果" prop="result_details">
        <el-input
            v-model="form.result_details"
            type="textarea"
            :rows="6"
            placeholder="请输入详细结果（JSON格式或文本）"
        />
        <div class="form-tip">
          支持JSON格式，会自动格式化显示。例如：{"error": "详细错误信息", "screenshot": "截图路径"}
        </div>
      </el-form-item>

      <el-form-item label="人工修改标记">
        <el-switch
            v-model="form.is_manually_modified"
            active-text="已人工修改"
            inactive-text="未人工修改"
        />
        <div class="form-tip">
          标记为人工修改后，系统自动扫描不会覆盖此用例的状态
        </div>
      </el-form-item>

      <el-form-item label="校验人">
        <el-select v-model="form.user" placeholder="请选择校验人">
          <el-option
              v-for="item in userOptions"
              :key="item.value"
              :label="item.value"
              :value="item.value"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        保存修改
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'
import StatusTag from './StatusTag.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  caseData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const submitting = ref(false)
const formRef = ref()

const form = reactive({
  status: '',
  verification_notes: '',
  result_details: '',
  is_manually_modified: false,
  user:''
})

const userOptions = ref([
  { value: '聂啸林' },
  { value: '滕飞' },
  { value: '高志聪' },
  { value: '刘雯' },
  { value: '汤承宗' },
  { value: '周军' },
  { value: '黄伟亚' },
  { value: '王佳杰' }
])

const rules = {
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 初始化表单
const initForm = () => {
  if (props.caseData) {
    form.status = props.caseData.status || ''
    form.verification_notes = props.caseData.verification_notes || ''
    form.result_details = formatResultDetails(props.caseData.result_details)
    form.is_manually_modified = props.caseData.is_manually_modified || false
  }
}

// 格式化结果详情
const formatResultDetails = (details) => {
  if (!details) return ''

  try {
    if (typeof details === 'string') {
      const parsed = JSON.parse(details)
      return JSON.stringify(parsed, null, 2)
    }
    return JSON.stringify(details, null, 2)
  } catch (e) {
    return details
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // 准备提交数据
    const submitData = { ...form }

    // 尝试格式化结果详情
    if (submitData.result_details) {
      try {
        submitData.result_details = JSON.parse(submitData.result_details)
      } catch (e) {
        // 如果不是JSON格式，保持原样
      }
    }

    const response = await api.updateTestCase(props.caseData.case_hash, submitData)

    if (response.success) {
      ElMessage.success('用例已更新')
      emit('success')
      handleClose()
    }
  } catch (error) {
    console.error('更新用例失败:', error)
    ElMessage.error('更新用例失败')
  } finally {
    submitting.value = false
  }
}

// 监听对话框显示状态
watch(dialogVisible, (val) => {
  if (val && props.caseData) {
    initForm()
  }
})

// 监听caseData变化
watch(() => props.caseData, () => {
  if (props.caseData) {
    initForm()
  }
}, { deep: true })
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
