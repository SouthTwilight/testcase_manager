<template>
  <div class="plan-progress">
    <!-- 进度条 -->
    <div class="progress-bar">
      <el-progress
          :percentage="progressPercentage"
          :color="progressColor"
          :stroke-width="8"
          :show-text="false"
          :indeterminate="isIndeterminate"
      />
    </div>

    <!-- 进度信息 -->
    <div class="progress-info">
      <div class="info-row">
        <span class="label">进度:</span>
        <span class="value">{{ progressText }}</span>
      </div>

      <div v-if="!isIndeterminate" class="info-row">
        <span class="label">用例:</span>
        <span class="value">
          {{ plan.executed_cases || 0 }}/{{ plan.total_cases || 0 }}
        </span>
      </div>

      <div v-if="plan.execution_duration" class="info-row">
        <span class="label">耗时:</span>
        <span class="value">{{ formatDuration(plan.execution_duration) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDuration } from '../../utils/formatter'

const props = defineProps({
  plan: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 计算进度百分比
const progressPercentage = computed(() => {
  if (!props.plan.total_cases || props.plan.total_cases === 0) {
    return 0
  }

  if (props.plan.status === 'completed') {
    return 100
  }

  if (props.plan.status === 'failed') {
    return Math.min((props.plan.executed_cases || 0) / props.plan.total_cases * 100, 100)
  }

  return Math.round((props.plan.executed_cases || 0) / props.plan.total_cases * 100)
})

// 判断是否是未确定状态
const isIndeterminate = computed(() => {
  return props.plan.status === 'running' && props.plan.total_cases === 0
})

// 进度条颜色
const progressColor = computed(() => {
  switch (props.plan.status) {
    case 'completed':
      return '#52c41a'
    case 'failed':
      return '#f5222d'
    case 'running':
      return '#1890ff'
    default:
      return '#faad14'
  }
})

// 进度文本
const progressText = computed(() => {
  if (props.plan.status === 'running' && isIndeterminate.value) {
    return '执行中...'
  }

  if (props.plan.status === 'completed') {
    return '已完成'
  }

  if (props.plan.status === 'failed') {
    return '已失败'
  }

  if (props.plan.status === 'waiting') {
    return '等待执行'
  }

  return `${progressPercentage.value}%`
})
</script>

<style scoped>
.plan-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar {
  width: 100%;
}

.progress-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.label {
  color: #999;
}

.value {
  color: #333;
  font-weight: 500;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
}
</style>
