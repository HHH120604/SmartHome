<template>
  <view class="page-container">
    <!-- 带背景的页面，与主页风格统一 -->
    <view class="page" :style="{ backgroundImage: 'url(/static/img/home_bg.png)', backgroundSize: 'cover' }">
      <!-- 头部导航，包含返回按钮 -->
  <!--    <view class="header">
        <text class="back" @click="navigateBack">←</text>
        <text class="title">环境监测</text>
      </view> -->
      
      <!-- 设备卡片列表（滚动容器） -->
      <scroll-view class="devices-scroll" scroll-y>
        <view class="devices">
          <!-- 温度卡片 -->
          <view class="device-card" :class="{ 'danger-card': tempStatusClass === 'status-danger' }">
            <view class="device-left">
              <view class="info">
                <text class="device-name">温度</text>
                <text class="device-value">{{ Math.round(envData.temp) }}°C</text>
                <view class="gauge">
                  <view class="gauge-fill temperature-gauge" :style="{ width: `${tempGaugeWidthAnimated}%` }"></view>
                </view>
                <text class="status" :class="tempStatusClass">{{ tempStatusText }}</text>
              </view>
            </view>
            <view class="detail-btn" @click="goToDetail('temperature')">
              <image src="/static/icon/arrow-right.png" class="arrow-icon" />
            </view>
          </view>

          <!-- 湿度卡片 -->
          <view class="device-card" :class="{ 'danger-card': humidityStatusClass === 'status-danger' }">
            <view class="device-left">
              <view class="info">
                <text class="device-name">湿度</text>
                <text class="device-value">{{ Math.round(envData.humidity) }}%</text>
                <view class="gauge">
                  <view class="gauge-fill humidity-gauge" :style="{ width: `${humidityGaugeWidthAnimated}%` }"></view>
                </view>
                <text class="status" :class="humidityStatusClass">{{ humidityStatusText }}</text>
              </view>
            </view>
            <view class="detail-btn" @click="goToDetail('humidity')">
              <image src="/static/icon/arrow-right.png" class="arrow-icon" />
            </view>
          </view>

          <!-- 可燃气体卡片 -->
          <view class="device-card" :class="{ 'danger-card': gasStatusClass === 'status-danger' }">
            <view class="device-left">
              <view class="info">
                <text class="device-name">可燃气体</text>
                <text class="device-value">{{ envData.gasConcentration.toFixed(1) }}ppm</text>
                <view class="gauge">
                  <view class="gauge-fill gas-gauge" :style="{ width: `${gasGaugeWidthAnimated}%` }"></view>
                </view>
                <text class="status" :class="gasStatusClass">{{ gasStatusText }}</text>
              </view>
            </view>
          </view>

          <!-- 火焰卡片 -->
          <view class="device-card" :class="{ 'danger-card': flameStatusClass === 'status-danger' }">
            <view class="device-left">
              <view class="info">
                <text class="device-name">火焰</text>
                <text class="device-value">{{ envData.flameLevel-1 }}级</text>
                <view class="gauge">
                  <view class="gauge-fill flame-gauge" :style="{ width: `${flameGaugeWidthAnimated}%` }"></view>
                </view>
                <text class="status" :class="flameStatusClass">{{ flameStatusText }}</text>
              </view>
            </view>
          </view>

          <!-- 烟雾卡片 -->
          <!-- <view class="device-card" :class="{ 'danger-card': smokeStatusClass === 'status-danger' }">
            <view class="device-left">
              <view class="info">
                <text class="device-name">烟雾</text>
                <text class="device-value">{{ envData.smokeLevel }}级</text>
                <view class="gauge">
                  <view class="gauge-fill smoke-gauge" :style="{ width: `${smokeGaugeWidthAnimated}%` }"></view>
                </view>
                <text class="status" :class="smokeStatusClass">{{ smokeStatusText }}</text>
              </view>
            </view>
          </view> -->

          <!-- 底部留白，确保最后一个卡片能完全显示 -->
          <view class="bottom-space"></view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      // 进度条动画宽度（用于平滑过渡效果）
      tempGaugeWidthAnimated: 0,
      humidityGaugeWidthAnimated: 0,
      gasGaugeWidthAnimated: 0,
      flameGaugeWidthAnimated: 0,
      smokeGaugeWidthAnimated: 0
    }
  },
  
  computed: {
    // 从Vuex获取完整环境数据（与主页共用同一数据源）
    envData() {
      return this.$store.getters.getFullEnvironment;
    },
    
    // 温度进度条宽度计算（0-50度范围）
    tempGaugeWidth() {
      const width = (this.envData.temp / 50) * 90 + 5; // 0度对应5%，50度对应95%
      return Math.max(5, Math.min(width, 95)); // 限制在5%-95%之间
    },
    
    // 湿度进度条宽度计算
    humidityGaugeWidth() {
      const width = ((this.envData.humidity - 15) / 65) * 80 + 10;
      return Math.max(5, Math.min(width, 95));
    },
    
    // 可燃气体进度条宽度计算
    gasGaugeWidth() {
      const width = (this.envData.gasConcentration / 10);
      return Math.max(5, Math.min(width, 95));
    },
    
    // 火焰进度条宽度计算
    flameGaugeWidth() {
      return this.envData.flameLevel > 1 ? (this.envData.flameLevel / 5) * 100 : 5;
    },
    
    // 烟雾进度条宽度计算
    smokeGaugeWidth() {
      return this.envData.smokeLevel > 0 ? (this.envData.smokeLevel / 5) * 100 : 5;
    },
    
    // 温度状态类和文本
    tempStatusClass() {
      if (this.envData.temp > 32) return 'status-warning';
      if (this.envData.temp < 18) return 'status-warning';
      return 'status-normal';
    },
    tempStatusText() {
      if (this.envData.temp > 32) return '偏高';
      if (this.envData.temp < 18) return '偏低';
      return '正常';
    },
    
    // 湿度状态类和文本
    humidityStatusClass() {
      if (this.envData.humidity > 70) return 'status-warning';
      if (this.envData.humidity < 30) return 'status-warning';
      return 'status-normal';
    },
    humidityStatusText() {
      if (this.envData.humidity > 70) return '偏高';
      if (this.envData.humidity < 30) return '偏低';
      return '舒适';
    },
    
    // 可燃气体状态类和文本
    gasStatusClass() {
      return this.envData.gasConcentration > 300 ? 'status-danger' : 'status-normal';
    },
    gasStatusText() {
      return this.envData.gasConcentration > 300 ? '危险' : '安全';
    },
    
    // 火焰状态类和文本
    flameStatusClass() {
      return this.envData.flameLevel > 1 ? 'status-danger' : 'status-normal';
    },
    flameStatusText() {
      return this.envData.flameLevel > 1 ? '检测到火焰' : '无火焰';
    },
    
    // 烟雾状态类和文本
    smokeStatusClass() {
      return this.envData.smokeLevel > 0 ? 'status-danger' : 'status-normal';
    },
    smokeStatusText() {
      return this.envData.smokeLevel > 0 ? '检测到烟雾' : '无烟雾';
    }
  },
  
  watch: {
    // 监听进度条宽度变化，触发动画
    tempGaugeWidth: {
      handler(newVal) {
        this.animateGauge('tempGaugeWidthAnimated', newVal, 1500);
      },
      immediate: true // 初始化时立即执行
    },
    humidityGaugeWidth: {
      handler(newVal) {
        this.animateGauge('humidityGaugeWidthAnimated', newVal, 1500);
      },
      immediate: true
    },
    gasGaugeWidth: {
      handler(newVal) {
        this.animateGauge('gasGaugeWidthAnimated', newVal, 1500);
      },
      immediate: true
    },
    flameGaugeWidth: {
      handler(newVal) {
        this.animateGauge('flameGaugeWidthAnimated', newVal, 1200);
      },
      immediate: true
    },
    smokeGaugeWidth: {
      handler(newVal) {
        this.animateGauge('smokeGaugeWidthAnimated', newVal, 1200);
      },
      immediate: true
    }
  },
  
  methods: {
    // 返回上一页（主页）
    navigateBack() {
      uni.navigateBack();
    },
    
    // 跳转到详情页
    goToDetail(type) {
      uni.navigateTo({
        url: `/pages/environment/linechart?type=${type}`
      });
    },
    
    // 进度条动画函数（平滑过渡效果）
    animateGauge(propertyName, targetValue, duration = 1500) {
      const startValue = this[propertyName];
      const difference = targetValue - startValue;
      const startTime = performance.now();
      
      // 根据变化幅度调整动画时长
      const minDuration = Math.abs(difference) < 10 ? 800 : duration;
      
      const update = (currentTime) => {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / minDuration, 1);
        
        // 缓动函数（使动画更自然）
        let easeProgress;
        if (progress < 0.5) {
          easeProgress = 4 * progress * progress * progress;
        } else {
          easeProgress = 1 - Math.pow(-2 * progress + 2, 3) / 2;
        }
        
        // 更新动画宽度
        this[propertyName] = startValue + difference * easeProgress;
        
        // 未完成则继续请求动画帧
        if (progress < 1) {
          requestAnimationFrame(update);
        }
      };
      
      requestAnimationFrame(update);
    }
  }
}
</script>

<style scoped>
/* 基础容器样式，与主页保持一致 */
.page-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.page {
  padding: 20rpx;
  font-family: "Arial", "PingFang SC", sans-serif;
  min-height: 100vh;
  background-repeat: no-repeat;
  box-sizing: border-box;
}

/* 头部样式，与主页风格统一 */
.header {
  display: flex;
  align-items: center;
  margin: 30rpx 0;
}

.back {
  font-size: 36rpx;
  color: #333;
  margin-right: 20rpx;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back:active {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 50%;
}

.title {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  flex: 1;
  text-align: center;
}

/* 设备列表滚动容器 */
.devices-scroll {
  flex: 1;
  height: calc(100vh - 100rpx);
  scrollbar-width: thin;
}

.devices-scroll::-webkit-scrollbar {
  width: 6rpx;
}

.devices-scroll::-webkit-scrollbar-thumb {
  background-color: rgba(0,0,0,0.1);
  border-radius: 3rpx;
}

/* 设备卡片容器 */
.devices {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
  padding: 10rpx 0;
}

/* 设备卡片样式，与主页设备卡片风格统一 */
.device-card {
  background: rgba(255,255,255,0.9);
  border-radius: 18rpx;
  padding: 20rpx 25rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.05);
  transition: all 0.2s ease;
}

/* 详情按钮样式 */
.detail-btn {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 122, 255, 0.1);
  border-radius: 50%;
  margin-top: -20rpx;
}

.detail-btn:active {
  background: rgba(0, 122, 255, 0.2);
}

.arrow-icon {
  width: 24rpx;
  height: 24rpx;
}

.device-card:hover {
  transform: translateY(-3rpx);
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);
}

.device-left {
  display: flex;
  align-items: center;
  width: 100%;
}

.info {
  flex: 1;
  overflow: hidden;
  padding: 5rpx 0;
}

.device-name {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 5rpx;
}

.device-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #222;
  line-height: 1.2;
  padding: 5rpx 0;
  display: block;
}

/* 进度条样式 */
.gauge {
  width: 100%;
  height: 12rpx;
  background: #f0f0f0;
  border-radius: 8rpx;
  margin: 10rpx 0;
  overflow: hidden;
}

.gauge-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.5s ease;
}

/* 状态文本样式 */
.status {
  font-size: 22rpx;
  padding: 3rpx 12rpx;
  border-radius: 20rpx;
  display: inline-block;
  margin-top: 5rpx;
}

/* 状态类样式 */
.status-normal {
  background-color: #e6f7ee;
  color: #00a65a;
}

.status-warning {
  background-color: #fef5e7;
  color: #ff8c00;
}

.status-danger {
  background-color: #fde8e8;
  color: #ff4d4f;
}

/* 各类型进度条颜色区分 */
.temperature-gauge { background: linear-gradient(90deg, #4facfe, #00f2fe); }
.humidity-gauge { background: linear-gradient(90deg, #a8ff78, #78ffd6); }
.gas-gauge { background: linear-gradient(90deg, #ff9966, #ff5e62); }
.flame-gauge { background: linear-gradient(90deg, #ff512f, #dd2476); }
.smoke-gauge { background: linear-gradient(90deg, #7b4397, #dc2430); }

/* 危险状态卡片动画效果 */
.danger-card {
  animation: danger-shake 0.4s ease-in-out 3, danger-glow 1s infinite;
  border: 2rpx solid #ff4d4f;
}

@keyframes danger-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6rpx); }
  75% { transform: translateX(6rpx); }
}

@keyframes danger-glow {
  0%, 100% { box-shadow: 0 0 15rpx rgba(255, 77, 79, 0.4); }
  50% { box-shadow: 0 0 8rpx rgba(255, 77, 79, 0.2); }
}

/* 底部留白 */
.bottom-space {
  height: 30rpx;
}
</style>
