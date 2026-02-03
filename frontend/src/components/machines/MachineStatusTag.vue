<template>
  <el-tag
      :type="tagType"
      :effect="effect"
      :size="size"
      :class="['machine-status-tag', status]"
  >
    <el-icon v-if="showIcon" :size="iconSize" class="status-icon">
      <component :is="statusIcon" />
    </el-icon>
    {{ statusText }}
    <span v-if="showDetail && detailText" class="detail-text">
      ({{ detailText }})
    </span>
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import {
  CircleCheck,
  CircleClose,
  Loading,
  Warning
} from '@element-plus/icons-vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['online', 'offline', 'busy', 'warning', 'maintenance'].includes(value)
  },
  detail: {
    type: String,
    default: ''
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
  },
  showDetail: {
    type: Boolean,
    default: false
  }
})

const statusConfig = {
  online: {
    text: '在线',
    type: 'success',
    icon: CircleCheck,
    color: '#52c41a'
  },
  offline: {
    text: '离线',
    type: 'danger',
    icon: CircleClose,
    color: '#f5222d'
  },
  busy: {
    text: '繁忙',
    type: 'warning',
    icon: Loading,
    color: '#faad14'
  },
  warning: {
    text: '警告',
    type: 'warning',
    icon: Warning,
    color: '#faad14'
  },
  maintenance: {
    text: '维护中',
    type: 'info',
    icon: Warning,
    color: '#666'
  }
}

const tagType = computed(() => statusConfig[props.status]?.type || 'info')
const statusText = computed(() => statusConfig[props.status]?.text || props.status)
const detailText = computed(() => props.detail)
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
.machine-status-tag {
  font-weight: 500;
  border-radius: 12px;
}

.machine-status-tag.online {
  --el-tag-bg-color: #f6ffed;
  --el-tag-border-color: #b7eb8f;
  --el-tag-text-color: #52c41a;
}

.machine-status-tag.offline {
  --el-tag-bg-color: #fff2f0;
  --el-tag-border-color: #ffccc7;
  --el-tag-text-color: #f5222d;
}

.machine-status-tag.busy {
  --el-tag-bg-color: #fffbe6;
  --el-tag-border-color: #ffe58f;
  --el-tag-text-color: #faad14;
}

.machine-status-tag.warning {
  --el-tag-bg-color: #fffbe6;
  --el-tag-border-color: #ffe58f;
  --el-tag-text-color: #faad14;
}

.machine-status-tag.maintenance {
  --el-tag-bg-color: #fafafa;
  --el-tag-border-color: #d9d9d9;
  --el-tag-text-color: #666;
}

.status-icon {
  margin-right: 4px;
  vertical-align: -2px;
}

.detail-text {
  font-size: 0.8em;
  opacity: 0.8;
  margin-left: 2px;
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
