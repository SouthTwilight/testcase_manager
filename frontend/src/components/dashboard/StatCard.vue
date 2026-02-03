<template>
  <el-card class="stat-card" :class="{ loading }">
    <div class="stat-content">
      <div class="stat-icon" :style="{ backgroundColor: color + '20' }">
        <el-icon :color="color" :size="24">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-title">{{ title }}</div>
        <div class="stat-value">
          <count-up
              v-if="!loading"
              :end-value="value"
              :duration="2"
              class="value-text"
          />
          <span v-else class="skeleton-value"></span>
        </div>
        <div v-if="!loading" class="stat-footer">
          <slot name="footer"></slot>
        </div>
        <div v-else class="skeleton-footer"></div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { defineProps } from 'vue'
import CountUp from '../common/CountUp.vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: '#1890ff'
  },
  loading: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.stat-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  height: 120px;
}

.stat-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  margin-bottom: 8px;
}

.value-text {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-footer {
  font-size: 12px;
  color: #999;
}

/* 加载状态样式 */
.stat-card.loading .skeleton-value {
  display: block;
  width: 80px;
  height: 32px;
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 50%, #f2f2f2 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
}

.stat-card.loading .skeleton-footer {
  display: block;
  width: 120px;
  height: 14px;
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 50%, #f2f2f2 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 2px;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
