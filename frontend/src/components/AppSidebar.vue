<template>
  <div class="sidebar panel">
    <div class="brand">
      <div class="brand-logo">
        <img src="/logo.jpg" alt="闲置市场" />
      </div>
      <div class="brand-copy">
        <div class="eyebrow">Marketplace</div>
        <strong>{{ title }}</strong>
        <p>{{ subtitle }}</p>
      </div>
    </div>
    <div class="nav-group">
      <div class="nav-caption">工作区</div>
      <RouterLink
        v-for="item in primaryItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ 'is-active': isItemActive(item) }"
      >
        <span class="nav-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </div>
    <div v-if="accountItems.length" class="nav-group secondary-group">
      <div class="nav-caption">账户</div>
      <RouterLink
        v-for="item in accountItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ 'is-active': isItemActive(item) }"
      >
        <span class="nav-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  items: { type: Array, required: true }
})

const route = useRoute()
const primaryItems = computed(() => props.items.filter((item) => item.to !== '/profile'))
const accountItems = computed(() => props.items.filter((item) => item.to === '/profile'))

function isItemActive(item) {
  if (item.activePrefix) {
    return route.path.startsWith(item.activePrefix)
  }
  return route.path === item.to
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 24px;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 4px 8px;
  border-bottom: 1px solid var(--line);
}

.brand-copy {
  min-width: 0;
}

.brand p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.55;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--line);
}

.brand-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand strong {
  display: block;
  font-size: 0.98rem;
  line-height: 1.2;
}

.nav-caption {
  padding: 0 8px;
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: none;
}

.nav-group {
  display: grid;
  gap: 4px;
}

.secondary-group {
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text);
  border: 1px solid transparent;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.nav-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--surface-soft);
  color: var(--muted);
}

.nav-link:hover,
.nav-link.is-active {
  background: var(--surface-soft);
  border-color: var(--line);
}

.nav-link.is-active {
  color: var(--brand-strong);
}

.nav-link.is-active .nav-icon {
  background: var(--brand-soft);
  color: var(--brand);
}

.nav-link.is-active::before {
  content: "";
  position: absolute;
  left: -1px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  border-radius: 999px;
  background: var(--brand);
}
</style>
