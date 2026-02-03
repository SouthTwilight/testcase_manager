// api/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
    baseURL: 'http://localhost:5000',
    timeout: 30000,
    withCredentials: true // 如果需要携带 cookie
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 响应拦截器 - 修复版
service.interceptors.response.use(
    response => {
        const res = response.data

        // 如果后端返回统一的成功标识
        if (res.code === 200 || res.success === true) {
            return res
        }

        // 业务逻辑错误
        ElMessage({
            message: res.message || '请求失败',
            type: 'error',
            duration: 3000
        })

        return Promise.reject(new Error(res.message || '请求失败'))
    },
    error => {
        console.error('请求错误:', error)

        // 如果请求被取消，不显示错误消息
        if (axios.isCancel(error)) {
            return Promise.reject(error)
        }

        let message = '网络错误，请检查网络连接'

        if (error.response) {
            switch (error.response.status) {
                case 403:
                    message = '拒绝访问'
                    break

                case 404:
                    message = '请求的资源不存在'
                    break

                case 500:
                    message = '服务器内部错误'
                    break

                default:
                    message = error.response.data?.message || '请求失败'
            }
        } else if (error.request) {
            message = '网络连接失败，请检查网络'
        }

        // 显示错误消息（401 除外，因为已经跳转到登录页）
        if (error.response?.status !== 401) {
            ElMessage({
                message,
                type: 'error',
                duration: 3000
            })
        }

        return Promise.reject(error)
    }
)

export default service
