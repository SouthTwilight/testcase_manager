<template>
  <div class="machines-container">
    <!-- 监控头部 -->
    <div class="monitor-header">
      <h1 class="monitor-title">机器状态监控</h1>
      <div class="monitor-actions">
        <el-button
            type="primary"
            :icon="Plus"
            @click="handleAddMachine"
        >
          添加机器
        </el-button>
        <el-button
            type="success"
            :icon="Refresh"
            @click="handleRefresh"
            :loading="loading"
        >
          刷新状态
        </el-button>
        <el-button
            type="warning"
            :icon="Setting"
            @click="handleConfigure"
        >
          监控配置
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item total">
            <div class="stat-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总机器数</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item online">
            <div class="stat-icon">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.online }}</div>
              <div class="stat-label">在线</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item offline">
            <div class="stat-icon">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.offline }}</div>
              <div class="stat-label">离线</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item busy">
            <div class="stat-icon">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.busy }}</div>
              <div class="stat-label">繁忙</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item tasks">
            <div class="stat-icon">
              <el-icon><List /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_tasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item cpu">
            <div class="stat-icon">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.avg_cpu }}%</div>
              <div class="stat-label">平均CPU</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item memory">
            <div class="stat-icon">
              <el-icon><Memory /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.avg_memory }}%</div>
              <div class="stat-label">平均内存</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6" :md="3" :lg="3">
          <div class="stat-item uptime">
            <div class="stat-icon">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatUptime(stats.avg_uptime) }}</div>
              <div class="stat-label">平均运行时间</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 机器列表 -->
    <el-card>
      <div class="machines-grid">
        <div
            v-for="machine in machines"
            :key="machine.id"
            :class="['machine-card', getStatusClass(machine.status)]"
        >
          <div class="machine-header">
            <div class="machine-info">
              <div class="machine-name">
                <el-icon><Monitor /></el-icon>
                <span>{{ machine.machine_name }}</span>
              </div>
              <machine-status-tag :status="machine.status" />
            </div>
            <div class="machine-actions">
              <el-dropdown trigger="click" @command="handleMachineCommand(machine, $event)">
                <el-button type="text" :icon="More" circle />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="details">
                      <el-icon><View /></el-icon>
                      查看详情
                    </el-dropdown-item>
                    <el-dropdown-item command="restart">
                      <el-icon><RefreshRight /></el-icon>
                      重启服务
                    </el-dropdown-item>
                    <el-dropdown-item command="logs">
                      <el-icon><Document /></el-icon>
                      查看日志
                    </el-dropdown-item>
                    <el-dropdown-item divided command="edit">
                      <el-icon><Edit /></el-icon>
                      编辑配置
                    </el-dropdown-item>
                    <el-dropdown-item command="remove">
                      <el-icon><Delete /></el-icon>
                      移除机器
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <div class="machine-content">
            <div class="machine-meta">
              <div class="meta-item">
                <el-icon><Location /></el-icon>
                <span class="meta-label">IP地址:</span>
                <span class="meta-value">{{ machine.machine_ip }}</span>
              </div>
              <div class="meta-item">
                <el-icon><Clock /></el-icon>
                <span class="meta-label">最后心跳:</span>
                <span class="meta-value">{{ formatRelativeTime(machine.last_heartbeat) }}</span>
              </div>
              <div class="meta-item">
                <el-icon><List /></el-icon>
                <span class="meta-label">当前任务:</span>
                <span class="meta-value">{{ machine.current_tasks }}/{{ machine.max_tasks }}</span>
              </div>
            </div>

            <div class="machine-resources">
              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-label">CPU使用率</span>
                  <span class="resource-value">{{ machine.cpu_usage }}%</span>
                </div>
                <el-progress
                    :percentage="machine.cpu_usage"
                    :color="getCpuColor(machine.cpu_usage)"
                    :stroke-width="8"
                    :show-text="false"
                />
              </div>

              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-label">内存使用率</span>
                  <span class="resource-value">{{ machine.memory_usage }}%</span>
                </div>
                <el-progress
                    :percentage="machine.memory_usage"
                    :color="getMemoryColor(machine.memory_usage)"
                    :stroke-width="8"
                    :show-text="false"
                />
              </div>

              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-label">磁盘使用率</span>
                  <span class="resource-value">{{ machine.disk_usage }}%</span>
                </div>
                <el-progress
                    :percentage="machine.disk_usage"
                    :color="getDiskColor(machine.disk_usage)"
                    :stroke-width="8"
                    :show-text="false"
                />
              </div>
            </div>

            <div class="machine-tasks">
              <div class="tasks-header">
                <span>当前任务</span>
                <el-button
                    v-if="machine.current_tasks > 0"
                    type="text"
                    size="small"
                    @click.stop="handleViewTasks(machine)"
                >
                  查看详情
                </el-button>
              </div>
              <div v-if="machine.tasks && machine.tasks.length > 0" class="tasks-list">
                <div
                    v-for="task in machine.tasks.slice(0, 3)"
                    :key="task.id"
                    class="task-item"
                >
                  <el-tag
                      size="small"
                      :type="getTaskStatusType(task.status)"
                      class="task-tag"
                  >
                    {{ task.case_name || `任务 ${task.id}` }}
                  </el-tag>
                  <span class="task-progress">{{ task.progress }}%</span>
                </div>
                <div v-if="machine.tasks.length > 3" class="more-tasks">
                  等 {{ machine.tasks.length - 3 }} 个任务
                </div>
              </div>
              <div v-else class="no-tasks">
                <span>暂无任务</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="machines.length === 0" class="empty-state">
        <el-empty description="暂无机器信息">
          <el-button type="primary" @click="handleAddMachine">
            添加机器
          </el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 添加机器对话框 -->
    <add-machine-dialog
        v-model="addDialogVisible"
        @success="handleMachineAdded"
    />

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Refresh,
  Setting,
  More,
  View,
  RefreshRight,
  Document,
  Edit,
  Delete,
  Monitor,
  CircleCheck,
  CircleClose,
  Loading,
  List,
  Cpu,
  Memory,
  Timer,
  Location,
  Clock
} from '@element-plus/icons-vue'
import api from '../api'
import MachineStatusTag from '../components/machines/MachineStatusTag.vue'
import AddMachineDialog from '../components/machines/AddMachineDialog.vue'
import { formatRelativeTime } from '@/utils/formatter'

// 数据状态
const loading = ref(false)
const machines = ref([])

// 统计信息
const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  busy: 0,
  total_tasks: 0,
  avg_cpu: 0,
  avg_memory: 0,
  avg_uptime: 0
})

// 对话框状态
const addDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const configDialogVisible = ref(false)
const selectedMachineId = ref(null)

// 获取机器状态
const fetchMachines = async () => {
  try {
    loading.value = true

    const response = await api.getMachines()

    if (response.success) {
      machines.value = response.data.machines

      // 更新统计信息
      updateStats(response.data.machines)
    }
  } catch (error) {
    console.error('获取机器状态失败:', error)
    ElMessage.error('获取机器状态失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStats = (machinesList) => {
  const newStats = {
    total: machinesList.length,
    online: 0,
    offline: 0,
    busy: 0,
    total_tasks: 0,
    total_cpu: 0,
    total_memory: 0,
    total_uptime: 0
  }

  machinesList.forEach(machine => {
    if (machine.status === 'online') {
      newStats.online++
    } else if (machine.status === 'offline') {
      newStats.offline++
    }

    if (machine.current_tasks > 0) {
      newStats.busy++
    }

    newStats.total_tasks += machine.current_tasks || 0
    newStats.total_cpu += machine.cpu_usage || 0
    newStats.total_memory += machine.memory_usage || 0

    // 计算运行时间（如果有last_heartbeat）
    if (machine.last_heartbeat) {
      const uptime = Date.now() - new Date(machine.last_heartbeat).getTime()
      newStats.total_uptime += uptime
    }
  })

  newStats.avg_cpu = newStats.total > 0 ? Math.round(newStats.total_cpu / newStats.total) : 0
  newStats.avg_memory = newStats.total > 0 ? Math.round(newStats.total_memory / newStats.total) : 0
  newStats.avg_uptime = newStats.total > 0 ? Math.round(newStats.total_uptime / newStats.total / 1000) : 0

  Object.assign(stats, newStats)
}

// 格式化运行时间
const formatUptime = (seconds) => {
  if (!seconds) return '0秒'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return `${seconds}秒`
  }
}

// 获取状态CSS类
const getStatusClass = (status) => {
  switch (status) {
    case 'online': return 'status-online'
    case 'offline': return 'status-offline'
    case 'busy': return 'status-busy'
    case 'warning': return 'status-warning'
    default: return ''
  }
}

// 获取CPU进度条颜色
const getCpuColor = (usage) => {
  if (usage < 70) return '#52c41a'
  if (usage < 85) return '#faad14'
  return '#f5222d'
}

// 获取内存进度条颜色
const getMemoryColor = (usage) => {
  if (usage < 70) return '#1890ff'
  if (usage < 85) return '#faad14'
  return '#f5222d'
}

// 获取磁盘进度条颜色
const getDiskColor = (usage) => {
  if (usage < 80) return '#722ed1'
  if (usage < 90) return '#faad14'
  return '#f5222d'
}

// 获取任务状态类型
const getTaskStatusType = (status) => {
  switch (status) {
    case 'running': return 'warning'
    case 'success': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

// 刷新状态
const handleRefresh = () => {
  fetchMachines()
}

// 添加机器
const handleAddMachine = () => {
  addDialogVisible.value = true
}

// 机器添加成功
const handleMachineAdded = () => {
  fetchMachines()
  ElMessage.success('机器添加成功')
}

// 查看任务
const handleViewTasks = (machine) => {
  selectedMachineId.value = machine.id
  detailDrawerVisible.value = true
}

// 机器命令处理
const handleMachineCommand = (machine, command) => {
  switch (command) {
    case 'details':
      selectedMachineId.value = machine.id
      detailDrawerVisible.value = true
      break
    case 'restart':
      handleRestartMachine(machine)
      break
    case 'logs':
      handleViewLogs(machine)
      break
    case 'edit':
      handleEditMachine(machine)
      break
    case 'remove':
      handleRemoveMachine(machine)
      break
  }
}

// 重启机器服务
const handleRestartMachine = async (machine) => {
  try {
    // 调用重启API
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success(`正在重启 ${machine.machine_name}`)
  } catch (error) {
    console.error('重启失败:', error)
    ElMessage.error('重启失败')
  }
}

// 查看日志
const handleViewLogs = (machine) => {
  ElMessage.info(`查看 ${machine.machine_name} 的日志`)
}

// 编辑机器
const handleEditMachine = (machine) => {
  ElMessage.info(`编辑 ${machine.machine_name}`)
}

// 移除机器
const handleRemoveMachine = async (machine) => {
  try {
    // 调用移除API
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success(`已移除 ${machine.machine_name}`)
    fetchMachines()
  } catch (error) {
    console.error('移除失败:', error)
    ElMessage.error('移除失败')
  }
}

// 配置监控
const handleConfigure = () => {
  configDialogVisible.value = true
}

// 组件挂载
onMounted(() => {
  fetchMachines()

  // 设置定时刷新
  const intervalId = setInterval(fetchMachines, 30000)

  // 组件卸载时清理定时器
  return () => {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.machines-container {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.monitor-title {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.monitor-actions {
  display: flex;
  gap: 12px;
}

.stats-overview {
  margin-bottom: 16px;
}

.stat-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  transition: all 0.3s;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-item.total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-item.online .stat-icon {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
}

.stat-item.offline .stat-icon {
  background: linear-gradient(135deg, #f5222d 0%, #ff4d4f 100%);
}

.stat-item.busy .stat-icon {
  background: linear-gradient(135deg, #1890ff 0%, #69c0ff 100%);
}

.stat-item.tasks .stat-icon {
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
}

.stat-item.cpu .stat-icon {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

.stat-item.memory .stat-icon {
  background: linear-gradient(135deg, #13c2c2 0%, #36cfc9 100%);
}

.stat-item.uptime .stat-icon {
  background: linear-gradient(135deg, #eb2f96 0%, #f759ab 100%);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon .el-icon {
  font-size: 24px;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.machines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.machine-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s;
  overflow: hidden;
}

.machine-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.machine-card.status-online {
  border-top: 3px solid #52c41a;
}

.machine-card.status-offline {
  border-top: 3px solid #f5222d;
}

.machine-card.status-busy {
  border-top: 3px solid #1890ff;
}

.machine-card.status-warning {
  border-top: 3px solid #faad14;
}

.machine-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.machine-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.machine-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #333;
}

.machine-name .el-icon {
  color: #1890ff;
}

.machine-actions {
  display: flex;
  align-items: center;
}

.machine-content {
  padding: 16px;
}

.machine-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.meta-item .el-icon {
  color: #666;
  font-size: 14px;
}

.meta-label {
  color: #999;
  min-width: 60px;
}

.meta-value {
  color: #333;
  font-weight: 500;
}

.machine-resources {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.resource-label {
  font-size: 12px;
  color: #666;
}

.resource-value {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.machine-tasks {
  border-top: 1px solid #e8e8e8;
  padding-top: 12px;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tasks-header span {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.task-tag {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-progress {
  font-size: 11px;
  color: #666;
  font-weight: 500;
}

.more-tasks {
  font-size: 11px;
  color: #999;
  text-align: center;
  padding: 4px;
}

.no-tasks {
  text-align: center;
  padding: 8px;
  color: #999;
  font-size: 12px;
}

.empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .monitor-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .machines-grid {
    grid-template-columns: 1fr;
  }

  .stat-item {
    margin-bottom: 8px;
  }
}
</style>
