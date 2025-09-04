<template>
  <view class="container">
    <view class="header">
      <text class="back" @click="navigateBack">←</text>
      <text class="title">{{ airDevice.name }}</text>
    </view>
    
    <view class="content">
      <view class="device-info">
        <image :src="airDevice.on ? airDevice.iconOn : airDevice.iconOff" class="device-img" />
        <text class="location-icon">⛄</text>
        <text class="device-name">{{ airDevice.name }}</text>
        <switch 
          class="device-switch" 
          :checked="airDevice.on" 
          @change="toggleDevice"
          :disabled="!airDevice.online"
        ></switch>
      </view>
      
      <view class="control-panel" v-if="airDevice.on && airDevice.online">
        <view class="temp-control">
          <text class="control-title">温度调节</text>
          <view class="temp-adjust">
            <button class="temp-btn" @click="adjustTemp(-1)">-</button>
            <text class="temp-value">{{ airDevice.status.temp }}℃</text>
            <button class="temp-btn" @click="adjustTemp(1)">+</button>
          </view>
        </view>
        
        <view class="mode-control">
          <text class="control-title">运行模式</text>
          <view class="mode-buttons">
            <button 
              :class="['mode-btn', airDevice.status.mode === 'cool' ? 'active' : '']" 
              @click="setMode('cool')"
            >
              制冷
            </button>
            <button 
              :class="['mode-btn', airDevice.status.mode === 'heat' ? 'active' : '']" 
              @click="setMode('heat')"
            >
              制热
            </button>
            <button 
              :class="['mode-btn', airDevice.status.mode === 'auto' ? 'active' : '']" 
              @click="setMode('auto')"
            >
              自动
            </button>
          </view>
        </view>
      </view>
      
      <view class="offline-tip" v-if="!airDevice.online">
        设备离线，无法控制
      </view>
      <view class="off-tip" v-if="airDevice.online && !airDevice.on">
        空调已关闭，开启后可进行调节
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      airDevice: {},
      deviceId: ''
    };
  },
  onLoad(options) {
      // 获取从主页传递的设备ID
      this.deviceId = options.deviceId || 'air';
      // 初始化设备数据
      this.loadDeviceData();
      
      // 监听Vuex中设备数据变化，实现实时同步
      this.unwatch = this.$store.watch(
        () => this.$store.getters.getCurrentUserDeviceById(this.deviceId),
        (newVal) => {
          if (newVal) {
            this.airDevice = { ...newVal };
          }
        },
        { deep: true } // 深度监听对象变化
      );
    },
  onUnload() {
    // 移除监听器，避免内存泄漏
    if (this.unwatch) {
      this.unwatch();
    }
  },
  methods: {
    // 从Vuex加载设备数据
    loadDeviceData() {
      const device = this.$store.getters.getCurrentUserDeviceById(this.deviceId);
      if (device) {
        this.airDevice = { ...device };
      }
    },
    // 返回主页
    navigateBack() {
      uni.navigateBack();
    },
    // 切换设备开关状态 - 优化体验：先本地更新再提交状态
    toggleDevice() {
      // 本地即时更新，提供即时反馈
      this.airDevice.on = !this.airDevice.on;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('TOGGLE_DEVICE_ON', this.deviceId);
    },
    // 调节温度 - 优化体验：先本地更新再提交状态
    adjustTemp(change) {
      // 本地即时更新，提供即时反馈
      const newTemp = Math.min(Math.max(this.airDevice.status.temp + change, 16), 30);
      this.airDevice.status.temp = newTemp;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('SET_AIR_TEMP', { 
        deviceId: this.deviceId, 
        temp: newTemp 
      });
    },
    // 设置运行模式 - 优化体验：先本地更新再提交状态
    setMode(mode) {
      // 本地即时更新，提供即时反馈
      this.airDevice.status.mode = mode;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('SET_AIR_MODE', {
        deviceId: this.deviceId,
        mode: mode
      });
    }
  }
};
</script>

<style>
.container {
  padding: 20rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  margin: 30rpx 0;
}
.back {
  font-size: 36rpx;
  color: #333;
  margin-right: 20rpx;
}
.title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
}
.device-info {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}
.device-img {
  width: 80rpx;
  height: 80rpx;
  margin-right: 30rpx;
}
.location-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}
.device-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
}
.device-switch {
  transform: scale(0.9);
}
.control-panel {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
}
.control-title {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 20rpx;
  display: block;
}
.temp-control, .mode-control {
  margin-bottom: 40rpx;
}
.temp-adjust {
  display: flex;
  align-items: center;
  justify-content: center;
}
.temp-btn {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background-color: #f0f0f0;
  color: #333;
  font-size: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  margin: 0 20rpx;
}
.temp-value {
  font-size: 48rpx;
  font-weight: bold;
  color: #007AFF;
  margin: 0 20rpx;
}
.mode-buttons {
  display: flex;
  justify-content: space-around;
}
.mode-btn {
  width: 140rpx;
  height: 60rpx;
  background-color: #f0f0f0;
  color: #333;
  border-radius: 10rpx;
  border: none;
  font-size: 26rpx;
}
.mode-btn.active {
  background-color: #007AFF;
  color: #fff;
}
.offline-tip, .off-tip {
  text-align: center;
  color: #999;
  font-size: 28rpx;
  padding: 40rpx;
  background-color: #fff;
  border-radius: 20rpx;
}
</style>
    