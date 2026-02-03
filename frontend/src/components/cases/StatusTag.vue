<template>
  <el-tag
      :type="tagType"
      :effect="effect"
      :size="size"
      :class="['status-tag', status]"
  >
    <el-icon v-if="showIcon" :size="iconSize" class="status-icon">
      <component :is="statusIcon" />
    </el-icon>
    {{ statusText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import {
  CircleCheck,
  CircleClose,
  Clock,
  Loading
} from '@element-plus/icons-vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['passed', 'failed', 'not_executed', 'executing'].includes(value)
  },
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  },
  effect: {
    type: String,
    default: 'light',
    validator: (value) => ['dark', 'light', 'plain'].includes(value)
  },
  showIcon: {
    type: Boolean,
    default: true
  }
})

const statusConfig = {
  passed: {
    text: '通过',
    type: 'success',
    icon: CircleCheck,
    color: '#52c41a'
  },
  failed: {
    text: '失败',
    type: 'danger',
    icon: CircleClose,
    color: '#f5222d'
  },
  not_executed: {
    text: '未执行',
    type: 'warning',
    icon: Clock,
    color: '#faad14'
  },
  executing: {
    text: '执行中',
    type: 'warning',
    icon: Loading,
    color: '#1890ff'
  }
}

const tagType = computed(() => statusConfig[props.status]?.type || 'info')
const statusText = computed(() => statusConfig[props.status]?.text || props.status)
const statusIcon = computed(() => statusConfig[props.status]?.icon || CircleCheck)
const iconSize = computed(() => {
  const sizeMap = {
    large: 14,
    default: 12,
    small: 10
  }
  return sizeMap[props.size]
})
</script>

<style scoped>
.status-tag {
  font-weight: 500;
  border-radius: 12px;
}

.status-tag.passed {
  --el-tag-bg-color: #f6ffed;
  --el-tag-border-color: #b7eb8f;
  --el-tag-text-color: #52c41a;
}

.status-tag.failed {
  --el-tag-bg-color: #fff2f0;
  --el-tag-border-color: #ffccc7;
  --el-tag-text-color: #f5222d;
}

.status-tag.not_executed {
  --el-tag-bg-color: #fffbe6;
  --el-tag-border-color: #ffe58f;
  --el-tag-text-color: #faad14;
}

.status-tag.executing {
  --el-tag-bg-color: #e6f7ff;
  --el-tag-border-color: #91d5ff;
  --el-tag-text-color: #1890ff;
}

.status-icon {
  margin-right: 4px;
  vertical-align: -2px;
}

:deep(.el-icon.is-loading) {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
