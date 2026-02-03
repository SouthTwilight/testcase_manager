<template>
  <el-tag
      :type="tagType"
      :effect="effect"
      :size="size"
      :class="['plan-status-tag', status]"
  >
    <el-icon v-if="showIcon && status === 'running'" :size="iconSize" class="status-icon">
      <Loading />
    </el-icon>
    <el-icon v-else-if="showIcon && status === 'completed'" :size="iconSize" class="status-icon">
      <CircleCheck />
    </el-icon>
    <el-icon v-else-if="showIcon && status === 'failed'" :size="iconSize" class="status-icon">
      <CircleClose />
    </el-icon>
    <el-icon v-else-if="showIcon && status === 'waiting'" :size="iconSize" class="status-icon">
      <Clock />
    </el-icon>
    {{ statusText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import {
  Loading,
  CircleCheck,
  CircleClose,
  Clock
} from '@element-plus/icons-vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['running', 'completed', 'failed', 'waiting', 'scheduled', 'paused'].includes(value)
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
  running: {
    text: '执行中',
    type: 'warning',
    color: '#1890ff'
  },
  completed: {
    text: '已完成',
    type: 'success',
    color: '#52c41a'
  },
  failed: {
    text: '已失败',
    type: 'danger',
    color: '#f5222d'
  },
  waiting: {
    text: '等待中',
    type: 'info',
    color: '#faad14'
  },
  scheduled: {
    text: '定时',
    type: 'warning',
    color: '#722ed1'
  },
  paused: {
    text: '已暂停',
    type: 'info',
    color: '#666'
  }
}

const tagType = computed(() => statusConfig[props.status]?.type || 'info')
const statusText = computed(() => statusConfig[props.status]?.text || props.status)
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
.plan-status-tag {
  font-weight: 500;
  border-radius: 12px;
  min-width: 60px;
  text-align: center;
}

.plan-status-tag.running {
  --el-tag-bg-color: #e6f7ff;
  --el-tag-border-color: #91d5ff;
  --el-tag-text-color: #1890ff;
}

.plan-status-tag.completed {
  --el-tag-bg-color: #f6ffed;
  --el-tag-border-color: #b7eb8f;
  --el-tag-text-color: #52c41a;
}

.plan-status-tag.failed {
  --el-tag-bg-color: #fff2f0;
  --el-tag-border-color: #ffccc7;
  --el-tag-text-color: #f5222d;
}

.plan-status-tag.waiting {
  --el-tag-bg-color: #fffbe6;
  --el-tag-border-color: #ffe58f;
  --el-tag-text-color: #faad14;
}

.plan-status-tag.scheduled {
  --el-tag-bg-color: #f9f0ff;
  --el-tag-border-color: #d3adf7;
  --el-tag-text-color: #722ed1;
}

.plan-status-tag.paused {
  --el-tag-bg-color: #fafafa;
  --el-tag-border-color: #d9d9d9;
  --el-tag-text-color: #666;
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
