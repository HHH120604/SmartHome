<template>
  <view class="container">
    <image class="bg" src="../../static/img/home_bg.png" mode="widthFix"></image>
    <view class="overlay"></view>

    <!-- 登录卡片 -->
    <view class="login-card">
      <view class="logo-container">
        <image src="../../static/icon/logo.png" class="logo" mode="widthFix"></image>
        <text class="app-name">CQU Home</text>
      </view>
      
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
            placeholder="请输入密码" 
            class="input-field" 
            password 
            clear
            :border="false"
          ></u-input>
        </view>
      </view>
      
      <button class="login-btn" @click="login">
        <text class="btn-text">登录</text>
      </button>
      
      <view class="register-link" @click="goRegister">
        <text>还没有账号？</text>
        <text class="highlight">立即注册</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    login() {
      // 原有校验逻辑保留
      // if (!this.username || !this.password) {
      //   uni.showToast({ title: "请输入账号密码", icon: "none" });
      //   return;
      // }
      
      // const users = uni.getStorageSync("users") || [];
      // const user = users.find(u => u.username === this.username);
      
      // if (!user) {
      //   uni.showToast({ title: "用户不存在", icon: "none" });
      //   return;
      // }
      // if (user.password !== this.password) {
      //   uni.showToast({ title: "密码错误", icon: "none" });
      //   return;
      // }

      let users = uni.getStorageSync("users") || [];
      const user = {
        username: "房主",
        password: "123456",
        registerTime: new Date().toLocaleString(),
        role: 'admin'
      };
      
      users.push(user);
      uni.setStorageSync("users", users);

      // 正确设置store中的currentUser
      this.$store.commit('SET_CURRENT_USER', user);
      
      // 自动同步含role的用户信息
      uni.setStorageSync("isLogin", true);
      uni.setStorageSync("currentUser", user);
	    console.log(user);
      uni.reLaunch({ url: "/pages/index/index" });
    },
    goRegister() {
      uni.navigateTo({ url: "/pages/register/register" });
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

.login-card {
  position: relative;
  z-index: 3;
  width: 85%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 15rpx 40rpx rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.logo {
  width: 140rpx;
  height: 140rpx;
  margin-bottom: 20rpx;
}

.app-name {
  font-size: 40rpx;
  font-weight: bold;
  color: #007AFF;
  letter-spacing: 2rpx;
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

.login-btn {
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

.register-link {
  font-size: 28rpx;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.highlight {
  color: #007AFF;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 4rpx;
}
</style>