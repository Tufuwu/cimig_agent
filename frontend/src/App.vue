<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()

const goHome = () => router.push('/')
const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')

</script>

<template>

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



</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
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



</style>
