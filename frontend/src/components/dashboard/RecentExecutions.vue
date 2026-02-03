<template>
  <div class="recent-executions">
    <div v-if="data && data.length > 0">
      <div v-for="item in data" :key="item.id" class="execution-item">
        <div class="execution-header">
          <div class="case-info">
            <el-tag
                size="small"
                :type="getStatusType(item.status)"
                class="status-tag"
            >
              {{ getStatusText(item.status) }}
            </el-tag>
            <span class="case-hash">{{ formatCaseHash(item.case_hash) }}</span>
          </div>
          <span class="duration">{{ item.duration }}ms</span>
        </div>

        <div class="execution-details">
          <div class="detail-item">
            <el-icon size="12"><User /></el-icon>
            <span>{{ item.executed_by || '系统' }}</span>
          </div>
          <div class="detail-item">
            <el-icon size="12"><Clock /></el-icon>
            <span>{{ formatTime(item.execution_time) }}</span>
          </div>
          <div v-if="item.machine_id" class="detail-item">
            <el-icon size="12"><Monitor /></el-icon>
            <span>{{ item.machine_id }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无执行记录" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import { User, Clock, Monitor } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const getStatusType = (status) => {
  switch (status) {
    case 'passed': return 'success'
    case 'failed': return 'danger'
    case 'executing': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status) => {
  const map = {
    'passed': '通过',
    'failed': '失败',
    'executing': '执行中',
    'not_executed': '未执行'
  }
  return map[status] || status
}

const formatCaseHash = (hash) => {
  if (!hash) return ''
  return hash.substring(0, 8) + '...'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = dayjs(time)
  const now = dayjs()

  if (date.isSame(now, 'day')) {
    return date.format('HH:mm:ss')
  } else if (date.isSame(now.subtract(1, 'day'), 'day')) {
    return '昨天 ' + date.format('HH:mm')
  } else {
    return date.format('MM-DD HH:mm')
  }
}
</script>

<style scoped>
.recent-executions {
  height: 100%;
}

.execution-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.execution-item:hover {
  background-color: #fafafa;
}

.execution-item:last-child {
  border-bottom: none;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.case-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  min-width: 50px;
  text-align: center;
}

.case-hash {
  font-size: 12px;
  color: #666;
  font-family: 'Monaco', 'Consolas', monospace;
}

.duration {
  font-size: 12px;
  color: #999;
  font-weight: 500;
}

.execution-details {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: #999;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.empty-state {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
