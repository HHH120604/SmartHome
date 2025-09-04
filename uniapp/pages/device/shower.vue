<template>
  <view class="container">
    <view class="header">
      <text class="back" @click="navigateBack">←</text>
      <text class="title">热水器控制</text>
    </view>
    
    <view class="content">
      <view class="device-info">
        <image :src="showerDevice.on ? showerDevice.iconOn : showerDevice.iconOff" class="device-img" />
        <text class="device-name">{{ showerDevice.name }}</text>
        <switch 
          class="device-switch" 
          :checked="showerDevice.on" 
          @change="toggleDevice"
          :disabled="!showerDevice.online"
        ></switch>
      </view>
      
      <view class="control-panel" v-if="showerDevice.on && showerDevice.online">
        <view class="temp-control">
          <text class="control-title">水温调节</text>
          <view class="temp-adjust">
            <button class="temp-btn" @click="adjustTemp(-1)">-</button>
            <text class="temp-value">{{ showerDevice.status.temp }}℃</text>
            <button class="temp-btn" @click="adjustTemp(1)">+</button>
          </view>
        </view>
        
        <view class="status-display">
          <text class="status-label">当前状态：</text>
          <text class="status-value">{{ showerDevice.desc }}</text>
        </view>
      </view>
      
      <view class="offline-tip" v-if="!showerDevice.online">
        设备离线，无法控制
      </view>
      <view class="off-tip" v-if="showerDevice.online && !showerDevice.on">
        热水器已关闭，开启后可进行调节
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      showerDevice: {
        temp: 40  // 提供默认温度值
      },
      deviceId: ''
    };
  },
  onLoad(options) {
      // 获取从主页传递的设备ID
      this.deviceId = options.deviceId || 'shower';
      // 初始化设备数据
      this.loadDeviceData();
      
      // 监听Vuex中设备数据变化，实现实时同步
      this.unwatch = this.$store.watch(
        () => this.$store.getters.getCurrentUserDeviceById(this.deviceId),
        (newVal) => {
          if (newVal) {
            this.showerDevice = { ...newVal };
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
        // 确保有温度属性
        this.showerDevice = { 
          ...device, 
          temp: device.status.temp || 40  // 如果没有温度属性，设置默认值
        };
      }
    },
    // 返回主页
    navigateBack() {
      uni.navigateBack();
    },
    // 切换设备开关状态 - 优化体验：先本地更新再提交状态
    toggleDevice() {
      // 本地即时更新，提供即时反馈
      this.showerDevice.on = !this.showerDevice.on;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('TOGGLE_DEVICE_ON', this.deviceId);
    },
    // 调节温度 - 优化体验：先本地更新再提交状态
    adjustTemp(change) {
      // 本地即时更新，提供即时反馈
      // 热水器温度范围限制（30-60℃）
      const newTemp = Math.min(Math.max(this.showerDevice.status.temp + change, 30), 60);
      this.showerDevice.status.temp = newTemp;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('SET_SHOWER_TEMP', {
        deviceId: this.deviceId,
        temp: newTemp
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
.temp-control {
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
  color: #FF7D00;
  margin: 0 20rpx;
}
.status-display {
  text-align: center;
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 10rpx;
}
.status-label {
  font-size: 26rpx;
  color: #666;
}
.status-value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
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
    