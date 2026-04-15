<template>
  <div class="publish-page">
    <header class="panel publish-header">
      <div class="header-copy">
        <div class="eyebrow">Seller Workspace</div>
        <h2>{{ pageTitle }}</h2>
        <p>{{ pageDescription }}</p>
        <div class="header-statuses">
          <span class="header-status">{{ workspaceStatus }}</span>
          <span v-if="loadedAuditLabel" class="header-status muted">{{ loadedAuditLabel }}</span>
          <span v-if="isEditMode" class="header-status muted">商品 #{{ currentProductId }}</span>
        </div>
      </div>
      <div class="header-actions">
        <RouterLink to="/my-products">
          <el-button plain>我的商品</el-button>
        </RouterLink>
        <el-button :loading="aiLoading" @click="generateByAi">生成建议</el-button>
        <el-button plain :loading="moderationLoading" :disabled="!canRunModeration" @click="runModeration">检查内容</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitDisabled" @click="submitProduct">
          {{ submitButtonLabel }}
        </el-button>
      </div>
    </header>

    <el-alert
      v-if="pageError"
      :title="pageError"
      type="warning"
      show-icon
      :closable="false"
    />

    <div v-loading="pageLoading" class="publish-layout">
      <main class="editor-column">
        <section class="panel editor-surface">
          <div class="editor-head">
            <div>
              <div class="eyebrow">Editor</div>
              <h3 class="section-title">商品内容</h3>
              <p class="section-meta">先整理标题、描述和基础字段，再决定是否采用建议。</p>
            </div>
            <span class="editor-state">{{ completionText }}</span>
          </div>

          <div class="editor-canvas">
            <div class="title-editor">
              <label>标题</label>
              <input v-model="form.title" type="text" placeholder="例如：MacBook Air M2 95新，箱说齐全">
            </div>

            <div class="description-editor">
              <label>描述</label>
              <textarea
                v-model="form.description"
                rows="8"
                placeholder="补充成色、配件、使用情况、交易方式和验机说明。"
              />
            </div>

            <div class="field-grid">
              <div class="field-card">
                <span class="field-label">价格</span>
                <el-input-number v-model="form.price" :min="0" :step="10" />
              </div>
              <div class="field-card">
                <span class="field-label">库存</span>
                <el-input-number v-model="form.stock" :min="1" />
              </div>
              <div class="field-card">
                <span class="field-label">类目</span>
                <el-select v-model="form.category_id" placeholder="选择类目">
                  <el-option
                    v-for="option in categoryOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </div>
              <div class="field-card">
                <span class="field-label">成色</span>
                <div class="choice-row">
                  <button
                    v-for="item in conditionOptions"
                    :key="item"
                    type="button"
                    class="choice-chip"
                    :class="{ 'is-selected': condition === item }"
                    @click="condition = item"
                  >
                    {{ item }}
                  </button>
                </div>
              </div>
            </div>

            <div class="tag-editor">
              <div class="tag-head">
                <div>
                  <div class="section-title">卖点标签</div>
                  <p class="section-meta">保留 3 到 5 个短词，便于搜索、推荐和审核判断。</p>
                </div>
              </div>
              <div class="tag-input-row">
                <el-input
                  v-model="tagDraft"
                  placeholder="例如：支持验机、原装配件、同城自提"
                  @keyup.enter="addSellingPoint"
                />
                <el-button @click="addSellingPoint">添加</el-button>
              </div>
              <div class="tag-list">
                <button
                  v-for="item in sellingPoints"
                  :key="item"
                  type="button"
                  class="tag-chip"
                  @click="removeSellingPoint(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="panel media-surface">
          <div class="section-header">
            <div>
              <div class="eyebrow">Media</div>
              <h3 class="section-title">图片管理</h3>
              <p class="section-meta">
                {{ mediaHint }}
              </p>
            </div>
            <div class="media-actions">
              <input ref="fileInput" class="file-input" type="file" accept="image/*" multiple @change="handleFileSelection">
              <el-button @click="openFilePicker">选择图片</el-button>
              <el-button :loading="uploading" @click="uploadSelectedFiles">上传</el-button>
            </div>
          </div>

          <div v-if="selectedFiles.length" class="selected-files">
            <span class="selected-label">待上传</span>
            <div class="selected-list">
              <span
                v-for="file in selectedFiles"
                :key="`${file.name}-${file.size}`"
                class="selected-chip"
              >
                {{ file.name }}
              </span>
            </div>
          </div>

          <div class="asset-grid" :class="{ 'is-empty': !displayAssets.length }">
            <PublishAssetItem
              v-for="asset in orderedAssets"
              :key="asset.id"
              :asset="asset"
              :is-cover="asset.id === activeCoverKey"
              :can-make-cover="canChangeCoverFor(asset)"
              :can-remove="canRemoveAsset(asset)"
              @make-cover="setCover"
              @remove="removeAsset"
            />
            <div v-if="!displayAssets.length" class="asset-empty">
              <strong>还没有图片</strong>
              <p>至少上传一张清晰图片，详情页和推荐卡片才会更可信。</p>
            </div>
          </div>
        </section>
      </main>

      <aside class="inspector-column">
        <PublishStageRail
          :steps="workflowSteps"
          :current-step="currentStep"
          :completed-steps="completedSteps"
          :status-label="workspaceStatus"
        />

        <PublishPreviewCard
          :product="form"
          :cover-image="previewCoverImage"
          :selling-points="sellingPoints"
          :condition-label="condition"
          :category-label="activeCategoryLabel"
          :asset-count="displayAssets.length"
        />

        <PublishSuggestionPanel
          :ai-result="aiResult"
          :moderation="moderation"
          :can-moderate="canRunModeration"
          @generate="generateByAi"
          @moderate="runModeration"
        />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import PublishAssetItem from '../../components/publish/PublishAssetItem.vue'
import PublishPreviewCard from '../../components/publish/PublishPreviewCard.vue'
import PublishStageRail from '../../components/publish/PublishStageRail.vue'
import PublishSuggestionPanel from '../../components/publish/PublishSuggestionPanel.vue'
import { productApi } from '../../api/products'

const categoryOptions = [
  { label: '数码', value: 1 },
  { label: '图书', value: 2 },
  { label: '家居', value: 3 },
  { label: '潮玩', value: 4 }
]

const conditionOptions = ['全新', '近新', '九成新', '正常使用']
const defaultSellingPoints = ['支持验机', '原装配件', '同城优先']

const route = useRoute()
const router = useRouter()

const form = reactive({
  title: '',
  description: '',
  price: 199,
  stock: 1,
  category_id: 1
})

const aiResult = ref({})
const moderation = ref({})
const selectedFiles = ref([])
const uploadedAssets = ref([])
const existingImages = ref([])
const uploading = ref(false)
const submitting = ref(false)
const aiLoading = ref(false)
const moderationLoading = ref(false)
const pageLoading = ref(false)
const pageError = ref('')
const fileInput = ref(null)
const tagDraft = ref('')
const coverAssetKey = ref(null)
const condition = ref('九成新')
const sellingPoints = ref([...defaultSellingPoints])
const loadedProduct = ref(null)
let loadSequence = 0

const currentProductId = computed(() => {
  const raw = Array.isArray(route.query.productId) ? route.query.productId[0] : route.query.productId
  const value = Number(raw)
  return Number.isFinite(value) && value > 0 ? value : null
})

const isEditMode = computed(() => Boolean(currentProductId.value))
const isResubmitMode = computed(() => route.query.mode === 'resubmit')
const canResubmitCurrent = computed(() => loadedProduct.value?.audit_status === 'CHANGES_REQUESTED')
const canRunModeration = computed(() => Boolean(form.title.trim() || form.description.trim()))

const activeCategoryLabel = computed(() => categoryOptions.find((item) => item.value === form.category_id)?.label || '')

const displayAssets = computed(() => {
  const persisted = existingImages.value.map((url, index) => ({
    id: `existing-${index}`,
    url,
    metadata: {
      stage: 'synced',
      original_filename: `已关联图片 ${index + 1}`
    }
  }))
  return [...persisted, ...uploadedAssets.value]
})

const canSelectCover = computed(() => !isEditMode.value || !existingImages.value.length)

const orderedAssets = computed(() => {
  if (!coverAssetKey.value || !canSelectCover.value) {
    return displayAssets.value
  }
  return [...displayAssets.value].sort((a, b) => (a.id === coverAssetKey.value ? -1 : b.id === coverAssetKey.value ? 1 : 0))
})

const activeCoverKey = computed(() => {
  if (canSelectCover.value) {
    return coverAssetKey.value || orderedAssets.value[0]?.id || null
  }
  return existingImages.value.length ? 'existing-0' : orderedAssets.value[0]?.id || null
})

const previewCoverImage = computed(() => {
  if (!orderedAssets.value.length) return ''
  const activeAsset = orderedAssets.value.find((item) => item.id === activeCoverKey.value) || orderedAssets.value[0]
  return activeAsset?.metadata?.variants?.preview || activeAsset?.url || ''
})

const isBaseInfoReady = computed(() => Boolean(form.title.trim() && form.description.trim() && form.price >= 0))
const hasAnyMedia = computed(() => displayAssets.value.length > 0)
const isAiReady = computed(() => Boolean(aiResult.value?.title || aiResult.value?.description))
const isReadyToSubmit = computed(() => isBaseInfoReady.value && hasAnyMedia.value)

const workflowSteps = [
  { key: 'content', label: '填写信息', meta: '整理标题、描述和基础字段' },
  { key: 'assist', label: '生成建议', meta: '根据卖点生成草稿与检查结果' },
  { key: 'media', label: '上传图片', meta: '补充商品图片，确认媒体已就绪' },
  { key: 'submit', label: '提交审核', meta: '保存修改并进入审核流程' }
]

const completedSteps = computed(() => {
  const steps = []
  if (isBaseInfoReady.value) steps.push('content')
  if (isAiReady.value || loadedProduct.value) steps.push('assist')
  if (hasAnyMedia.value) steps.push('media')
  if (isReadyToSubmit.value) steps.push('submit')
  return steps
})

const currentStep = computed(() => {
  if (!isBaseInfoReady.value) return 'content'
  if (!isAiReady.value && !loadedProduct.value) return 'assist'
  if (!hasAnyMedia.value) return 'media'
  return 'submit'
})

const pageTitle = computed(() => {
  if (isResubmitMode.value) return '修改后重新提交'
  if (isEditMode.value) return '编辑商品'
  return '发布商品'
})

const pageDescription = computed(() => {
  if (isResubmitMode.value) return '按审核意见补充内容，保存后重新进入待审队列。'
  if (isEditMode.value) return '继续完善商品信息，更新图片与卖点，再决定是否重新提交。'
  return '填写信息、整理图片并生成建议，再提交审核。'
})

const submitButtonLabel = computed(() => {
  if (isResubmitMode.value && canResubmitCurrent.value) return '保存并重新提交'
  if (isEditMode.value) return '保存修改'
  return '提交审核'
})

const submitDisabled = computed(() => pageLoading.value || submitting.value || !isReadyToSubmit.value)

const workspaceStatus = computed(() => {
  if (isResubmitMode.value && canResubmitCurrent.value) return '待重新提交'
  if (isReadyToSubmit.value) return isEditMode.value ? '可保存' : '可提交'
  if (hasAnyMedia.value) return '待提交'
  if (isBaseInfoReady.value) return '编辑中'
  return '起稿中'
})

const loadedAuditLabel = computed(() => {
  if (!loadedProduct.value?.audit_status) return ''
  const mapping = {
    PENDING: '当前状态：待审',
    APPROVED: '当前状态：已通过',
    REJECTED: '当前状态：已驳回',
    CHANGES_REQUESTED: '当前状态：待修改'
  }
  return mapping[loadedProduct.value.audit_status] || loadedProduct.value.audit_status
})

const completionText = computed(() => {
  if (isReadyToSubmit.value) return isResubmitMode.value ? '可重新提交' : '信息完整'
  if (isBaseInfoReady.value) return '继续补充图片'
  return '继续填写'
})

const mediaHint = computed(() => {
  if (isEditMode.value && existingImages.value.length) {
    return '已有图片会保留原排序，新上传图片会追加到当前商品中。'
  }
  return '先上传，再选择封面，发布页和推荐卡片会优先使用封面图。'
})

watch(
  () => currentProductId.value,
  (productId) => {
    if (!productId) {
      pageError.value = ''
      resetWorkspace()
      return
    }
    loadEditorProduct(productId)
  },
  { immediate: true }
)

function resetWorkspace() {
  form.title = ''
  form.description = ''
  form.price = 199
  form.stock = 1
  form.category_id = 1
  aiResult.value = {}
  moderation.value = {}
  selectedFiles.value = []
  uploadedAssets.value = []
  existingImages.value = []
  coverAssetKey.value = null
  condition.value = '九成新'
  sellingPoints.value = [...defaultSellingPoints]
  loadedProduct.value = null
}

async function loadEditorProduct(productId) {
  const sequence = ++loadSequence
  pageLoading.value = true
  pageError.value = ''
  try {
    const detail = await productApi.detail(productId)
    if (sequence !== loadSequence) return
    loadedProduct.value = detail
    form.title = detail.title || ''
    form.description = detail.description || ''
    form.price = detail.price ?? 199
    form.stock = detail.stock ?? 1
    form.category_id = detail.category_id || 1
    existingImages.value = detail.images || []
    uploadedAssets.value = []
    selectedFiles.value = []
    aiResult.value = {}
    moderation.value = {}
    condition.value = detail.tags?.condition || '九成新'
    sellingPoints.value = Array.isArray(detail.tags?.keywords) && detail.tags.keywords.length
      ? detail.tags.keywords.slice(0, 6).map((item) => String(item))
      : [...defaultSellingPoints]
    coverAssetKey.value = existingImages.value.length ? 'existing-0' : null
  } catch (error) {
    if (sequence !== loadSequence) return
    pageError.value = error.message
    resetWorkspace()
  } finally {
    if (sequence === loadSequence) {
      pageLoading.value = false
    }
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileSelection(event) {
  selectedFiles.value = Array.from(event.target.files || [])
}

function addSellingPoint() {
  const value = tagDraft.value.trim()
  if (!value || sellingPoints.value.includes(value)) {
    tagDraft.value = ''
    return
  }
  sellingPoints.value = [...sellingPoints.value, value].slice(0, 6)
  tagDraft.value = ''
}

function removeSellingPoint(value) {
  sellingPoints.value = sellingPoints.value.filter((item) => item !== value)
}

function canChangeCoverFor(asset) {
  return canSelectCover.value && typeof asset.id === 'number'
}

function canRemoveAsset(asset) {
  return typeof asset.id === 'number'
}

function setCover(assetId) {
  if (!canSelectCover.value) {
    ElMessage.info('编辑已有商品时会保留原封面排序，新图会追加在后。')
    return
  }
  coverAssetKey.value = assetId
}

function removeAsset(assetId) {
  uploadedAssets.value = uploadedAssets.value.filter((item) => item.id !== assetId)
  if (coverAssetKey.value === assetId) {
    coverAssetKey.value = uploadedAssets.value[0]?.id || null
  }
}

function buildPayload() {
  const orderedNumericAssets = orderedAssets.value
    .filter((item) => typeof item.id === 'number')
    .map((item) => item.id)

  return {
    ...form,
    asset_ids: orderedNumericAssets,
    tags: {
      source: 'manual',
      condition: condition.value,
      keywords: sellingPoints.value
    }
  }
}

async function submitProduct() {
  if (!isBaseInfoReady.value) {
    ElMessage.warning('请先补全标题、描述和基础信息')
    return
  }
  if (!hasAnyMedia.value) {
    ElMessage.warning('请至少上传一张商品图片')
    return
  }

  submitting.value = true
  try {
    const payload = buildPayload()
    if (!isEditMode.value) {
      const product = await productApi.create(payload)
      ElMessage.success(`商品已提交审核，ID ${product.id}`)
    } else {
      const updated = await productApi.update(currentProductId.value, payload)
      loadedProduct.value = updated
      if (isResubmitMode.value && canResubmitCurrent.value) {
        const resubmitted = await productApi.resubmit(currentProductId.value)
        loadedProduct.value = resubmitted
        ElMessage.success('商品已重新提交审核')
      } else {
        ElMessage.success('商品修改已保存')
      }
    }
    await router.push('/my-products')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

async function generateByAi() {
  aiLoading.value = true
  try {
    aiResult.value = await productApi.aiDraft({
      keywords: sellingPoints.value.length ? sellingPoints.value : ['二手', '高性价比', '保养好'],
      category: activeCategoryLabel.value || '数码'
    })
    form.title = aiResult.value.title || form.title
    form.description = aiResult.value.description || form.description
    ElMessage.success('已生成建议草稿')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    aiLoading.value = false
  }
}

async function runModeration() {
  moderationLoading.value = true
  try {
    moderation.value = await productApi.aiModeration({
      title: form.title,
      description: form.description
    })
    ElMessage.success('已完成内容检查')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    moderationLoading.value = false
  }
}

async function uploadSelectedFiles() {
  if (!selectedFiles.value.length) {
    ElMessage.warning('请先选择至少一张图片')
    return
  }

  uploading.value = true
  try {
    const assets = []
    for (const file of selectedFiles.value) {
      const init = await productApi.uploadInit({ filename: file.name, mime_type: file.type || 'application/octet-stream' })
      await productApi.uploadFile(init.id, file)
      const complete = await productApi.uploadComplete({ asset_id: init.id })
      assets.push({
        id: complete.id,
        url: complete.url,
        metadata: complete.metadata || {}
      })
    }
    uploadedAssets.value = [...uploadedAssets.value, ...assets]
    if (!coverAssetKey.value && canSelectCover.value && assets[0]) {
      coverAssetKey.value = assets[0].id
    }
    selectedFiles.value = []
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    ElMessage.success(`已上传 ${assets.length} 张图片`)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.publish-page {
  display: grid;
  gap: 18px;
}

.publish-header {
  padding: 18px 22px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.header-copy h2 {
  margin: 0 0 4px;
  font-size: 1.46rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.header-copy p {
  margin: 0;
  color: var(--muted);
  font-size: 0.92rem;
}

.header-statuses {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-status,
.editor-state {
  padding: 7px 11px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.92);
  color: var(--text);
  font-size: 0.78rem;
  font-weight: 700;
}

.header-status.muted {
  color: var(--muted);
}

.publish-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.48fr) minmax(340px, 0.82fr);
  gap: 18px;
  align-items: start;
}

.editor-column,
.inspector-column {
  display: grid;
  gap: 18px;
}

.editor-surface,
.media-surface {
  padding: 22px;
}

.editor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.editor-canvas {
  display: grid;
  gap: 18px;
}

.title-editor,
.description-editor {
  display: grid;
  gap: 8px;
}

.title-editor label,
.description-editor label,
.field-label {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.title-editor input,
.description-editor textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fbfdff;
  color: var(--text);
  font: inherit;
  resize: vertical;
}

.title-editor input {
  min-height: 66px;
  padding: 16px 18px;
  font-size: 1.18rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.description-editor textarea {
  min-height: 180px;
  padding: 16px 18px;
  line-height: 1.75;
}

.title-editor input:focus,
.description-editor textarea:focus {
  outline: none;
  border-color: rgba(37, 86, 216, 0.28);
  box-shadow: 0 0 0 4px rgba(37, 86, 216, 0.08);
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-card {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fbfdff;
  display: grid;
  gap: 10px;
}

.choice-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.choice-chip {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: white;
  color: var(--muted);
  font-weight: 600;
  cursor: pointer;
}

.choice-chip.is-selected {
  border-color: rgba(37, 86, 216, 0.2);
  background: var(--brand-soft);
  color: var(--brand-strong);
}

.tag-editor {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: #fbfdff;
  display: grid;
  gap: 12px;
}

.tag-input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  padding: 7px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: white;
  color: var(--text);
  cursor: pointer;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 700;
  line-height: 1.35;
}

.section-meta {
  margin: 4px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.media-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-input {
  display: none;
}

.selected-files {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.selected-label {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-chip {
  padding: 7px 10px;
  border-radius: 999px;
  background: #f4f7fb;
  color: var(--muted);
  font-size: 0.8rem;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
}

.asset-grid.is-empty {
  grid-template-columns: 1fr;
}

.asset-empty {
  min-height: 168px;
  border: 1px dashed var(--line);
  border-radius: 18px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--muted);
  padding: 18px;
}

.asset-empty strong {
  display: block;
  color: var(--text);
  margin-bottom: 6px;
}

@media (max-width: 1080px) {
  .publish-header {
    flex-direction: column;
  }

  .publish-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .field-grid,
  .tag-input-row {
    grid-template-columns: 1fr;
  }
}
</style>
