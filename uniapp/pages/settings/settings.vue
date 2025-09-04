<template>
  <view class="page">
    <view class="setting-item" v-for="(item, i) in settings" :key="i" @click="clickSetting(item)">
      <text>{{ item.name }}</text>
      <text class="arrow">></text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      settings: [
        { name: "账号管理" },
        { name: "WiFi 配置" },
        { name: "关于我们" }
      ]
    }
  },
  methods: {
    clickSetting(item) {
      uni.showToast({
        title: `点击了 ${item.name}`,
        icon: "none"
      })
    }
  }
}
</script>

<style>
.page { padding: 20rpx; }
.setting-item {
  padding: 30rpx; border-bottom: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center;
}
.arrow { color: #999; }
</style>
