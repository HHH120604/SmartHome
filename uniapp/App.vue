<script>
import store from "./store/index.js"
export default {
  onLaunch() {
    console.log("App Launch")
    // 检查登录状态并从localStorage恢复用户信息
    const isLogin = uni.getStorageSync('isLogin');
    const currentUser = uni.getStorageSync('currentUser');
    
    if (isLogin && currentUser) {
      // 设置当前用户到store
      store.commit('SET_CURRENT_USER', currentUser);
    } else if (!store.getters.isLoggedIn) {
      // 用户未登录，跳转到登录页
      uni.reLaunch({
        url: "/pages/login/login"
      })
    }
  },
  onShow() {
    console.log("App Show")
  },
  onHide() {
    console.log("App Hide")
  }
}
</script>

<style lang="scss">
@import "uview-ui/index.scss";
body,
html,
page {
  padding: 0;
  margin: 0;
  height: 100%;
}
</style>

