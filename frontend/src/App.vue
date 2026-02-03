<template>
  <div id="app">
    <el-container class="main-container">
      <el-aside :width="isCollapse ? '64px' : '200px'">
        <Sidebar :collapse="isCollapse" @toggle-collapse="toggleCollapse" />
      </el-aside>
      <el-container>
        <el-header>
          <Header/>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import Sidebar from './components/layout/Sidebar.vue'
import Header from './components/layout/Header.vue'

const isCollapse = ref(false)


const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style>
#app {
  height: 100vh;
}

.main-container {
  height: 100vh;
}

.el-header {
  padding: 0;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.el-aside {
  background: #304156;
  transition: width 0.3s;
}

.el-main {
  padding: 20px;
  background: #f0f2f5;
}
</style>
