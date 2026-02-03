import request from './request'

export default {

    // 仪表板数据
    getDashboardStats() {
        return request.get('/api/dashboard-stats')
    },
    getTestCaseStats() {
        return request.get('/api/test-cases/stats')
    },
    getTestPlanStats() {
        return request.get('/api/test-plan-stats')
    },
    getExecutionTrend() {
        return request.get('/api/execution-trend')
    },
    getSystemHealth() {
        return request.get('/api/system-health')
    },
    getRecentActivities() {
        return request.get('/api/recent-activities')
    },

    // 测试用例管理
    getTestCases(params) {
        return request.get('/api/test-cases', { params })
    },
    getTestCase(caseHash) {
        return request.get(`/api/test-cases/${caseHash}`)
    },
    updateTestCase(caseHash, data) {
        return request.put(`/api/test-cases/${caseHash}`, data)
    },
    deleteTestCase(caseHash) {
        return request.delete(`/api/test-cases/${caseHash}`)
    },
    batchUpdateCases(data) {
        return request.put('/api/test-cases/batch', data)
    },
    batchDeleteCases(data) {
        return request.delete('/api/test-cases/batch', data)
    },
    scanCases(data) {
        return request.post('/api/test-cases/scan', data)
    },
    getCasePaths() {
        return request.get('/api/test-cases/paths')
    },
    scanTestCases() {
        return request.get('/api/scan-cases')
    },

    // 测试计划
    getTestPlans(params) {
        return request.get('/api/test-plans', { params })
    },
    getTestPlan(planId) {
        return request.get(`/api/test-plans/${planId}`)
    },
    updateTestPlan(planId, data) {
        return request.put(`/api/test-plans/${planId}`, data)
    },
    deleteTestPlan(planId) {
        return request.delete(`/api/test-plans/${planId}`)
    },
    pauseTestPlan(planId) {
        return request.post(`/api/test-plans/${planId}/pause`)
    },
    resumeTestPlan(planId) {
        return request.post(`/api/test-plans/${planId}/resume`)
    },
    executeTestPlan(data) {
        return request.post('/api/execute-plan', data)
    },
    getPlanTasks(planId, params) {
        return request.get(`/api/test-plans/${planId}/tasks`, { params })
    },

    // 执行历史
    getExecutionHistory(params) {
        return request.get('/api/execution-history', { params })
    },
    getExecutionDetail(executionId) {
        return request.get(`/api/execution-history/${executionId}`)
    },
    deleteExecution(executionId) {
        return request.delete(`/api/execution-history/${executionId}`)
    },
    clearExecutionHistory(data) {
        return request.post('/api/execution-history/clear', data)
    },
    getExecutionStats(params) {
        return request.get('/api/execution-history/stats', { params })
    },

    // 机器状态
    getMachines() {
        return request.get('/api/machines')
    },

    // 批量执行计划
    batchExecutePlans(data) {
        return request.post('/api/batch-execute-plans', data)
    },

    // 获取批量执行记录
    getBatchExecutions(params) {
        return request.get('/api/batch-executions', { params })
    },

    // 系统设置
    getSettings() {
        return request.get('/api/settings')
    },
    updateSettings(data) {
        return request.put('/api/settings', data)
    },
    resetSettings() {
        return request.post('/api/settings/reset')
    },
    getSchedulerStatus() {
        return request.get('/api/scheduler/status')
    },
    getSystemInfo() {
        return request.get('/api/system/info')
    }
}
