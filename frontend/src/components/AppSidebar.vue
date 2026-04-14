<template>
  <div class="sidebar panel">
    <div class="brand">
      <div class="brand-badge">AM</div>
      <div>
        <strong>{{ title }}</strong>
        <p>{{ subtitle }}</p>
      </div>
    </div>
    <RouterLink
      v-for="item in items"
      :key="item.to"
      class="nav-link"
      :to="item.to"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </RouterLink>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  items: { type: Array, required: true }
})
</script>

<style scoped>
.sidebar {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.brand p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.brand-badge {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-weight: 800;
  background: linear-gradient(135deg, var(--brand), #d28f4f);
  color: white;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  color: var(--text);
  transition: transform 0.18s ease, background 0.18s ease;
}

.nav-link:hover,
.router-link-active {
  transform: translateX(4px);
  background: rgba(176, 88, 46, 0.12);
}
</style>

