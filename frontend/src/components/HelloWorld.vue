<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()

const goHome = () => router.push('/')
const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')

</script>

<template>
  <div id="app">
    <!-- 导航栏 -->
    <header class="nav-header">
      <div class="nav-content">
        <!-- Logo -->
        <div class="nav-left">
          <div class="nav-logo" @click="goHome">
            <span class="logo-text">CIMigAgent</span>
          </div>
        </div>
        <div class="nav-right">
          <div class="nav-logo" @click="goLogin">
            <span class="logo-text">登录</span>
          </div>

          <div class="nav-logo" @click="goRegister">
            <span class="logo-text">登出</span>
          </div>
        </div>
      </div>
    </header>

    <main>
      <router-view></router-view>
    </main>


  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 导航栏 */
.nav-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.nav-content {
  max-width: auto;
  margin: 0 auto;
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left{

}

.nav-right {
  margin-left: auto; /* 核心！把右侧整体推到最右 */
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-logo:hover {
  opacity: 0.8;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #000005;
  letter-spacing: -0.5px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  color: #666;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #1a1a2e;
  background: #f0f0f0;
}

.nav-link.active {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.login-btn {
  color: #666 !important;
  font-weight: 500;
}

.login-btn:hover {
  color: #1a1a2e !important;
}

.signup-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
  border-radius: 8px;
}

.signup-btn:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
}

/* 主内容区 */
.main-content {
  flex: 1;
  margin-top: 64px;
  background: #f5f7fa;
}

/* 页脚 */
.app-footer {
  background: white;
  border-top: 1px solid #e8e8e8;
  padding: 24px 40px;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.footer-divider {
  margin: 0 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .nav-content {
    padding: 0 20px;
  }

  .nav-links {
    display: none;
  }

  .logo-text {
    font-size: 16px;
  }
}
</style>