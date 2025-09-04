<template>
  <view class="page-container">
    <!-- 带背景的页面（确保背景图正确显示） -->
    <view class="page" :style="{
      backgroundImage: 'url(/static/img/home_bg.png)', 
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundAttachment: 'fixed'
    }">
      <!-- 顶部标题 -->
      <view class="header">
        <image src="/static/icon/clear.png" class="refresh-btn" @click="refreshData" />
        <text class="title">CQU Home</text>
        <view class="message-container" @click="goToMessage">
          <image src="/static/icon/message.png" class="message-btn" />
          <text v-if="unreadMessageCount > 0" class="message-badge">{{ unreadMessageCount }}</text>
        </view>
      </view>

      <!-- 场景导航 -->
      <scroll-view scroll-x class="scene-nav">
        <view 
          v-for="item in scenes" 
          :key="item" 
          :class="['scene-item', currentScene === item ? 'active' : '']"
          @click="changeScene(item)">
          {{ item }}
        </view>
      </scroll-view>

      <!-- 环境监测区域：紧凑布局，向左并拢 -->
      <view class="status-container">
        <!-- 时间卡片 -->
        <view class="status-card">
          <image src="/static/icon/time.png" class="status-icon" />
          <text class="status-value">{{ currentTime }}</text>
        </view>
        
        <!-- 温度卡片（显示整数） -->
        <view class="status-card">
          <image src="/static/icon/temp.png" class="status-icon" />
          <text class="status-value" :class="environment.tempStatus">{{ Math.round(environment.temp) }}℃</text>
          <text class="status-tip">{{ getTempTip(environment.tempStatus) }}</text>
        </view>
        
        <!-- 湿度卡片（显示整数） -->
        <view class="status-card">
          <image src="/static/icon/humidity.png" class="status-icon" />
          <text class="status-value" :class="environment.humidityStatus">{{ Math.round(environment.humidity) }}%</text>
          <text class="status-tip">{{ getHumidityTip(environment.humidityStatus) }}</text>
        </view>
        
        <!-- 更多按钮卡片 -->
        <view class="status-card more-card" @click="goToEnvMonitor">
          <image src="/static/icon/more.png" class="status-icon" />
          <text class="status-value">更多</text>
        </view>
      </view>

      <!-- 设备统计卡片 -->
      <view class="device-stat-card">
        <view class="stat-item" @click="goToDeviceManage">
          <text class="stat-label">设备数</text>
          <text class="stat-value">{{ currentSceneDeviceCount }}</text>
        </view>
        <view class="stat-item" @click="goToDeviceManage">
          <text class="stat-label">在线</text>
          <text class="stat-value online">{{ currentSceneOnlineCount }}</text>
        </view>
        <view class="stat-item" @click="goToDeviceManage">
          <text class="stat-label">已开启</text>
          <text class="stat-value active">{{ currentSceneActiveCount }}</text>
        </view>
        <image src="/static/icon/arrow-right.png" class="stat-arrow" @click="goToDeviceManage" />
        <text class="add-device-btn" @click.stop="showAddDeviceForm">+</text>
      </view>

      <!-- 模式模块 -->
      <view class="modes">
        <view 
          v-for="(item, index) in modes" 
          :key="index" 
          :class="['mode-item', currentMode === item ? 'active' : '']"
          @click="activateMode(item)"
        >
          {{ item }}
          <view v-if="currentMode === item" class="active-indicator"></view>
        </view>
      </view>

      <!-- 设备卡片列表 -->
      <scroll-view class="devices-scroll" scroll-y>
        <view class="devices">
          <view 
            v-for="device in filteredDevices" 
            :key="device.id" 
            class="device-card"
          >
            <!-- 左侧信息区域 -->
            <view class="device-left">
              <image :src="device.on ? device.iconOn : device.iconOff" class="device-icon"/>
              <view class="info" @click="goToDevice(device)">
                <text class="device-name">{{ device.name }}</text>
                <text class="device-location">{{ device.scene }}</text>
                
                <!-- 显示设备描述 (灰色字体温度) -->
                <text class="device-desc">{{ device.online ? device.desc : '设备离线' }}</text>
                
                <!-- 对于空调设备在线且开启状态，额外显示温度加减控制 -->
                <template v-if="device.type === 'air' && device.on && device.online">
                  <!-- 温度控制 (空调设备) -->
                  <view class="temp-controls">
                    <button class="temp-btn minus" @click.stop="adjustTemperature(-1, device)">-</button>
                    <text class="current-temp">{{ device.status.temp }}℃</text>
                    <button class="temp-btn plus" @click.stop="adjustTemperature(1, device)">+</button>
                  </view>
                </template>
              </view>
            </view>
            
            <!-- 右侧开关和删除按钮 -->
      <view class="device-right-controls">
        <switch 
          class="device-switch" 
          :checked="device.on" 
          @change="toggleDevice(device)"
          :disabled="!device.online"
        ></switch>
        <image src="/static/icon/delete.png" class="delete-btn" @click.stop="deleteDevice(device.id)" />
      </view>
          </view>
          
          <!-- 底部留白 -->
          <view class="bottom-space"></view>
        </view>
      </scroll-view>
    </view>

    <!-- 添加设备模态框 - 修复选择器位置过低问题 -->
    <view v-if="showAddForm" class="modal-overlay" @click="hideAddDeviceForm">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">添加新设备</text>
        </view>
        <view class="modal-body">
          <view class="form-item">
            <text class="form-label">设备类型</text>
            <picker @change="changeDeviceType" :value="deviceTypeIndex" :range="deviceTypes">
              <view class="picker">
                {{ deviceTypes[deviceTypeIndex] }}
              </view>
            </picker>
          </view>
          
          <view class="form-item">
            <text class="form-label">设备名称</text>
            <input class="form-input" v-model="deviceName" placeholder="请输入设备名称" />
          </view>
          
          <view class="form-item">
            <text class="form-label">场景</text>
            <picker @change="changeDeviceScene" :value="deviceSceneIndex" :range="deviceScenes">
              <view class="picker">
                {{ deviceScenes[deviceSceneIndex] }}
              </view>
            </picker>
          </view>
        </view>
        <view class="modal-footer">
          <button class="btn-cancel" @click="hideAddDeviceForm">取消</button>
          <button class="btn-confirm" @click="addDevice">确定</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import API_CONFIG from '../../utils/api-config.js'
export default {
  data() {
    return {
      refreshKey: 0,
      currentScene: "全屋",
      scenes: ["全屋", "客厅", "卧室", "厨房", "卫生间"],
      modes: ["夜晚", "离家", "回家", "起床"],
      timer: null,
      timeUpdateTimer: null,
      messageTimer: null,
      currentTime: "",
      // 添加设备相关数据
      showAddForm: false,
      deviceTypes: ['灯', '空调', '淋浴', '风扇'],
      deviceScenes: ["客厅", "卧室", "厨房", "卫生间"],
      deviceTypeIndex: 0,
      deviceSceneIndex: 0,
      deviceName: '',
      
      // 环境数据
      // environment: {
      //   temp: 25.5,
      //   humidity: 50,
      //   tempStatus: 'normal', // 'low', 'normal', 'high'
      //   humidityStatus: 'normal' // 'low', 'normal', 'high'
      // },
    };
  },
  
  onLoad() {
    this.updateTime();
    this.timeUpdateTimer = setInterval(() => {
      this.updateTime();
    }, 5000); // 每分钟更新一次时间
    
    // 同步环境数据到store
    // this.$store.commit('UPDATE_FULL_ENVIRONMENT');
    // 监听设备状态变化的事件
    this.$on('refreshDevices', this.refreshData);
    
    // 初始化获取消息
    this.fetchNewMessages();
    // 每5秒拉取一次新消息
    this.messageTimer = setInterval(() => {
      this.fetchNewMessages();
    }, 5000);
  },
  
  onShow() {
    // 每次页面显示时自动刷新数据
    this.refreshData();
  },
  
  onUnload() {
    if (this.timeUpdateTimer) {
      clearInterval(this.timeUpdateTimer);
    }
    if (this.messageTimer) {
      clearInterval(this.messageTimer);
    }
    // 移除事件监听
    this.$off('refreshDevices', this.refreshData);
  },
  
  computed: {
    environment() {
      return this.$store.getters.getFullEnvironment;
    },

    currentMode() {
      return this.$store.getters.getCurrentMode;
    },
    
    // 从store中获取当前用户的设备
    filteredDevices() {
      // 添加refreshKey引用以确保每次获取时都重新计算
      this.refreshKey;
      if (this.currentScene === '全屋') {
        return Object.values(this.$store.getters.getCurrentUserDevices);
      } else {
        return this.$store.getters.getCurrentUserDevicesByScene(this.currentScene);
      }
    },
    
    currentSceneDeviceCount() {
      return this.filteredDevices.length;
    },
    
    currentSceneOnlineCount() {
      return this.filteredDevices.filter(device => device.online).length;
    },
    
    currentSceneActiveCount() {
      return this.filteredDevices.filter(device => device.on && device.online).length;
    },
    
    // 获取未读消息数量
    unreadMessageCount() {
      return this.$store.getters.getUnreadMessageCount || 0;
    }
  },
  
  methods: {
    activateMode(mode) {
      // 如果点击的是当前已激活的模式，则取消激活
      if (mode === this.currentMode) {
        this.$store.commit('DEACTIVATE_MODE');
      } else {
        // 激活对应的模式
        this.$store.commit('ACTIVATE_MODE', mode);
      }
    },
    
    getTempTip(status) {
      switch(status) {
        case 'low':
          return '偏冷';
        case 'high':
          return '偏热';
        default:
          return '舒适';
      }
    },
    
    getHumidityTip(status) {
      switch(status) {
        case 'low':
          return '偏干';
        case 'high':
          return '偏湿';
        default:
          return '舒适';
      }
    },
    
    goToDeviceManage() {
      // 跳转到设备管理页面
      console.log('跳转到设备管理页面');
    },
    
    goToEnvMonitor() {
      // 跳转到环境监测页面
      try {
        uni.navigateTo({
          url: '/pages/environment/monitor',
          success: () => {
            console.log('成功跳转到环境监测页');
          },
          fail: (err) => {
            console.error('环境监测页跳转失败:', err);
            uni.showToast({
              title: '跳转失败，请重试',
              icon: 'none'
            });
          }
        });
      } catch (error) {
        console.error('导航异常:', error);
      }
    },
    
    changeScene(scene) {
      this.currentScene = scene;
    },
    
    updateTime() {
      const now = new Date();
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      this.currentTime = `${hours}:${minutes}`;
    },
    
    toggleDevice(device) {
      // 1. 本地即时更新，使用响应式方法更新设备状态
      // 创建一个新的设备对象数组，完全替换当前的设备列表
      const newDevices = this.filteredDevices.map(d => {
        if (d.id === device.id) {
          return { ...d, on: !d.on };
        }
        return d;
      });
      
      // 2. 更新refreshKey强制computed属性重新计算
      this.refreshKey += 1;
      
      // 3. 立即强制重新渲染以实现即时反馈
      this.$nextTick(() => {
        this.$forceUpdate();
      });
      
      // 4. 提交到store进行实际状态更新
      setTimeout(() => {
        this.$store.commit('TOGGLE_DEVICE_ON', device.id);
      }, 0);
    },
    
    deleteDevice(id) {
      // 先获取设备是否存在，再删除
      const device = this.$store.getters.getCurrentUserDeviceById(id);
      if (device) {
        // 显示确认对话框
        uni.showModal({
          title: '确认删除',
          content: '确定要删除该设备吗？',
          success: (res) => {
            if (res.confirm) {
              this.$store.commit('DELETE_DEVICE', id);
              // 强制重新渲染以更新列表
              this.$forceUpdate();
              uni.showToast({
                title: '删除成功',
                icon: 'success'
              });
            }
          }
        });
      }
    },
    
    goToDevice(device) {
      // 跳转到设备详情页面
      let devicePage = '';
      switch(device.type) {
        case 'light':
          devicePage = '/pages/device/light';
          break;
        case 'air':
          devicePage = '/pages/device/air';
          break;
        case 'shower':
          devicePage = '/pages/device/shower';
          break;
        default:
          devicePage = '/pages/device/light';
      }
      
      // 使用try-catch捕获可能的导航错误
      try {
        uni.navigateTo({
          url: `${devicePage}?deviceId=${device.id}`,
          success: () => {
            console.log('成功跳转到设备详情页');
          },
          fail: (err) => {
            console.error('设备详情页跳转失败:', err);
            uni.showToast({
              title: '跳转失败，请重试',
              icon: 'none'
            });
          }
        });
      } catch (error) {
        console.error('导航异常:', error);
      }
    },
    
    adjustTemperature(change, device) {
      this.$store.commit('SET_AIR_TEMP', {
        deviceId: device.id,
        temp: device.status.temp + change
      });
      // 强制重新渲染以更新温度显示
      this.$forceUpdate();
    },
    
    // 添加设备相关方法
    showAddDeviceForm() {
      this.showAddForm = true;
      // 重置表单数据
      this.deviceTypeIndex = 0;
      this.deviceSceneIndex = 0;
      this.deviceName = '';
    },
    
    hideAddDeviceForm() {
      this.showAddForm = false;
    },
    
    changeDeviceType(e) {
      this.deviceTypeIndex = e.detail.value;
    },
    
    changeDeviceScene(e) {
      this.deviceSceneIndex = e.detail.value;
    },
    
    addDevice() {
      if (!this.deviceName.trim()) {
        uni.showToast({
          title: '设备名称不能为空',
          icon: 'none'
        });
        return;
      }
      
      // 创建新设备
      const newDevice = {
        name: this.deviceName,
        device_type: this.getDeviceTypeValue(this.deviceTypes[this.deviceTypeIndex]),
        room_id: this.deviceSceneIndex + 1,
      };
      
      // 通过store添加设备
      this.$store.commit('ADD_DEVICE', newDevice);
      
      // 关闭模态框
      this.hideAddDeviceForm();
      
      // 添加设备后立即刷新
      this.refreshData();
      
      uni.showToast({
        title: '设备添加成功'
      });
    },
    
    getDeviceTypeValue(typeName) {
      switch(typeName) {
        case '灯':
          return 'light';
        case '空调':
          return 'air';
        case '淋浴':
          return 'shower';
        case '风扇':
          return 'fan';
        default:
          return 'light';
      }
    },
    
    getDeviceIcon(typeName, isOn) {
      const suffix = isOn ? '_on' : '_off';
      switch(typeName) {
        case '灯':
          return `/static/icon/light${suffix}.png`;
        case '空调':
          return `/static/icon/air${suffix}.png`;
        case '淋浴':
          return `/static/icon/shower${suffix}.png`;
        default:
          return `/static/icon/light${suffix}.png`;
      }
    },
    
    // 刷新数据方法
    refreshData() {
      // 改变refreshKey以触发computed重新计算
      this.refreshKey = this.refreshKey + 1;
      this.$store.commit('INIT_DEVICES');
      this.$store.commit('UPDATE_FULL_ENVIRONMENT');
      // 强制重新渲染UI
      this.$forceUpdate();
      // 显示刷新成功提示
      uni.showToast({
        title: '数据已刷新',
        icon: 'success',
        duration: 1000
      });
    },
    
    // 跳转到消息页面
    goToMessage() {
      // 自动将所有未读消息标记为已读
      const unreadMessages = this.$store.getters.getMessages.filter(msg => !msg.read);
      unreadMessages.forEach(msg => {
        this.$store.commit('MARK_MESSAGE_AS_READ', msg.id);
      });
      
      uni.navigateTo({
        url: '/pages/message/message'
      });
    },
    
    // 获取新消息并保存到Vuex
	fetchNewMessages() {
	  try {
	    uni.request({
	      url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_MESSAGES}`,
	      method: 'GET',
	      timeout: API_CONFIG.TIMEOUT,
	      success: (res) => {
	        if (res.statusCode === 200 && Array.isArray(res.data)) {
	          // 获取现有的消息，用于保留已读状态
	          const existingMessages = this.$store.getters.getMessages || []
	          // 创建一个映射，方便查找现有消息的已读状态
	          const existingMessagesMap = {}
	          existingMessages.forEach(msg => {
	            existingMessagesMap[msg.id] = msg.read
	          })
	          
	          // 为每条消息添加read字段，如果是已存在的消息则保留原有的已读状态
	          const messagesWithReadStatus = res.data.map(msg => ({
	            ...msg,
	            read: existingMessagesMap[msg.id] || false, // 保留已读状态，新消息默认为未读
	            time: new Date(msg.time).getTime() // 转换时间格式为时间戳
	          }))
	          
	          // 将消息保存到Vuex store
	          this.$store.commit('SET_MESSAGES', messagesWithReadStatus)
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
	}
  }
};
</script>

<style scoped>
/* 基础容器样式 */
.page-container {
  width: 100%;
  height: 100%;
  background-color: #f5f5f5;
  overflow: visible;
  margin: 0;
  padding: 0;
}

/* 页面背景 */
.page {
  width: 100%;
  min-height: 100vh;
  padding: 0 20rpx;
  box-sizing: border-box;
  margin: 0;
  position: relative;
}

/* 头部样式 */
.header {
  text-align: center;
  margin-bottom: 20rpx;
  margin-top: 0;
  padding-top: 0;
  position: relative;
  height: 70rpx;
  line-height: 70rpx;
}

/* 刷新按钮样式 */
.refresh-btn {
  position: absolute;
  left: 30rpx;
  top: 50%;
  transform: translateY(-50%);
  width: 50rpx;
  height: 50rpx;
}

/* 消息按钮容器 */
.message-container {
  position: absolute;
  right: 30rpx;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 消息按钮样式 */
.message-btn {
  width: 50rpx;
  height: 50rpx;
}

/* 消息角标样式 */
.message-badge {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  min-width: 36rpx;
  height: 36rpx;
  line-height: 36rpx;
  padding: 0 10rpx;
  background-color: #ff4d4f;
  color: white;
  font-size: 24rpx;
  border-radius: 18rpx;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 确保页面内容从顶部开始 */
* {
  box-sizing: border-box;
}

page {
  padding: 0;
  margin: 0;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

/* 场景导航 */
.scene-nav {
  height: 70rpx;
  margin-bottom: 20rpx;
}
.scene-item {
  display: inline-block;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 30rpx;
  margin-right: 20rpx;
  border-radius: 30rpx;
  font-size: 28rpx;
  color: #666;
  background-color: rgba(255, 255, 255, 0.7);
}
.scene-item.active {
  color: #007AFF;
  background-color: rgba(0, 122, 255, 0.1);
}

/* 环境监测区域 */
.status-container {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}
.status-card {
  flex: 1;
  background-color: rgba(255, 255, 255, 0.85);
  border-radius: 15rpx;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}
.status-icon {
  width: 50rpx;
  height: 50rpx;
  margin-bottom: 10rpx;
}
.status-value {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}
.status-value.normal {
  color: #333;
}
.status-value.low {
  color: #007AFF;
}
.status-value.high {
  color: #FF3B30;
}
.status-tip {
  font-size: 20rpx;
  color: #666;
  margin-top: 5rpx;
}
.more-card {
  cursor: pointer;
}

/* 设备统计卡片 */
.device-stat-card {
  background-color: rgba(255, 255, 255, 0.85);
  border-radius: 15rpx;
  padding: 20rpx;
  margin-bottom: 30rpx;
  position: relative;
  display: flex;
  align-items: center;
}
.stat-item {
  flex: 1;
  text-align: center;
  cursor: pointer;
}
.stat-label {
  display: block;
  font-size: 24rpx;
  color: #666;
  margin-bottom: 5rpx;
}
.stat-value {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}
.stat-value.online {
  color: #34C759;
}
.stat-value.active {
  color: #007AFF;
}
.stat-arrow {
  width: 20rpx;
  height: 32rpx;
  position: absolute;
  right: 60rpx;
  top: 50%;
  transform: translateY(-50%);
}
.add-device-btn {
  position: absolute;
  right: 20rpx;
  top: 50%;
  transform: translateY(-50%);
  width: 50rpx;
  height: 50rpx;
  line-height: 50rpx;
  text-align: center;
  font-size: 40rpx;
  font-weight: bold;
  color: #007AFF;
  background-color: rgba(0, 122, 255, 0.1);
  border-radius: 50%;
  z-index: 10;
}

/* 模式选择 */
.modes {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

/* 温度控制样式 */
.temp-controls {
  display: flex;
  align-items: center;
  margin-top: 10rpx;
}
.current-temp {
  font-size: 28rpx;
  font-weight: bold;
  color: #007AFF;
  margin: 0 20rpx;
}
.temp-btn {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background-color: #f0f0f0;
  color: #333;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  margin: 0 5rpx;
}
.temp-btn.minus {
  background-color: #FF3B30;
  color: white;
}
.temp-btn.plus {
  background-color: #34C759;
  color: white;
}
.mode-item {
  flex: 1;
  height: 70rpx;
  line-height: 70rpx;
  text-align: center;
  font-size: 28rpx;
  color: #666;
  background-color: rgba(255, 255, 255, 0.85);
  border-radius: 15rpx;
  position: relative;
}
.mode-item.active {
  color: #007AFF;
  background-color: rgba(0, 122, 255, 0.1);
}
.active-indicator {
  position: absolute;
  bottom: 0;
  left: 25%;
  width: 50%;
  height: 6rpx;
  background-color: #007AFF;
  border-radius: 3rpx;
}

/* 设备列表滚动容器 */
.devices-scroll {
  height: calc(100vh - 500rpx);
}
.devices {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

/* 设备卡片样式 */
.device-card {
  background: rgba(255,255,255,0.9);
  border-radius: 18rpx;
  padding: 15rpx 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.05);
  min-height: 100rpx;
}
.device-card:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.08);
  transition: all 0.2s ease;
}
.device-left {
  display: flex;
  align-items: center;
  width: 82%;
}
.device-icon {
  width: 50rpx;
  height: 50rpx;
  margin-right: 18rpx;
}
.info {
  flex: 1;
  overflow: hidden;
  padding: 5rpx 0;
}
.info:active {
  background-color: rgba(0, 122, 255, 0.05);
  border-radius: 5rpx;
}
.device-name {
  font-size: 26rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 3rpx;
}
.device-location {
  font-size: 20rpx;
  color: #666;
  display: block;
  margin-bottom: 2rpx;
  opacity: 0.9;
}
.device-desc {
  font-size: 20rpx;
  color: #999;
}
.device-right-controls {
  display: flex;
  align-items: center;
  position: relative;
}

.device-switch {
  transform: scale(0.85);
  z-index: 10;
  margin-right: 10rpx;
}

.delete-btn {
  position: relative;
  right: 0;
  top: 0;
  transform: none;
  width: 40rpx;
  height: 40rpx;
  z-index: 20;
  cursor: pointer;
}

/* 空调温度控制 */
.temp-controls {
  display: flex;
  align-items: center;
  margin-top: 5rpx;
  height: 36rpx;
}
.temp-btn {
  width: 36rpx;
  height: 36rpx;
  line-height: 36rpx;
  padding: 0;
  margin: 0 6rpx;
  border-radius: 50%;
  font-size: 24rpx;
  font-weight: bold;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
}
.temp-btn.plus {
  background-color: #e6f7ff;
  color: #1890ff;
}
.temp-btn.minus {
  background-color: #fff1f0;
  color: #ff4d4f;
}
.current-temp {
  font-size: 22rpx;
  color: #007AFF;
  font-weight: 500;
}

/* 底部留白 */
.bottom-space {
  height: 30rpx;
}

/* 模态框样式 - 确保设备类型和场景选择器正常显示 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 100rpx;
  z-index: 999;
  pointer-events: auto;
}
.modal-content {
  background-color: white;
  border-radius: 20rpx;
  width: 80%;
  max-width: 600rpx;
  max-height: 70vh;
  z-index: 999;
  position: relative;
  pointer-events: auto;
  overflow: visible;
}
/* 选择器样式 - 确保选择器在最上层显示 */
.picker {
  position: relative;
  z-index: 1999;
}
.modal-header {
  padding: 30rpx 0;
  text-align: center;
  border-bottom: 1rpx solid #eee;
  background-color: white;
}
.modal-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}
.modal-body {
  padding: 30rpx;
  max-height: 50vh;
  overflow-y: auto;
}
.form-item {
  margin-bottom: 30rpx;
}
.form-item:last-child {
  margin-bottom: 0;
}
.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 15rpx;
}
.picker {
  height: 80rpx;
  line-height: 80rpx;
  padding: 0 20rpx;
  background-color: #f5f5f5;
  border-radius: 10rpx;
  font-size: 28rpx;
  color: #666;
}
.form-input {
  height: 80rpx;
  line-height: 80rpx;
  padding: 0 20rpx;
  background-color: #f5f5f5;
  border-radius: 10rpx;
  font-size: 28rpx;
  color: #333;
}
.modal-footer {
  padding: 20rpx 30rpx;
  display: flex;
  gap: 20rpx;
  border-top: 1rpx solid #eee;
}
.btn-cancel {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  text-align: center;
  font-size: 28rpx;
  color: #666;
  background-color: #f5f5f5;
  border-radius: 10rpx;
  border: none;
}
.btn-confirm {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  text-align: center;
  font-size: 28rpx;
  color: white;
  background-color: #007AFF;
  border-radius: 10rpx;
  border: none;
}
</style>