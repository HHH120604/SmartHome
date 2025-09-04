<template>
  <view class="container">
    <image class="bg" src="../../static/img/home_bg.png" mode="widthFix"></image>
    <view class="overlay"></view>

    <!-- 修改密码卡片 -->
    <view class="change-card">
      <view class="title">修改密码</view>
      
      <view class="input-group">
        <view class="input-item">
          <image src="../../static/icon/lock.png" class="input-icon"></image>
          <u-input 
            v-model="oldPassword" 
            placeholder="请输入旧密码" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
        
        <view class="input-item">
          <image src="../../static/icon/new_password.png" class="input-icon"></image>
          <u-input 
            v-model="newPassword" 
            placeholder="请输入新密码（至少6位）" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
        
        <view class="input-item">
          <image src="../../static/icon/confirm_password.png" class="input-icon"></image>
          <u-input 
            v-model="confirmPassword" 
            placeholder="请再次输入新密码" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
      </view>
      
      <button class="confirm-btn" @click="changePassword">
        <text class="btn-text">确认修改</text>
      </button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  },
  methods: {
    changePassword() {
      const user = uni.getStorageSync("currentUser");
      if (!user) {
        uni.showToast({ title: "未登录", icon: "none" });
        return;
      }
      
      if (this.oldPassword !== user.password) {
        uni.showToast({ title: "旧密码错误", icon: "none" });
        return;
      }
      
      if (this.newPassword.length < 6) {
        uni.showToast({ title: "新密码长度不能少于6位", icon: "none" });
        return;
      }
      
      if (this.newPassword !== this.confirmPassword) {
        uni.showToast({ title: "两次密码不一致", icon: "none" });
        return;
      }
      
      let users = uni.getStorageSync("users") || [];
      const index = users.findIndex(u => u.username === user.username);
      if (index !== -1) {
        users[index].password = this.newPassword;
        uni.setStorageSync("users", users);
        uni.setStorageSync("currentUser", users[index]);
        uni.showToast({ title: "修改成功", icon: "success" });
        uni.navigateBack();
      }
    }
  }
}
</script>

<style scoped lang="scss">
.container {
  width: 100%;
  height: 100vh;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.bg {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6));
  z-index: 2;
}

.change-card {
  position: relative;
  z-index: 3;
  width: 85%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 15rpx 40rpx rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 50rpx;
  text-align: center;
}

.input-group {
  width: 100%;
  margin-bottom: 50rpx;
}

.input-item {
  width: 100%;
  height: 90rpx;
  background: #f5f7fa;
  border-radius: 15rpx;
  display: flex;
  align-items: center;
  padding: 0 30rpx;
  margin-bottom: 25rpx;
  transition: all 0.3s ease;
  
  &:focus-within {
    box-shadow: 0 0 0 2rpx #007AFF;
  }
}

.input-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 20rpx;
  opacity: 0.6;
}

.input-field {
  flex: 1;
  font-size: 28rpx;
  height: 100%;
}

.confirm-btn {
  width: 100%;
  height: 96rpx;
  background: #007AFF;
  color: #fff;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  transition: all 0.3s ease;
  
  &:hover {
    background: #0066cc;
  }
  
  &:active {
    transform: scale(0.98);
  }
}
</style>

