// Flask后端服务器地址
const API_CONFIG = {
  // Flask后端服务器地址
  BASE_URL: 'http://127.0.0.1:8000',
  
  // API endpoints
  ENDPOINTS: {
    // 获取设备
    GET_DEVICES: '/api/v1/devices/',
    // 添加设备
    ADD_DEVICE: '/api/v1/devices/',
    // 删除设备
    DELETE_DEVICE: '/api/v1/devices/',
    // 控制设备
    CONTROL_DEVICE: '/api/v1/devices/control/',

    // 获取消息列表
    GET_MESSAGES: '/api/v1/messages/',
    // 删除指定消息
    DELETE_MESSAGE: '/api/v1/messages/',

    // 获取传感器数据
    GET_ENVIRONMENT: '/api/v1/sensors/latest',
    GET_ENVIRONMENT_HISTORY: '/api/v1/sensors/latest/',

    // 获取所有日程
    GET_SCHEDULES: '/api/v1/schedules/',
    
    // 添加新日程
    ADD_SCHEDULE: '/api/v1/schedules',
    
    // 更新日程
    UPDATE_SCHEDULE: '/api/v1/schedules',
    
    // 删除日程
    DELETE_SCHEDULE: '/api/v1/schedules',
    
    // 获取指定日期的日程
    GET_SCHEDULES_BY_DATE: '/api/v1/schedules/date',
    
    // 获取本周日程统计
    GET_WEEK_STATS: '/schedules/week-stats'
  },
  
  // 请求超时时间（毫秒）
  TIMEOUT: 10000,

  // 请求头配置
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

export default API_CONFIG