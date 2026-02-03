<template>
  <div class="category-stats">
    <el-table
        :data="data"
        size="small"
        :show-header="false"
        :row-class-name="tableRowClassName"
        @row-click="handleRowClick"
    >
      <el-table-column prop="category" label="目录">
        <template #default="{ row }">
          <div class="category-item">
            <el-icon class="folder-icon"><Folder /></el-icon>
            <span class="category-name">{{ row.category || '未分类' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="total" label="总数" width="80" align="right">
        <template #default="{ row }">
          <span class="stat-number">{{ row.total }}</span>
        </template>
      </el-table-column>
      <el-table-column label="通过率" width="120" align="right">
        <template #default="{ row }">
          <el-progress
              :percentage="row.pass_rate"
              :stroke-width="6"
              :show-text="false"
          />
          <span class="pass-rate">{{ row.pass_rate }}%</span>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!data || data.length === 0" class="empty-state">
      <el-empty description="暂无目录统计信息" />
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['category-click'])
const router = useRouter()

const tableRowClassName = ({ row }) => {
  if (row.pass_rate >= 90) return 'success-row'
  if (row.pass_rate >= 70) return 'warning-row'
  return 'error-row'
}

const handleRowClick = (row) => {
  emit('category-click', row.category)
  router.push({
    path: '/test-cases',
    query: { path: row.category }
  })
}
</script>

<style scoped>
.category-stats {
  height: 100%;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.folder-icon {
  color: #ffa940;
}

.category-name {
  font-size: 12px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-number {
  font-weight: bold;
  color: #1890ff;
}

.pass-rate {
  font-size: 12px;
  color: #666;
  margin-left: 8px;
}

:deep(.success-row) {
  --el-table-tr-bg-color: #f6ffed;
}

:deep(.warning-row) {
  --el-table-tr-bg-color: #fffbe6;
}

:deep(.error-row) {
  --el-table-tr-bg-color: #fff2f0;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
