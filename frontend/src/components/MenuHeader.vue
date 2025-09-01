<template>
  <div class="menu-header">
    <i class="fas fa-list"></i>
    菜单功能
  </div>
</template>

<script>
export default {
  name: 'MenuHeader'
}
</script>

<style scoped>
.menu-header {
  background: linear-gradient(135deg, #1976D2 0%, #42A5F5 100%);
  color: white;
  padding: 20px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
  margin-bottom: 0;
}

.menu-header i {
  font-size: 20px;
  color: white;
}
</style> 