<template>
  <section class="panel gallery-card">
    <div class="section-header">
      <div>
        <div class="eyebrow">Media</div>
        <h3 class="section-title">商品图片</h3>
      </div>
    </div>

    <div v-if="images.length" class="gallery">
      <img class="cover" :src="activeImage" :alt="title || '商品图片'">
      <div class="thumbs">
        <button
          v-for="image in images"
          :key="image"
          type="button"
          class="thumb-button"
          :class="{ 'is-active': image === activeImage }"
          @click="$emit('select', image)"
        >
          <img :src="image" :alt="title || '商品缩略图'">
        </button>
      </div>
    </div>

    <div v-else class="gallery-empty">暂无图片</div>
  </section>
</template>

<script setup>
defineProps({
  images: {
    type: Array,
    default: () => []
  },
  activeImage: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  }
})

defineEmits(['select'])
</script>

<style scoped>
.gallery-card {
  padding: 18px;
}

.gallery {
  display: grid;
  gap: 12px;
}

.cover {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 18px;
  border: 1px solid var(--line);
  background: #eef4fb;
}

.thumbs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 10px;
}

.thumb-button {
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: white;
  cursor: pointer;
}

.thumb-button.is-active {
  border-color: rgba(37, 86, 216, 0.26);
  box-shadow: 0 0 0 2px rgba(37, 86, 216, 0.1);
}

.thumb-button img {
  width: 100%;
  height: 86px;
  object-fit: cover;
  display: block;
}

.gallery-empty {
  padding: 28px;
  border-radius: 16px;
  border: 1px dashed var(--line-strong);
  background: #fbfdff;
  color: var(--muted);
  text-align: center;
}
</style>
