import request from './request'

export default {

    // 仪表板数据
    getDashboardStats() {
        return request.get('/api/dashboard-stats')
    },
    getTestCaseStats() {
        return request.get('/api/test-cases/stats')
    },

    // 测试用例管理
    getTestCases(params) {
        return request.get('/api/test-cases', { params })
    },
    updateTestCase(caseHash, data) {
        return request.put(`/api/test-cases/${caseHash}`, data)
    },
    scanTestCases() {
        return request.get('/api/scan-cases')
    },

    // 测试计划
    getTestPlans(params) {
        return request.get('/api/test-plans', { params })
    },
    executeTestPlan(data) {
        return request.post('/api/execute-plan', data)
    },

    // 执行历史
    getExecutionHistory(params) {
        return request.get('/api/execution-history', { params })
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
    }
}
