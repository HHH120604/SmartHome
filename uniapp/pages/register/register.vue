<template>
  <view class="container">
    <image class="bg" src="../../static/img/home_bg.png" mode="widthFix"></image>
    <view class="overlay"></view>

    <!-- 注册卡片 -->
    <view class="register-card">
      <view class="title">创建账号</view>
      
      <view class="input-group">
        <view class="input-item">
          <image src="../../static/icon/user.png" class="input-icon"></image>
          <u-input 
            v-model="username" 
            placeholder="请输入用户名" 
            class="input-field" 
            clear
            :border="false"
          ></u-input>
        </view>
        
        <view class="input-item">
          <image src="../../static/icon/password.png" class="input-icon"></image>
          <u-input 
            v-model="password" 
            placeholder="请输入密码（至少6位）" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
        
        <view class="input-item">
          <image src="../../static/icon/password.png" class="input-icon"></image>
          <u-input 
            v-model="confirmPassword" 
            placeholder="请再次输入密码" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
      </view>
      
      <button class="register-btn" @click="register">
        <text class="btn-text">注册</text>
      </button>
      
      <view class="login-link" @click="goLogin">
        <text>已有账号？</text>
        <text class="highlight">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: '',
      confirmPassword: ''
    }
  },
  methods: {
    register() {
      // 原有校验逻辑保留
      if (!this.username || !this.password || !this.confirmPassword) {
        uni.showToast({ title: "请输入完整信息", icon: "none" });
        return;
      }
      if (this.password.length < 6) {
        uni.showToast({ title: "密码长度不能少于6位", icon: "none" });
        return;
      }
      if (this.password !== this.confirmPassword) {
        uni.showToast({ title: "两次密码不一致", icon: "none" });
        return;
      }
      
      let users = uni.getStorageSync("users") || [];
      if (users.find(u => u.username === this.username)) {
        uni.showToast({ title: "用户已存在", icon: "none" });
        return;
      }
      
      // 新增：角色分配（第一个用户→管理员，其余→普通用户）
      const newUser = {
        username: this.username,
        password: this.password,
        registerTime: new Date().toLocaleString(),
        role: users.length === 0 ? 'admin' : 'user' // 核心：角色字段
      };
      
      users.push(newUser);
      uni.setStorageSync("users", users);
      
      // 新增：提示第一个用户成为管理员
      if (newUser.role === 'admin') {
        uni.showToast({ title: "注册成功！您是第一个用户，自动成为管理员", icon: "none", duration: 2000 });
      } else {
        uni.showToast({ title: "注册成功", icon: "success" });
      }
      
      uni.navigateBack();
    },
    goLogin() {
      uni.navigateBack();
    }
  }
}
</script>

<style scoped lang="scss">
/* 原有样式不变，无需修改 */
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

.register-card {
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

.register-btn {
  width: 100%;
  height: 96rpx;
  background: #007AFF;
  color: #fff;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 30rpx;
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

.login-link {
  font-size: 28rpx;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.highlight {
  color: #007AFF;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 4rpx;
}
</style>