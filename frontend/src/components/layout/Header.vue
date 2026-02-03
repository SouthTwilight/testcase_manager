<template>
  <div class="header-container">
    <div class="header-left">
      <div class="collapse-button" @click="toggleCollapse">
        <el-icon>
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
      </div>
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
          <span v-if="item.path" @click="handleBreadcrumbClick(item)">
            {{ item.meta.title || item.name }}
          </span>
          <span v-else>{{ item.meta.title || item.name }}</span>
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="header-right">
      <div class="user-info">
        <el-dropdown @command="handleCommand">
          <div class="user-dropdown">
            <el-avatar :size="32" :src="avatarUrl" class="user-avatar">
              {{ userInitial }}
            </el-avatar>
            <span class="username">admin</span>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  ArrowDown,
  User,
  SwitchButton
} from '@element-plus/icons-vue'

const emit = defineEmits(['toggle-collapse'])

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)

const userInitial = computed(() => {
  return 'U'
})
const avatarUrl = computed(() => {
  // 这里可以根据实际情况生成或获取头像URL
  return ''
})

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    name: item.name,
    meta: item.meta
  }))
})

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  emit('toggle-collapse')
}

const handleBreadcrumbClick = (item) => {
  if (item.path !== route.path) {
    router.push(item.path)
  }
}

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped>
.header-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-button {
  font-size: 18px;
  cursor: pointer;
  margin-right: 16px;
  color: #666;
  transition: color 0.3s;
}

.collapse-button:hover {
  color: #1890ff;
}

.breadcrumb {
  font-size: 14px;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  cursor: pointer;
}

.breadcrumb :deep(.el-breadcrumb__inner):hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  margin-left: 20px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f5f5;
}

.user-avatar {
  margin-right: 8px;
  background-color: #1890ff;
}

.username {
  font-size: 14px;
  color: #333;
  margin-right: 4px;
}

.dropdown-icon {
  font-size: 12px;
  color: #999;
}
</style>
