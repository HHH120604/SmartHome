<template>
  <view class="container">
    <image src="@/static/img/home_bg.png" class="bg"></image>
    <view class="overlay"></view>

    <view class="content">
      <!-- 用户信息：新增角色显示 -->
      <view class="userinfo-card">
        <view class="user-info-row">
          <text class="username">{{ username }}</text>
          <text class="status">{{ isLogin ? "已登录" : "未登录" }}</text>
        </view>
        <!-- 新增：显示当前用户角色 -->
        <view class="role-tag" v-if="isLogin">
          角色：{{ currentUser.role === 'admin' ? '管理员' : '普通用户' }}
        </view>
      </view>

      <!-- 功能菜单：按角色控制显示 -->
      <view class="menu-card">
        <!-- 管理员专属：用户管理 -->
        <view class="menu-item" @click="goUserManagement" v-if="isAdmin">
          <image src="@/static/icon/friend.png" class="icon-img"/>
          <text class="menu-text">用户管理</text>
        </view>

        <!-- 所有登录用户可见：修改密码 -->
        <view class="menu-item" @click="goChangePassword" v-if="isLogin">
          <image src="@/static/icon/device_active.png" class="icon-img"/>
          <text class="menu-text">修改密码</text>
        </view>

        <!-- 所有登录用户可见：退出登录 -->
        <view class="menu-item" @click="logout" v-if="isLogin">
          <image src="@/static/icon/out.png" class="icon-img"/>
          <text class="menu-text">退出登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return { 
      isLogin: false, 
      username: "游客",
      currentUser: {} // 存储含角色的当前用户信息
    };
  },
  computed: {
    // 新增：判断是否为管理员
    isAdmin() {
      return this.isLogin && this.currentUser.role === 'admin';
    }
  },
  onShow() {
    // 读取登录状态和用户信息（含角色）
    this.isLogin = uni.getStorageSync("isLogin") || false;
    this.currentUser = uni.getStorageSync("currentUser") || {};
    this.username = this.isLogin ? this.currentUser.username : "游客";
  },
  methods: {
    goUserManagement() {
      uni.navigateTo({ url: "/pages/userManagement/userManagement" });
    },
    goChangePassword() {
      uni.navigateTo({ url: "/pages/changePassword/changePassword" });
    },
    logout() {
      uni.showModal({
        title: "退出登录", 
        content: "确定要退出登录吗？",
        success: (res) => {
          if (res.confirm) {
            uni.removeStorageSync("isLogin");
            uni.removeStorageSync("currentUser");
            this.isLogin = false;
            this.username = "游客";
            uni.reLaunch({ url: "/pages/login/login" });
          }
        }
      });
    }
  }
};
</script>

<style scoped lang="scss">
.container { position: relative; width: 100%; height: 100vh; }
.bg { position: absolute; width: 100%; height: 100%; object-fit: cover; }
.overlay { position: absolute; width: 100%; height: 100%; background: rgba(0,0,0,0.25); }
.content { position: relative; z-index: 2; display: flex; flex-direction: column; padding: 50rpx 20rpx; }

/* 用户信息卡片 */
.userinfo-card {
  width: 90%; 
  background: rgba(255,255,255,0.95); 
  border-radius: 20rpx; 
  padding: 30rpx; 
  margin-bottom: 30rpx;
}
.user-info-row { 
  display: flex; 
  align-items: center;
  .username { font-size: 32rpx; font-weight: bold; margin-right: 20rpx; }
  .status { font-size: 26rpx; color: #38f9d7; }
}
/* 新增：角色标签样式 */
.role-tag {
  font-size: 24rpx;
  color: #007AFF;
  margin-top: 15rpx;
  padding: 5rpx 10rpx;
  background: rgba(0, 122, 255, 0.1);
  border-radius: 8rpx;
}

/* 菜单卡片 */
.menu-card { 
  width: 90%; 
  background: rgba(255,255,255,0.95); 
  border-radius: 20rpx; 
  box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.15);
  display: flex; 
  flex-direction: column; 
  padding: 20rpx; 
}
.menu-item { 
  display: flex; 
  align-items: center; 
  padding: 20rpx 0; 
  border-bottom: 1rpx solid #eee; 
}
.icon-img { width: 40rpx; height: 40rpx; margin-right: 20rpx; }
.menu-text { font-size: 28rpx; color: #333; }
</style>