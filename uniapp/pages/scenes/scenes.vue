<template>
  <view class="page">
    <view class="scene-item" v-for="(scene, i) in scenes" :key="i" @click="runScene(scene)">
      <text class="scene-name">{{ scene.name }}</text>
      <text class="desc">{{ scene.desc }}</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      scenes: [
        { name: "回家模式", desc: "打开客厅灯和空调" },
        { name: "离家模式", desc: "关闭所有灯和电器" },
        { name: "睡眠模式", desc: "关灯，开卧室空调" }
      ]
    }
  },
  methods: {
    runScene(scene) {
      uni.showToast({
        title: `执行：${scene.name}`,
        icon: "success"
      })
    }
  }
}
</script>

<style>
.page { padding: 20rpx; }
.scene-item {
  padding: 30rpx; background: #2d5cf7; color: #fff;
  border-radius: 20rpx; margin-bottom: 20rpx;
}
.scene-name { font-size: 36rpx; font-weight: bold; display: block; }
.desc { font-size: 28rpx; opacity: 0.8; }
</style>
