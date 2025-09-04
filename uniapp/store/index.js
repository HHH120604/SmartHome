import Vue from 'vue'
import Vuex from 'vuex'
import API_CONFIG from '../utils/api-config';
import steps from 'uview-ui/libs/config/props/steps';

Vue.use(Vuex)

// 生成初始的模拟历史数据 
// function generateInitialHistoryData(baseValue, count, variation, type) {
//   const data = [];
//   const now = new Date();
//   const minValue = type === 'temperature' ? 16 : 20;
//   const maxValue = type === 'temperature' ? 35 : 80;
  
//   // 生成count个历史数据点，模拟过去一段时间的数据
//   for (let i = count - 1; i >= 0; i--) {
//     const time = new Date(now);
//     time.setMinutes(now.getMinutes() - i * 5); // 每5分钟一个点
    
//     // 生成有波动的值，越新的数据越接近当前值
//     const normalizedI = i / (count - 1);
//     const adaptiveVariation = normalizedI * variation;
//     const value = Math.max(minValue, Math.min(maxValue, baseValue + (Math.random() - 0.5) * adaptiveVariation));
    
//     data.push({
//       time: time.toISOString(),
//       value: Number(value.toFixed(1))
//     });
//   }
  
//   return data;
// }

function control_device(username, devices)
{
  let data = [];
  devices.forEach(device => {
    device.status.power = device.on ? true : false;
    data.push({
      "device_id": device.id,
      "status": device.status,
    });
  });
  // console.log(data);
  try {
    uni.request({
      url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CONTROL_DEVICE}` + username,
      method: 'POST',
      timeout: API_CONFIG.TIMEOUT,
      data: data,
      success: (res) => {
        if (res.statusCode === 200) {
          // 为每条消息添加read字段，默认为false（未读）
        }
      },
      fail: (err) => {
        console.error('控制设备失败:', err)
        // 可以在这里添加重试逻辑或提示用户
      }
    })
  } catch (error) {
    console.error('控制设备异常:', error)
  }
}

export default new Vuex.Store({
  state: {
    // 当前登录用户
    currentUser: null,
    // 用户设备状态：按用户组织设备
    userDevices: {},
    // 当前激活的模式
    currentMode: null,
    // 完整环境数据（支持温湿度、可燃气体、火焰、烟雾）
    environment: {
      temp: 25,          // 温度(℃)
      humidity: 50,      // 湿度(%)
      gasConcentration: 3, // 可燃气体浓度(ppm)
      flameLevel: 0,     // 火焰等级(0-5)
      // smokeLevel: 0,     // 烟雾等级(0-5)
      // 主页用温湿度状态标识
      tempStatus: 'normal',  // low, normal, high
      humidityStatus: 'normal' // dry, normal, wet
    },
    // 消息数据
    messages: [],
    // 环境历史数据存储结构 - 三个不同粒度的数据
    environmentHistory: {
      // 10分钟粒度数据（保存最近3小时）
      '10min': {
        temperature: [], // 温度数据
        humidity: []     // 湿度数据
      },
      // 小时粒度数据（保存最近24小时）
      'hourly': {
        temperature: [],
        humidity: []
      },
      // 天粒度数据（保存最近15天）
      'daily': {
        temperature: [],
        humidity: []
      }
    },
    // 上次保存10分钟粒度数据的时间
    lastTenMinuteSaveTime: null,
    // 日程数据（按用户组织）
    userSchedules: {},
    // 全局日程数据（用于兼容性）
    schedules: [
      {
        id: 1,
        date: '2025-08-31',
        time: '09:00',
        title: '团队晨会',
        description: '讨论本周工作计划',
        location: '会议室A',
        priority: 'high',
        reminder: '15',
        completed: false
      },
      {
        id: 2,
        date: '2025-08-31',
        time: '14:30',
        title: '客户拜访',
        description: '洽谈合作事宜',
        location: '客户公司',
        priority: 'medium',
        reminder: '30',
        completed: false
      },
      {
        id: 3,
        date: '2025-08-31',
        time: '18:00',
        title: '健身房锻炼',
        description: '',
        location: '星光健身房',
        priority: 'low',
        reminder: 'none',
        completed: true
      },
      {
        id: 4,
        date: '2025-09-01',
        time: '10:00',
        title: '项目评审会',
        description: '智能家居项目中期评审',
        location: '大会议室',
        priority: 'high',
        reminder: '60',
        completed: false
      },
      {
        id: 5,
        date: '2025-09-02',
        time: '15:00',
        title: '产品设计讨论',
        description: 'UI/UX优化方案讨论',
        location: '设计部',
        priority: 'medium',
        reminder: '15',
        completed: false
      }
    ]
  },
  getters: {
      // 检查是否登录
      isLoggedIn: (state) => {
        return !!state.currentUser;
      },
      // 获取当前用户ID
      getCurrentUserId: (state) => {
        return state.currentUser ? state.currentUser.username : null;
      },
      // 获取当前用户的所有设备
      getCurrentUserDevices: (state) => {
        const userId = state.currentUser ? state.currentUser.username : null;
        return userId && state.userDevices[userId] ? state.userDevices[userId] : {};
      },
      // 获取当前用户按ID的设备
      getCurrentUserDeviceById: (state) => (id) => {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][id]) {
          return state.userDevices[userId][id];
        }
        return null;
      },
      // 获取当前用户按场景的设备
      getCurrentUserDevicesByScene: (state) => (scene) => {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userDevices[userId]) {
          return [];
        }
        return Object.values(state.userDevices[userId]).filter(device => 
          scene === '全屋' || device.scene === scene
        );
      },
      // 当前用户设备统计
      getCurrentUserTotalDeviceCount: (state, getters) => {
        return Object.keys(getters.getCurrentUserDevices).length;
      },
      getCurrentUserOnlineDeviceCount: (state, getters) => {
        return Object.values(getters.getCurrentUserDevices).filter(d => d.online).length;
      },
      getCurrentUserActiveDeviceCount: (state, getters) => {
        return Object.values(getters.getCurrentUserDevices).filter(d => d.on && d.online).length;
      },
      // 主页用环境数据（仅返回温湿度+状态）
      getEnvironment: (state) => ({
        temp: state.environment.temp,
        humidity: state.environment.humidity,
        tempStatus: state.environment.tempStatus,
        humidityStatus: state.environment.humidityStatus
      }),
      // 环境监测页用完整环境数据（所有监测项）
      getFullEnvironment: (state) => state.environment,
      // 当前激活模式
      getCurrentMode: (state) => state.currentMode,
      // 按ID获取设备
      getDeviceById: (state) => (id) => {
        // 检查用户设备
        if (state.userDevices[id]) {
          return state.userDevices[id]
        }
        return null
      },
      // 按场景获取设备
      getDevicesByScene: (state) => (scene) => {
        // 只返回用户设备
        return Object.values(state.userDevices).filter(device => 
          scene === '全屋' || device.scene === scene
        )
      },
      // 设备统计
      getTotalDeviceCount: (state) => Object.keys(state.userDevices).length,
      getOnlineDeviceCount: (state) => Object.values(state.userDevices).filter(d => d.online).length,
      getActiveDeviceCount: (state) => Object.values(state.userDevices).filter(d => d.on && d.online).length,
      // 获取所有灯光设备
      getAllLights: (state, getters) => {
        return Object.values(getters.getCurrentUserDevices).filter(device => device.id.includes('light_'))
      },
      
      // 日程相关getters
      // 获取当前用户的所有日程
      getCurrentUserSchedules: (state) => {
        const userId = state.currentUser ? state.currentUser.username : null;
        // 如果用户有专属日程，返回用户日程；否则返回全局日程
        if (userId && state.userSchedules[userId] && state.userSchedules[userId].length > 0) {
          return state.userSchedules[userId];
        }
        return state.schedules;
      },
      
      // 根据日期获取日程
      getSchedulesByDate: (state, getters) => (date) => {
        return getters.getCurrentUserSchedules.filter(schedule => schedule.date === date);
      },
      
      // 获取有日程的所有日期
      getDatesWithSchedules: (state, getters) => {
        const schedules = getters.getCurrentUserSchedules;
        const dates = [...new Set(schedules.map(schedule => schedule.date))];
        return dates;
      },
      
      // 获取环境历史数据
      getEnvironmentHistory: (state) => (granularity, type) => {
        if (state.environmentHistory[granularity] && state.environmentHistory[granularity][type]) {
          return state.environmentHistory[granularity][type];
        }
        return [];
      },
      
      // 获取消息
      getMessages: (state) => {
        return state.messages;
      },
      
      // 获取未读消息数量
      getUnreadMessageCount: (state) => {
        return state.messages.filter(msg => !msg.read).length;
      }
    },
    mutations: {
      // 设置当前用户
      SET_CURRENT_USER(state, user) {
        state.currentUser = user;
        // 确保该用户的设备集合存在，但不初始化任何默认设备
        if (user && !state.userDevices[user.username]) {
          state.userDevices[user.username] = {};
        }
      },
      // 清除当前用户
      CLEAR_CURRENT_USER(state) {
        state.currentUser = null;
        state.currentMode = null;
      },
      INIT_DEVICES(state) {
        // const user = uni.getStorageSync("currentUser");
        const username = state.currentUser ? state.currentUser.username : null;
        try {
          uni.request({
            url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_DEVICES}` + username,
            method: 'GET',
            timeout: API_CONFIG.TIMEOUT,
            success: (res) => {
              if (res.statusCode === 200) {
                // 为每条消息添加read字段，默认为false（未读）
                state.userDevices = res.data;
                Object.values(state.userDevices[username]).forEach(device => {
                  if (device.type === "light")
                  {
                    device.iconOff = "/static/icon/light_off.png";
                    device.iconOn = "/static/icon/light_on.png";
                  }
                  else if (device.type === "air")
                  {
                    device.iconOff = "/static/icon/air_off.png";
                    device.iconOn = "/static/icon/air_on.png";
                  }
                  else if (device.type === "shower")
                  {
                    device.iconOff = "/static/icon/shower_off.png";
                    device.iconOn = "/static/icon/shower_on.png";
                  }
                });
              }
            },
            fail: (err) => {
              console.error('获取消息失败:', err)
              // 可以在这里添加重试逻辑或提示用户
            }
          })
        } catch (error) {
          console.error('获取消息异常:', error)
        }
      },
      // 1. 切换设备开关状态（适配用户设备隔离）
      TOGGLE_DEVICE_ON(state, deviceId) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][deviceId]) {
          const device = state.userDevices[userId][deviceId];
          device.on = !device.on;
          control_device(userId, Object.values(state.userDevices[userId]).filter(device => device.on));
          // 根据设备类型更新描述
          if (device.type === 'light') {
            device.desc = device.on ? '已开启' : '已关闭';
          } else if (device.type === 'shower') {
            device.desc = device.on ? '正常运行' : '已关闭';
          } else if (device.type === 'air') {
            // 空调设备保持原有描述逻辑
            const modeText = { cool: '制冷', heat: '制热', auto: '自动' };
            if (device.on) {
              device.desc = `${modeText[device.status.mode || 'auto']} ${device.status.temp || 25}℃`;
            } else {
              device.desc = '已关闭';
            }
          }
        }
      },
      // 2. 空调温度更新（适配用户设备隔离）
      SET_AIR_TEMP(state, { deviceId, temp }) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][deviceId] && state.userDevices[userId][deviceId].type === 'air') {
          const device = state.userDevices[userId][deviceId];
          device.status.temp = temp;
          const modeText = { cool: '制冷', heat: '制热', auto: '自动' };
          device.desc = `${modeText[device.status.mode || 'auto']} ${temp}℃`;
        }
      },
      // 3. 空调模式更新（适配用户设备隔离）
      SET_AIR_MODE(state, { deviceId, mode }) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][deviceId] && state.userDevices[userId][deviceId].type === 'air') {
          const device = state.userDevices[userId][deviceId];
          device.status.mode = mode;
          const modeText = { cool: '制冷', heat: '制热', auto: '自动' };
          device.desc = `${modeText[mode]} ${device.status.temp || 25}℃`;
        }
      },
      // 4. 淋浴设备温度更新（适配用户设备隔离）
      SET_SHOWER_TEMP(state, { deviceId, temp }) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][deviceId] && state.userDevices[userId][deviceId].type === 'shower') {
          const device = state.userDevices[userId][deviceId];
          device.status.temp = temp;
          device.desc = `水温 ${temp}℃`;
        }
      },
      // 5. 更新完整环境数据（新增：支持所有监测项）
      UPDATE_FULL_ENVIRONMENT(state) {
        // 发送请求
        uni.request({
          url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_ENVIRONMENT}`,
          method: 'GET',
          timeout: API_CONFIG.TIMEOUT,
          success: (res) => {
            if (res.statusCode === 200 && res.data) {
              // console.log(res.data);
              state.environment = res.data;
              state.environment.flameLevel = state.environment.flameLevel ? 2 : 1;
            } else {
              // 处理错误响应
              console.error('获取环境数据失败:', res);
            }
          },
          fail: (err) => {
            console.error('请求环境数据网络失败:', err);
          },
        });
        
        // 同步更新温湿度状态标识（供主页使用）
        // 温度状态：<20低，20-26正常，>26高
        if (state.environment.temp < 20) {
          state.environment.tempStatus = 'low'
        } else if (state.environment.temp > 26) {
          state.environment.tempStatus = 'high'
        } else {
          state.environment.tempStatus = 'normal'
        }
        
        // 湿度状态：<30干，30-60正常，>60湿
        if (state.environment.humidity < 30) {
          state.environment.humidityStatus = 'dry'
        } else if (state.environment.humidity > 60) {
          state.environment.humidityStatus = 'wet'
        } else {
          state.environment.humidityStatus = 'normal'
        }
      },
      // 6. 激活模式（适配用户设备隔离）
      ACTIVATE_MODE(state, modeName) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userDevices[userId]) {
          return;
        }
        
        state.currentMode = modeName;
        
        // 模式配置简化，只保留基本功能
        const modeConfig = {
          '夜晚': {
            light: { on: false },
            air: { on: true, temp: 26, mode: 'auto' },
            shower: { on: false }
          },
          '离家': {
            light: { on: false },
            air: { on: false },
            shower: { on: false }
          },
          '回家': {
            light: { on: true },
            air: { on: true, temp: 26, mode: 'cool' },
            shower: { on: false }
          },
          '起床': {
            light: { on: true },
            air: { on: true, temp: 26, mode: 'cool' },
            shower: { on: false }
          }
        }
        
        if (modeConfig[modeName]) {
          Object.keys(state.userDevices[userId]).forEach(deviceId => {
            const device = state.userDevices[userId][deviceId];
            const deviceType = device.type;
            
            // 根据设备类型应用对应的模式配置
            if (modeConfig[modeName][deviceType]) {
              const config = modeConfig[modeName][deviceType];
              Object.assign(device, config);
              
              if (deviceType === 'light') {
                device.desc = device.on ? '已开启' : '已关闭';
              } else if (deviceType === 'air') {
                const modeText = { cool: '制冷', heat: '制热', auto: '自动' };
                device.desc = `${modeText[device.status.mode]} ${device.status.temp}℃`;
              } else if (deviceType === 'shower') {
                device.desc = `水温 ${device.status.temp}℃`;
              }
            }
          });
        }
      },
      // 7. 取消激活模式（同时关闭该模式下打开的设备）
      DEACTIVATE_MODE(state) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userDevices[userId] || !state.currentMode) {
          state.currentMode = null;
          return;
        }
        
        // 记录要取消的模式
        const modeToDeactivate = state.currentMode;
        
        // 模式配置（与ACTIVATE_MODE保持一致）
        const modeConfig = {
          '夜晚': {
            light: { on: false },
            air: { on: true, temp: 26, mode: 'auto' },
            shower: { on: false }
          },
          '离家': {
            light: { on: false },
            air: { on: false },
            shower: { on: false }
          },
          '回家': {
            light: { on: true },
            air: { on: true, temp: 26, mode: 'cool' },
            shower: { on: false }
          },
          '起床': {
            light: { on: true },
            air: { on: true, temp: 26, mode: 'cool' },
            shower: { on: false }
          }
        }
        
        // 如果该模式有配置且包含需要关闭的设备
        if (modeConfig[modeToDeactivate]) {
          Object.keys(state.userDevices[userId]).forEach(deviceId => {
            const device = state.userDevices[userId][deviceId];
            const deviceType = device.type;
            
            // 根据设备类型检查该模式下是否需要关闭
            if (modeConfig[modeToDeactivate][deviceType] && modeConfig[modeToDeactivate][deviceType].on) {
              // 关闭在该模式下被打开的设备
              device.on = false;
              
              // 更新设备描述
              if (deviceType === 'light') {
                device.desc = '已关闭';
              } else if (deviceType === 'air') {
                device.desc = '已关闭';
              } else if (deviceType === 'shower') {
                device.desc = '已关闭';
              }
            }
          });
        }
        
        // 最后取消模式状态
        state.currentMode = null
      },
      // 8. 重命名设备（适配用户设备隔离）
      RENAME_DEVICE(state, { id, name }) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (userId && state.userDevices[userId] && state.userDevices[userId][id]) {
          state.userDevices[userId][id].name = name;
        }
      },
      // 9. 删除设备（适配用户设备隔离）
      DELETE_DEVICE(state, deviceId) {
        const username = state.currentUser ? state.currentUser.username : null;
        if (!username) {
          return;
        };
        try {
          uni.request({
            url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DELETE_DEVICE}` + username + '/' + deviceId,
            method: 'DELETE',
            timeout: API_CONFIG.TIMEOUT,
            success: (res) => {
              if (res.statusCode === 200) {
                console.log(res.data);
                Vue.delete(state.userDevices[username], deviceId);
              }
            },
            fail: (err) => {
              console.error('删除设备失败:', err)
              // 可以在这里添加重试逻辑或提示用户
            }
          })
        } catch (error) {
          console.error('删除设备异常:', error)
        }
      },
      // 10. 添加新设备（适配用户设备隔离）
      ADD_DEVICE(state, device) {
        const username = state.currentUser ? state.currentUser.username : null;
        if (!username) {
          return;
        };
        try {
          uni.request({
            url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ADD_DEVICE}` + username,
            method: 'POST',
            timeout: API_CONFIG.TIMEOUT,
            data: device,
            success: (res) => {
              if (res.statusCode === 200) {
                // 为每条消息添加read字段，默认为false（未读）
                console.log(res.data);
                device = res.data;
                if (device.type === "light")
                {
                  device.iconOff = "/static/icon/light_off.png";
                  device.iconOn = "/static/icon/light_on.png";
                }
                else if (device.type === "air")
                {
                  device.iconOff = "/static/icon/air_off.png";
                  device.iconOn = "/static/icon/air_on.png";
                }
                else if (device.type === "shower")
                {
                  device.iconOff = "/static/icon/shower_off.png";
                  device.iconOn = "/static/icon/shower_on.png";
                }
                Vue.set(state.userDevices[username], device.id, device);
              }
            },
            fail: (err) => {
              console.error('添加设备失败:', err)
              // 可以在这里添加重试逻辑或提示用户
            }
          })
        } catch (error) {
          console.error('添加设备异常:', error)
        }
      },
      // 11. 删除用户的所有设备（当用户被删除时调用）
      DELETE_USER_DEVICES(state, username) {
        if (state.userDevices[username]) {
          Vue.delete(state.userDevices, username);
        }
      },
      // // 12. 更新环境历史数据
      // UPDATE_ENVIRONMENT_HISTORY(state, { granularity, type, data }) {
      //   if (state.environmentHistory[granularity]) {
      //     state.environmentHistory[granularity][type] = data;
      //   }
      // },
      // 13. 设置上次保存10分钟粒度数据的时间
      SET_LAST_TEN_MINUTE_SAVE_TIME(state, time) {
        state.lastTenMinuteSaveTime = time;
      },
      // 日程相关mutations
      // 14. 添加日程
      ADD_SCHEDULE(state, schedule) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId) return;
        
        // 确保该用户的日程数组存在
        if (!state.userSchedules[userId]) {
          Vue.set(state.userSchedules, userId, []);
        }
        
        // 添加日程
        state.userSchedules[userId].push(schedule);
      },
      
      // 15. 更新日程
      UPDATE_SCHEDULE(state, { id, updates }) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userSchedules[userId]) return;
        
        const index = state.userSchedules[userId].findIndex(schedule => schedule.id === id);
        if (index !== -1) {
          Object.assign(state.userSchedules[userId][index], updates);
        }
      },
      
      // 16. 删除日程
      DELETE_SCHEDULE(state, scheduleId) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userSchedules[userId]) return;
        
        const index = state.userSchedules[userId].findIndex(schedule => schedule.id === scheduleId);
        if (index !== -1) {
          state.userSchedules[userId].splice(index, 1);
        }
      },
      
      // 17. 切换日程完成状态
      TOGGLE_SCHEDULE_COMPLETE(state, scheduleId) {
        const userId = state.currentUser ? state.currentUser.username : null;
        if (!userId || !state.userSchedules[userId]) return;
        
        const schedule = state.userSchedules[userId].find(s => s.id === scheduleId);
        if (schedule) {
          schedule.completed = !schedule.completed;
        }
      },
      
      // 18. 删除用户的所有日程
      DELETE_USER_SCHEDULES(state, username) {
        if (state.userSchedules[username]) {
          Vue.delete(state.userSchedules, username);
        }
      },
      // 19. 初始化环境历史数据
      // INITIALIZE_ENVIRONMENT_HISTORY(state) {
      //   // 为10分钟粒度生成初始数据（最近3小时，每5分钟一个点，共36个点）
      //   state.environmentHistory['10min'].temperature = generateInitialHistoryData(state.environment.temp, 36, 4, 'temperature');
      //   state.environmentHistory['10min'].humidity = generateInitialHistoryData(state.environment.humidity, 36, 10, 'humidity');
        
      //   // 为小时粒度生成初始数据（最近24小时，每小时一个点）
      //   state.environmentHistory.hourly.temperature = generateInitialHistoryData(state.environment.temp, 24, 6, 'temperature');
      //   state.environmentHistory.hourly.humidity = generateInitialHistoryData(state.environment.humidity, 24, 15, 'humidity');
        
      //   // 为天粒度生成初始数据（最近15天，每天一个点）
      //   state.environmentHistory.daily.temperature = generateInitialHistoryData(state.environment.temp, 15, 8, 'temperature');
      //   state.environmentHistory.daily.humidity = generateInitialHistoryData(state.environment.humidity, 15, 20, 'humidity');
        
      //   // 设置上次保存时间
      //   state.lastTenMinuteSaveTime = new Date().toISOString();
      // },
      INITIALIZE_ENVIRONMENT_HISTORY(state) {

      },
      
      // 设置消息列表
         SET_MESSAGES(state, messages) {
     	  state.messages = state.messages.concat(messages);
           // state.messages = messages
         },
         
         // 添加单条消息
         ADD_MESSAGE(state, message) {
           // 检查是否已存在相同ID的消息
           const existingIndex = state.messages.findIndex(msg => msg.id === message.id)
           if (existingIndex === -1) {
             state.messages.push(message)
           } else {
             // 更新已存在的消息
             state.messages[existingIndex] = message
           }
         },

      // 21. 标记消息为已读
      MARK_MESSAGE_AS_READ(state, messageId) {
        const message = state.messages.find(msg => msg.id === messageId);
        if (message) {
          message.read = true;
        }
      }
    },
    // actions: {
    //   // 初始化应用数据
    //   initializeApp({ commit, state }) {
    //     // 初始化环境历史数据
    //     commit('INITIALIZE_ENVIRONMENT_HISTORY');

    //   }
    // }
})