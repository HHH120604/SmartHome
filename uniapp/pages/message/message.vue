<template>
  <view class="container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">安全提示</text>
      <text class="message-count">{{ messageList.length }} 条消息</text>
    </view>
    
    <!-- 消息状态筛选 -->
    <view class="filter-bar">
      <view class="filter-item" :class="{active: filterType === 'all'}" @click="filterType = 'all'">全部</view>
      <view class="filter-item" :class="{active: filterType === 'unread'}" @click="filterType = 'unread'">未读</view>
      <view class="filter-item" :class="{active: filterType === 'read'}" @click="filterType = 'read'">已读</view>
    </view>

    <!-- 消息列表 -->
    <view class="message-list">
      <!-- 循环显示消息 -->
      <view 
        v-for="msg in filteredMessages" 
        :key="msg.id" 
        class="card" 
        :class="[getCardClass(msg.type), { 'unread': !msg.read }]"
        @click="markAsRead(msg.id)"
      >
        <!-- 未读标记 -->
        <view v-if="!msg.read" class="unread-dot"></view>
        
        <view class="card-header">
          <view class="icon-wrapper">
            <text class="icon">{{ getIcon(msg.type) }}</text>
          </view>
          <text class="msg-content">{{ msg.content }}</text>
        </view>
        
        <view class="card-footer">
          <!-- 消息类型标签 -->
          <view class="msg-type-tag">{{ getTypeText(msg.type) }}</view>
          <text class="msg-time">{{ formatTime(msg.time) }}</text>
        </view>

        <!-- 删除按钮 -->
        <button class="delete-btn" @click.stop="handleDelete(msg.id)">
          <text>×</text>
        </button>
      </view>
      
      <!-- 空状态 -->
        <view v-if="filteredMessages.length === 0" class="empty-state">
          <image src="../../static/img/empty.svg" mode="aspectFit" class="empty-image"></image>
          <text class="empty-text">暂无消息</text>
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
      filterType: 'all'  // 筛选类型：all, unread, read
    }
  },
  computed: {
    // 从Vuex获取消息列表
    messageList() {
      return this.$store.getters.getMessages
    },
    // 筛选后的消息列表
    filteredMessages() {
      if (this.filterType === 'all') {
        return this.messageList
      } else if (this.filterType === 'unread') {
        return this.messageList.filter(msg => !msg.read)
      } else if (this.filterType === 'read') {
        return this.messageList.filter(msg => msg.read)
      }
      return this.messageList
    }
  },
  methods: {
    // 获取消息卡片样式
    getCardClass(type) {
      switch(type) {
        case 'fire': return 'card-fire'
        case 'water': return 'card-water'
        case 'gas': return 'card-gas'
        case 'motion': return 'card-motion'
      default: return 'card-default'
    }
    },

    // 获取图标
    getIcon(type) {
      switch(type) {
        case 'fire': return '🔥'
        case 'water': return '💧'
        case 'gas': return '🛢'
        case 'motion': return '👤'
        default: return '🔔'
      }
    },
    
    // 获取类型文本
    getTypeText(type) {
      switch(type) {
        case 'fire': return '火灾预警'
        case 'water': return '水浸预警'
        case 'gas': return '燃气预警'
        case 'motion': return '移动侦测'
        default: return '系统消息'
      }
    },
    
    // 格式化时间
    formatTime(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 小于1分钟
      if (diff < 60000) {
        return '刚刚'
      }
      // 小于1小时
      else if (diff < 3600000) {
        return Math.floor(diff / 60000) + '分钟前'
      }
      // 小于24小时
      else if (diff < 86400000) {
        return Math.floor(diff / 3600000) + '小时前'
      }
      // 大于等于24小时
      else {
        return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
      }
    },
    

    // 删除消息
    deleteMessage(messageId) {
      uni.request({
        url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DELETE_MESSAGE}${messageId}`,
        method: 'DELETE',
        timeout: API_CONFIG.TIMEOUT,
        success: (res) => {
          if (res.statusCode === 200) {
            // 从Vuex store中删除消息
            this.$store.commit('REMOVE_MESSAGE', messageId)
          } else {
            console.error("删除失败", res)
            // 可以在这里添加提示用户的逻辑
          }
        },
        fail: (err) => {
          console.error("删除请求失败:", err)
          // 可以在这里添加重试逻辑或提示用户
        }
      })
    },
    
    // 标记为已读
    markAsRead(messageId) {
      // 更新Vuex store中的消息状态
      this.$store.commit('MARK_MESSAGE_AS_READ', messageId)
    },
    
    // 处理删除操作
    handleDelete(messageId) {
      // 使用uni.showModal实现删除确认
      uni.showModal({
        title: '确认删除',
        content: '确定要删除这条消息吗？',
        confirmText: '确定',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            this.deleteMessage(messageId)
            uni.showToast({
              title: '删除成功',
              icon: 'success',
              duration: 2000
            })
          }
        }
      })
    }
  },
  onLoad() {

  }
}
</script>

<style scoped>
/* 全局样式 */
.container {
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 44rpx;
  font-weight: bold;
  color: #333;
}

.message-count {
  font-size: 28rpx;
  color: #666;
  background-color: #f0f0f0;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 10rpx 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.filter-item {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: #666;
  border-radius: 16rpx;
  transition: all 0.3s;
}

.filter-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 600;
}

/* 消息列表 */
.message-list {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

/* 消息卡片 */
.card {
  padding: 30rpx;
  border-radius: 20rpx;
  margin-bottom: 20rpx;
  color: #fff;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.15);
}

/* 未读消息样式 */
.card.unread {
  border: 4rpx solid rgba(255, 255, 255, 0.8);
  transform: translateX(0);
  animation: pulse 2s infinite;
}

/* 未读标记 */
.unread-dot {
  position: absolute;
  top: 30rpx;
  right: 30rpx;
  width: 20rpx;
  height: 20rpx;
  background-color: #ff4d4f;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.8);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20rpx;
}

.icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  border-radius: 16rpx;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.icon {
  font-size: 48rpx;
}

.msg-content {
  font-size: 34rpx;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
  word-wrap: break-word;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 消息类型标签 */
.msg-type-tag {
  font-size: 24rpx;
  background-color: rgba(255, 255, 255, 0.3);
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
}

.msg-time {
  font-size: 24rpx;
  opacity: 0.8;
}

/* 删除按钮 */
.delete-btn {
  position: absolute;
  top: 10rpx;
  right: 60rpx;
  width: 60rpx;
  height: 60rpx;
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  font-size: 40rpx;
  opacity: 1;
  transition: all 0.3s;
  font-weight: bold;
}

.delete-btn:active {
  background-color: rgba(255, 255, 255, 0.4);
}

/* 消息类型颜色 */
.card-fire { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
.card-water { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
.card-gas { background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }
.card-motion { background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); }
.card-default { background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%); }

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 100rpx 0;
}

.empty-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 30rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #999;
}

/* 动画效果 */
@keyframes pulse {
  0% {
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.15);
  }
  50% {
    box-shadow: 0 8rpx 40rpx rgba(0, 0, 0, 0.25);
  }
  100% {
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.15);
  }
}

/* 点击效果 */
.card:active {
  transform: scale(0.98);
}
</style>