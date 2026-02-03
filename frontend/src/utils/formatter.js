import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 格式化时间
 * @param {string|Date} time - 时间
 * @param {string} format - 格式，默认：'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的时间
 */
export const formatTime = (time, format = 'YYYY-MM-DD HH:mm:ss') => {
    if (!time) return '-'
    return dayjs(time).format(format)
}

/**
 * 格式化相对时间
 * @param {string|Date} time - 时间
 * @returns {string} 相对时间
 */
export const formatRelativeTime = (time) => {
    if (!time) return '-'
    return dayjs(time).fromNow()
}

/**
 * 格式化持续时间（毫秒）
 * @param {number} duration - 持续时间（毫秒）
 * @returns {string} 格式化的时间
 */
export const formatDuration = (duration) => {
    if (!duration) return '0ms'

    if (duration < 1000) {
        return `${duration}ms`
    }

    if (duration < 60000) {
        return `${(duration / 1000).toFixed(2)}s`
    }

    const minutes = Math.floor(duration / 60000)
    const seconds = ((duration % 60000) / 1000).toFixed(1)
    return `${minutes}m ${seconds}s`
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化的文件大小
 */
export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'

    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 截断文本
 * @param {string} text - 文本
 * @param {number} length - 最大长度
 * @returns {string} 截断后的文本
 */
export const truncateText = (text, length = 50) => {
    if (!text) return ''
    if (text.length <= length) return text
    return text.substring(0, length) + '...'
}

/**
 * 格式化JSON字符串
 * @param {string} jsonStr - JSON字符串
 * @returns {string} 格式化后的JSON字符串
 */
export const formatJson = (jsonStr) => {
    try {
        const obj = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr
        return JSON.stringify(obj, null, 2)
    } catch (e) {
        return jsonStr
    }
}

/**
 * 格式化时间范围
 * @param {Array} timeRange - 时间范围数组 [start, end]
 * @returns {string} 格式化的时间范围
 */
export const formatTimeRange = (timeRange) => {
    if (!timeRange || timeRange.length !== 2) return '-'
    return `${formatTime(timeRange[0])} ~ ${formatTime(timeRange[1])}`
}
