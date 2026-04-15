<template>
  <section class="panel preview-card">
    <div class="preview-media">
      <img v-if="coverImage" :src="coverImage" :alt="product.title || '商品预览'">
      <div v-else class="preview-placeholder">Preview</div>
    </div>

    <div class="preview-body">
      <div class="preview-topline">
        <span class="preview-status">{{ conditionLabel }}</span>
        <span v-if="categoryLabel" class="preview-status muted">{{ categoryLabel }}</span>
      </div>

      <h3 class="preview-title">{{ product.title || '未命名商品' }}</h3>
      <div class="preview-price">¥ {{ Number(product.price || 0).toFixed(2) }}</div>
      <p class="preview-summary">{{ summaryText }}</p>

      <div v-if="sellingPoints.length" class="preview-tags">
        <span v-for="item in sellingPoints" :key="item" class="preview-tag">{{ item }}</span>
      </div>

      <div class="preview-foot">
        <span>库存 {{ product.stock || 1 }}</span>
        <span>{{ assetCount }} 张图片</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  coverImage: {
    type: String,
    default: ''
  },
  sellingPoints: {
    type: Array,
    default: () => []
  },
  conditionLabel: {
    type: String,
    default: '成色待补充'
  },
  categoryLabel: {
    type: String,
    default: ''
  },
  assetCount: {
    type: Number,
    default: 0
  }
})

const summaryText = computed(() => {
  if (!props.product.description) {
    return '描述区会在这里生成更接近真实商品卡片的摘要预览。'
  }
  return props.product.description
})
</script>

<style scoped>
.preview-card {
  overflow: hidden;
}

.preview-media {
  height: 212px;
  background: linear-gradient(180deg, #edf4fc 0%, #e7eef7 100%);
  border-bottom: 1px solid var(--line);
}

.preview-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(15, 23, 42, 0.26);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.preview-body {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.preview-topline {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preview-status {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 0.76rem;
  font-weight: 700;
}

.preview-status.muted {
  background: #f4f7fb;
  color: var(--muted);
}

.preview-title {
  margin: 0;
  font-size: 1.18rem;
  line-height: 1.35;
  letter-spacing: -0.02em;
}

.preview-price {
  font-size: 1.22rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.preview-summary {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-tag {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f5f8fd;
  color: var(--text);
  font-size: 0.78rem;
  font-weight: 600;
}

.preview-foot {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
  font-size: 0.8rem;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
</style>
