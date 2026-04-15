<template>
  <section class="gallery-shell">
    <div class="stage-wrap">
      <div class="stage-meta">
        <span class="stage-kicker">{{ category || '商品图集' }}</span>
        <span class="stage-count">{{ normalizedImages.length ? `${currentIndex + 1} / ${normalizedImages.length}` : '暂无图片' }}</span>
      </div>
      <div class="gallery-stage">
        <img v-if="activeImage" :src="activeImage" :alt="title || '商品图片'" class="stage-image">
        <div v-else class="gallery-placeholder">
          <p>暂未上传更多实拍图</p>
          <strong>{{ title || '待展示商品' }}</strong>
        </div>
      </div>
    </div>

    <div class="thumb-strip" :class="{ empty: !normalizedImages.length }">
      <button
        v-for="(image, index) in normalizedImages"
        :key="`${image}-${index}`"
        type="button"
        class="thumb"
        :class="{ active: index === currentIndex }"
        @click="$emit('update:currentIndex', index)"
      >
        <img :src="image" :alt="`${title || '商品'}缩略图${index + 1}`">
      </button>
      <div v-if="!normalizedImages.length" class="thumb-placeholder">卖家还没有上传更多图片</div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
  title: { type: String, default: '' },
  category: { type: String, default: '' }
})

defineEmits(['update:currentIndex'])

const normalizedImages = computed(() => props.images.filter(Boolean))
const activeImage = computed(() => normalizedImages.value[props.currentIndex] || normalizedImages.value[0] || '')
</script>

<style scoped>
.gallery-shell {
  display: grid;
  gap: 16px;
}

.stage-wrap {
  position: relative;
}

.stage-meta {
  position: absolute;
  z-index: 1;
  left: 20px;
  right: 20px;
  top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.stage-kicker,
.stage-count {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 252, 247, 0.84);
  backdrop-filter: blur(12px);
  font-size: 0.78rem;
  font-weight: 800;
}

.stage-kicker {
  color: var(--muted-strong);
}

.stage-count {
  color: var(--text);
}

.gallery-stage {
  min-height: 620px;
  overflow: hidden;
  border-radius: 34px;
  padding: 36px;
  background: linear-gradient(180deg, #efe7dc 0%, #e5dacb 100%);
  box-shadow: 0 28px 60px rgba(37, 26, 17, 0.12);
}

.stage-image {
  width: 100%;
  min-height: 548px;
  height: 100%;
  object-fit: contain;
  display: block;
}

.gallery-placeholder {
  min-height: 548px;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 40px;
  background:
    radial-gradient(circle at top left, rgba(35, 68, 93, 0.12), transparent 24%),
    radial-gradient(circle at bottom right, rgba(49, 95, 84, 0.12), transparent 24%),
    linear-gradient(180deg, #f5efe6 0%, #ece3d6 100%);
}

.gallery-placeholder p {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 0.92rem;
}

.gallery-placeholder strong {
  max-width: 12ch;
  font-size: 2.2rem;
  line-height: 1.08;
  letter-spacing: -0.04em;
}

.thumb-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.thumb-strip.empty {
  grid-template-columns: 1fr;
}

.thumb,
.thumb-placeholder {
  min-height: 108px;
  overflow: hidden;
  border: 0;
  border-radius: 20px;
  background: var(--surface-strong);
  box-shadow: inset 0 0 0 1px rgba(73, 57, 41, 0.08);
}

.thumb {
  padding: 0;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.thumb:hover {
  transform: translateY(-2px);
}

.thumb img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.thumb.active {
  box-shadow: inset 0 0 0 2px rgba(35, 68, 93, 0.3), 0 12px 24px rgba(37, 26, 17, 0.1);
}

.thumb-placeholder {
  display: grid;
  place-items: center;
  padding: 0 18px;
  color: var(--muted);
  font-size: 0.9rem;
}

@media (max-width: 960px) {
  .gallery-stage,
  .stage-image,
  .gallery-placeholder {
    min-height: 360px;
  }

  .thumb-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
