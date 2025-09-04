<template>
  <view class="card" @click="goDetail">
    <image class="icon" :src="iconSrc" mode="aspectFit"></image>
    <view class="name">{{ device.name }}</view>
    <u-switch v-model="localOn" @change="onToggle" size="20"></u-switch>
  </view>
</template>

<script>
export default {
  props: { device: { type: Object, required: true } },
  data() {
    return { localOn: this.device.on }
  },
  computed: {
    iconSrc() {
      const base = '/static/icon/'
      const map = {
        light: [ 'light_off.png', 'light_on.png' ],
        fan:   [ 'fan_off.png',   'fan_on.png'   ],
        ac:    [ 'ac_off.png',    'ac_on.png'    ],
      }
      const pair = map[this.device.type] || [ 'device_off.png', 'device_on.png' ]
      return base + (this.localOn ? pair[1] : pair[0])
    }
  },
  methods: {
    onToggle() {
      this.$emit('toggle', { id: this.device.id, type: this.device.type, on: this.localOn })
    },
    goDetail() {
      const pageMap = { light: 'light', fan: 'fan', ac: 'ac' }
      const page = pageMap[this.device.type] || 'light'
      uni.navigateTo({ url: `/pages/device-detail/${page}?id=${this.device.id}` })
    }
  },
  watch: {
    'device.on'(v){ this.localOn = v }
  }
}
</script>

<style lang="scss" scoped>
.card {
  width: 46%;
  margin: 2%;
  padding: 28rpx;
  background: #fff;
  border-radius: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(0,0,0,.06);
  display: flex; flex-direction: column; align-items: center; gap: 16rpx;
}
.icon { width: 120rpx; height: 120rpx; }
.name { font-size: 28rpx; color: #333; }
</style>
