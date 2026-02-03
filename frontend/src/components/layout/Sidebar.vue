<template>
  <div class="sidebar">
    <div class="logo">
      <h1 v-show="!collapse">测试平台</h1>
    </div>

    <el-menu
        :default-active="activeMenu"
        :collapse="collapse"
        :collapse-transition="false"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
    >
      <el-menu-item index="/">
        <el-icon><Odometer /></el-icon>
        <span>仪表板</span>
      </el-menu-item>

      <el-menu-item index="/test-cases">
        <el-icon><Document /></el-icon>
        <span>测试用例</span>
      </el-menu-item>

      <el-menu-item index="/test-plans">
        <el-icon><List /></el-icon>
        <span>测试计划</span>
      </el-menu-item>

      <el-menu-item index="/execution-history">
        <el-icon><Clock /></el-icon>
        <span>执行历史</span>
      </el-menu-item>

      <el-menu-item index="/machines">
        <el-icon><Monitor /></el-icon>
        <span>机器状态</span>
      </el-menu-item>
    </el-menu>

    <div class="collapse-button" @click="$emit('toggle-collapse')">
      <el-icon>
        <Expand v-if="collapse" />
        <Fold v-else />
      </el-icon>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  collapse: Boolean
})

const emit = defineEmits(['toggle-collapse'])
const route = useRoute()

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta.activeMenu) {
    return meta.activeMenu
  }
  return path
})
</script>

<style scoped>
.sidebar {
  height: 100%;
  position: relative;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b2f3a;
  color: #fff;
  overflow: hidden;
}

.logo h1 {
  font-size: 18px;
  margin: 0;
  white-space: nowrap;
}

.el-menu {
  border-right: none;
  height: calc(100% - 100px);
}

.collapse-button {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b2f3a;
  color: #bfcbd9;
  cursor: pointer;
  transition: all 0.3s;
}

.collapse-button:hover {
  background: #263445;
  color: #fff;
}
</style>
