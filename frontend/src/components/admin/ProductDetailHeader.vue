<template>
  <section class="panel header-card">
    <div class="header-main">
      <div>
        <div class="eyebrow">Product Detail</div>
        <h2>{{ product.title || `商品 ${product.id}` }}</h2>
        <p>{{ product.description || '暂无描述' }}</p>
      </div>
      <div class="header-aside">
        <div class="price">¥ {{ Number(product.price || 0).toFixed(2) }}</div>
        <div class="status-row">
          <AuditStatusBadge :status="product.audit_status" />
          <AuditStatusBadge :status="product.product_status" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import AuditStatusBadge from './AuditStatusBadge.vue'

defineProps({
  product: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.header-card {
  padding: 22px;
}

.header-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.header-main h2 {
  margin: 0 0 8px;
  font-size: 1.48rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.03em;
}

.header-main p {
  margin: 0;
  max-width: 64ch;
  color: var(--muted);
  line-height: 1.65;
}

.header-aside {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.price {
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.status-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .header-main {
    flex-direction: column;
  }

  .header-aside {
    justify-items: start;
  }
}
</style>
