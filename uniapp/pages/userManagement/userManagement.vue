<template>
  <view class="container">
    <image src="@/static/img/home_bg.png" class="bg"></image>
    <view class="overlay"></view>

    <view class="content">
      <view class="card">
        <!-- 管理员提示 -->
        <view class="admin-tip">管理员可删除用户或修改角色</view>
        
        <!-- 用户列表：显示角色 + 新增修改角色按钮 -->
        <view v-for="(user, index) in users" :key="index" class="user-item">
          <view class="user-info">
            <text class="username">{{ user.username }}</text>
            <!-- 显示用户角色标签 -->
            <text class="role-tag" :class="user.role === 'admin' ? 'admin-tag' : 'user-tag'">
              {{ user.role === 'admin' ? '管理员' : '普通用户' }}
            </text>
            <text class="time">注册时间：{{ user.registerTime }}</text>
          </view>
          
          <view class="user-actions">
            <!-- 修改角色按钮：不允许修改自己的角色 -->
            <button 
              class="btn-role" 
              @click="changeRole(user)"
              v-if="currentUser.username !== user.username"
            >
              {{ user.role === 'admin' ? '设为普通用户' : '设为管理员' }}
            </button>
            
            <!-- 删除按钮：防止删除最后一个管理员 -->
            <button class="btn-del" @click="deleteUser(user)">删除</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return { 
      users: [],
      currentUser: {} // 当前登录的管理员信息
    };
  },
  onLoad() {
    // 新增：权限校验（非管理员禁止进入）
    this.currentUser = uni.getStorageSync("currentUser") || {};
    if (this.currentUser.role !== 'admin') {
      uni.showToast({ title: "无权限访问，仅管理员可进入", icon: "none" });
      setTimeout(() => {
        uni.switchTab({ url: "/pages/mine/mine" }); // 跳回「我的」页面
      }, 1000);
      return;
    }
    // 管理员：加载用户列表
    this.loadUsers();
  },
  methods: {
    // 加载用户列表
    loadUsers() {
      this.users = uni.getStorageSync("users") || [];
    },
    
    // 新增：修改用户角色
    changeRole(user) {
      const newRole = user.role === 'admin' ? 'user' : 'admin';
      uni.showModal({
        title: "修改角色",
        content: `确定将 ${user.username} 设为${newRole === 'admin' ? '管理员' : '普通用户'}？`,
        success: (res) => {
          if (res.confirm) {
            // 更新用户角色
            this.users = this.users.map(u => 
              u.username === user.username ? { ...u, role: newRole } : u
            );
            // 同步存储
            uni.setStorageSync("users", this.users);
            uni.showToast({ title: "角色修改成功" });
            this.loadUsers(); // 重新加载列表
          }
        }
      });
    },
    
    // 优化：删除用户（防止删除最后一个管理员）
    deleteUser(user) {
      // 1. 禁止删除当前登录用户
      if (this.currentUser.username === user.username) {
        uni.showToast({ title: "不能删除当前登录用户", icon: "none" });
        return;
      }

      // 2. 禁止删除最后一个管理员
      const adminCount = this.users.filter(u => u.role === 'admin').length;
      if (user.role === 'admin' && adminCount === 1) {
        uni.showToast({ title: "不能删除最后一个管理员", icon: "none" });
        return;
      }

      // 3. 执行删除
      uni.showModal({
        title: "删除用户",
        content: `确定删除用户 ${user.username}？删除后该用户的所有设备也将被清除。`,
        success: (res) => {
          if (res.confirm) {
            this.users = this.users.filter(u => u.username !== user.username);
            uni.setStorageSync("users", this.users);
            
            // 同时删除该用户的所有设备
            this.$store.commit('DELETE_USER_DEVICES', user.username);
            
            uni.showToast({ title: "删除成功", icon: "success" });
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
.overlay { position: absolute; width: 100%; height: 100%; background: rgba(0,0,0,0.3); }
.content { position: relative; z-index: 2; padding: 30rpx; }

/* 卡片容器 */
.card { 
  background: rgba(255,255,255,0.95); 
  border-radius: 20rpx; 
  padding: 20rpx; 
}

/* 管理员提示 */
.admin-tip { 
  font-size: 24rpx; 
  color: #007AFF; 
  margin-bottom: 20rpx; 
}

/* 用户项布局 */
.user-item { 
  display: flex; 
  justify-content: space-between; 
  align-items: flex-start; 
  padding: 20rpx 0; 
  border-bottom: 1rpx solid #eee; 
}
.user-info { flex: 1; margin-right: 20rpx; }

/* 角色标签 */
.role-tag { 
  font-size: 22rpx; 
  padding: 3rpx 10rpx; 
  border-radius: 6rpx; 
  margin-left: 10rpx; 
}
.admin-tag { background: #007AFF; color: #fff; }
.user-tag { background: #eee; color: #666; }

.time { 
  font-size: 24rpx; 
  color: #666; 
  display: block; 
  margin-top: 8rpx; 
}

/* 操作按钮组 */
.user-actions { 
  display: flex; 
  flex-direction: column; 
  gap: 10rpx; 
}
.btn-role { 
  background: #007AFF; 
  color: #fff; 
  padding: 8rpx 15rpx; 
  border-radius: 15rpx; 
  font-size: 22rpx; 
  border: none;
}
.btn-del { 
  background: #ff4d4f; 
  color: #fff; 
  padding: 8rpx 15rpx; 
  border-radius: 15rpx; 
  font-size: 22rpx; 
  border: none;
}
</style>