<template>
  <view class="container">
    <view class="header">
      <text class="back" @click="navigateBack">←</text>
      <text class="title">灯光控制</text>
    </view>
    
    <view class="content">
      <view class="device-info">
        <image :src="lightDevice.on ? lightDevice.iconOn : lightDevice.iconOff" class="device-img" />
        <view class="device-text">
          <text class="device-name">{{ lightDevice.name }}</text>
          <text class="device-location">{{ lightDevice.location }}</text>
        </view>
        <switch 
          class="device-switch" 
          :checked="lightDevice.on" 
          @change="toggleDevice"
          :disabled="!lightDevice.online"
        ></switch>
      </view>
      
      <view class="status-panel" v-if="lightDevice.online">
        <view class="status-item">
          <text class="status-label">设备状态：</text>
          <text class="status-value">{{ lightDevice.on ? '已开启' : '已关闭' }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">连接状态：</text>
          <text class="status-value online">在线</text>
        </view>
      </view>
      
      <view class="offline-tip" v-if="!lightDevice.online">
        设备离线，无法控制
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      lightDevice: {},
      deviceId: ''
    };
  },
  onLoad(options) {
      this.deviceId = options.deviceId;
      this.loadDeviceData();
      
      // 监听设备数据变化，实现实时同步
      this.unwatch = this.$store.watch(
        () => this.$store.getters.getCurrentUserDeviceById(this.deviceId),
        (newVal) => {
          if (newVal) {
            this.lightDevice = { ...newVal };
          }
        },
        { deep: true }
      );
    },
  onUnload() {
    if (this.unwatch) {
      this.unwatch();
    }
  },
  methods: {
    loadDeviceData() {
      const device = this.$store.getters.getCurrentUserDeviceById(this.deviceId);
      if (device) {
        this.lightDevice = { ...device };
      }
    },
    navigateBack() {
      uni.navigateBack();
    },
    // 仅保留开关控制，无亮度调节
    // 切换设备开关状态 - 优化体验：先本地更新再提交状态
    toggleDevice() {
      // 本地即时更新，提供即时反馈
      this.lightDevice.on = !this.lightDevice.on;
      // 强制更新UI
      this.$forceUpdate();
      
      // 提交到Vuex进行实际状态更新
      this.$store.commit('TOGGLE_DEVICE_ON', this.deviceId);
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
.device-text {
  flex: 1;
}
.device-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
}
.device-location {
  font-size: 22rpx;
  color: #666;
  opacity: 0.8;
}
.device-switch {
  transform: scale(0.9);
}
.status-panel {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
}
.status-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1px solid #f5f5f5;
}
.status-item:last-child {
  border-bottom: none;
}
.status-label {
  font-size: 26rpx;
  color: #666;
  width: 160rpx;
}
.status-value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}
.status-value.online {
  color: #00B42A;
}
.offline-tip {
  text-align: center;
  color: #999;
  font-size: 28rpx;
  padding: 40rpx;
  background-color: #fff;
  border-radius: 20rpx;
}
</style>
    