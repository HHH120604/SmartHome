<template>
  <view v-if="show" class="confirm-dialog-overlay" @click.self="handleCancel">
    <view class="confirm-dialog">
      <!-- 图标区域 -->
      <view class="dialog-icon">
        <image :src="iconSrc" mode="aspectFit" class="icon-image"></image>
      </view>
      
      <!-- 标题 -->
      <text class="dialog-title">{{ title }}</text>
      
      <!-- 内容 -->
      <text class="dialog-content">{{ content }}</text>
      
      <!-- 按钮区域 -->
      <view class="dialog-buttons">
        <button class="cancel-btn" @click="handleCancel">{{ cancelText }}</button>
        <button class="confirm-btn" @click="handleConfirm">{{ confirmText }}</button>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'confirm-dialog',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '确认操作'
    },
    content: {
      type: String,
      default: '确定要执行此操作吗？'
    },
    confirmText: {
      type: String,
      default: '确定'
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    iconType: {
      type: String,
      default: 'warning'
    }
  },
  computed: {
    iconSrc() {
      // 根据不同的图标类型返回不同的图标路径
      const iconMap = {
        warning: '../../static/icon/lock.png',
        delete: '../../static/icon/delete-icon.svg',
        success: '../../static/icon/dianzan_active.png'
      }
      return iconMap[this.iconType] || iconMap.warning
    }
  },
  methods: {
    handleConfirm() {
      this.$emit('confirm')
    },
    handleCancel() {
      this.$emit('cancel')
    }
  }
}
</script>

<style scoped>
/* 遮罩层 */
.confirm-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  animation: fadeIn 0.3s;
}

/* 弹窗容器 */
.confirm-dialog {
  width: 600rpx;
  background-color: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  text-align: center;
  box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.2);
  animation: scaleIn 0.3s;
}

/* 图标区域 */
.dialog-icon {
  margin-bottom: 30rpx;
  display: flex;
  justify-content: center;
}

.icon-image {
  width: 120rpx;
  height: 120rpx;
}

/* 标题 */
.dialog-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

/* 内容 */
.dialog-content {
  font-size: 32rpx;
  color: #666;
  line-height: 1.5;
  display: block;
  margin-bottom: 40rpx;
}

/* 按钮区域 */
.dialog-buttons {
  display: flex;
  justify-content: space-between;
}

/* 取消按钮 */
.cancel-btn {
  flex: 1;
  margin-right: 20rpx;
  background-color: #f5f5f5;
  color: #666;
  font-size: 32rpx;
  height: 90rpx;
  line-height: 90rpx;
  border-radius: 45rpx;
  border: none;
}

/* 确认按钮 */
.confirm-btn {
  flex: 1;
  margin-left: 20rpx;
  background-color: #e74c3c;
  color: #fff;
  font-size: 32rpx;
  height: 90rpx;
  line-height: 90rpx;
  border-radius: 45rpx;
  border: none;
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* 按钮点击效果 */
.cancel-btn:active {
  background-color: #e0e0e0;
}

.confirm-btn:active {
  background-color: #c0392b;
}
</style>