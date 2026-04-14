<template>
  <div class="grid grid-2">
    <section class="panel" style="padding: 24px;">
      <div class="section-header">
        <div>
          <div class="pill">发布工作台</div>
          <h2 class="section-title">商品发布 + AI 辅助 + 媒体登记</h2>
        </div>
      </div>

      <el-form :model="form" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="form.price" :min="0" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="form.stock" :min="1" />
        </el-form-item>
        <el-space wrap>
          <el-button type="primary" @click="submitProduct">提交审核</el-button>
          <el-button @click="generateByAi">AI 生成文案</el-button>
          <el-button @click="runModeration">风险预审</el-button>
          <el-button @click="simulateUpload">模拟登记媒体</el-button>
        </el-space>
      </el-form>
    </section>

    <section class="grid">
      <div class="panel" style="padding: 24px;">
        <h3 class="section-title">AI 输出</h3>
        <pre class="code">{{ aiResult }}</pre>
      </div>
      <div class="panel" style="padding: 24px;">
        <h3 class="section-title">风险预审</h3>
        <pre class="code">{{ moderation }}</pre>
      </div>
      <div class="panel" style="padding: 24px;">
        <h3 class="section-title">媒体记录</h3>
        <pre class="code">{{ asset }}</pre>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { productApi } from '../../api/products'

const form = reactive({
  title: '',
  description: '',
  price: 199,
  stock: 1,
  category_id: null
})

const aiResult = ref({})
const moderation = ref({})
const asset = ref({})

async function submitProduct() {
  const product = await productApi.create(form)
  ElMessage.success(`商品已提交，ID ${product.id}`)
}

async function generateByAi() {
  aiResult.value = await productApi.aiDraft({
    keywords: ['二手', '高性价比', '保养好'],
    category: '数码'
  })
  form.title = aiResult.value.title || form.title
  form.description = aiResult.value.description || form.description
}

async function runModeration() {
  moderation.value = await productApi.aiModeration({
    title: form.title,
    description: form.description
  })
}

async function simulateUpload() {
  const init = await productApi.uploadInit({ filename: 'sample.jpg', mime_type: 'image/jpeg' })
  asset.value = await productApi.uploadComplete({ asset_id: init.id, width: 1200, height: 900 })
}
</script>

<style scoped>
.code {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: rgba(36, 92, 90, 0.08);
  overflow: auto;
}
</style>

