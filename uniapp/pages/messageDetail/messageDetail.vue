<template>
  <view class="container">
    <view class="header">
      <text class="icon">{{ getIcon(type) }}</text>
      <text class="title">{{ title }}</text>
    </view>

    <view class="content">
      <text class="content-text">{{ content }}</text>
    </view>

    <view class="time">
      <text>📅 时间：{{ time }}</text>
    </view>

    <!-- 根据类型显示不同的操作提示 -->
    <view v-if="type === 'alert'" class="extra">
      🚨 紧急处理：请立即检查火源，并确认设备报警是否正常！
    </view>

    <view v-else-if="type === 'device'" class="extra">
      💧 提示：系统已完成自动浇水，无需手动操作。
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      type: "",
      title: "",
      content: "",
      time: ""
    }
  },
  onLoad(options) {
    // 从消息列表传过来的参数
    this.type = options.type || "system"
    this.title = options.title || "未知消息"
    this.content = options.content || "暂无内容"
    this.time = options.time || new Date().toLocaleString()
  },
  methods: {
    getIcon(type) {
      switch(type) {
        case "alert": return "🔥"
        case "device": return "💧"
        case "system": return "📢"
        default: return "📩"
      }
    }
  }
}
</script>

<style>
.container {
  padding: 30rpx;
  background: #f6f6f6;
  min-height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
}
.icon {
  font-size: 60rpx;
  margin-right: 20rpx;
}
.title {
  font-size: 40rpx;
  font-weight: bold;
}
.content {
  background: #fff;
  padding: 20rpx;
  border-radius: 20rpx;
  margin-bottom: 20rpx;
}
.content-text {
  font-size: 32rpx;
  line-height: 1.6;
  color: #333;
}
.time {
  font-size: 28rpx;
  color: #888;
  margin-top: 20rpx;
}
.extra {
  margin-top: 40rpx;
  padding: 20rpx;
  background: #fff3cd;
  border-radius: 20rpx;
  font-size: 30rpx;
  color: #856404;
}
</style>