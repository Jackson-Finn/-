export function formatDateTime(value, options = {}) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString(
    'zh-CN',
    options.withTime
      ? { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }
      : { year: 'numeric', month: '2-digit', day: '2-digit' }
  )
}

export function formatShortDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

export function formatPrice(value) {
  return `¥ ${Number(value || 0).toFixed(2)}`
}

export function buildProductCode(product) {
  return `AM-${String(product?.id || 0).padStart(5, '0')}`
}

export function getStatusMeta(product) {
  const audit = (product?.audit_status || '').toString()
  const status = (product?.product_status || '').toString()

  if (audit === 'APPROVED' && status === 'ACTIVE') {
    return {
      label: '在售中',
      tone: 'positive',
      summary: '平台审核通过，可继续沟通并下单。'
    }
  }

  const mapping = {
    PENDING: { label: '审核中', tone: 'warning', summary: '平台正在核对图片、描述和价格信息。' },
    CHANGES_REQUESTED: { label: '待补充资料', tone: 'warning', summary: '卖家需要补充更多细节后再开放交易。' },
    REJECTED: { label: '未通过审核', tone: 'danger', summary: '当前不支持继续交易。' },
    OFF_SHELF: { label: '已下架', tone: 'muted', summary: '商品已结束公开出售。' },
    BLOCKED: { label: '已拦截', tone: 'danger', summary: '平台已拦截该商品，暂不支持浏览交易。' },
    NEEDS_REVISION: { label: '待修改', tone: 'warning', summary: '信息仍需补充，建议稍后再看。' },
    DRAFT: { label: '草稿中', tone: 'muted', summary: '卖家仍在整理信息。' }
  }

  return mapping[audit] || mapping[status] || {
    label: status || audit || '状态待确认',
    tone: 'muted',
    summary: '当前状态待确认。'
  }
}

export function getRiskTone(level) {
  const normalized = (level || '').toLowerCase()
  if (normalized === 'high') return 'danger'
  if (normalized === 'medium') return 'warning'
  return 'safe'
}

export function sellerMetricItems(seller) {
  if (!seller) return []
  return [
    { label: '信用评分', value: `${seller.trust_score || 0} / 100` },
    { label: '历史交易', value: `${seller.completed_orders || 0} 笔` },
    { label: '在售商品', value: `${seller.active_products || 0} 件` },
    { label: '平均响应', value: `${seller.response_time_minutes || '-'} 分钟` }
  ]
}

export function normalizeDetailSections(product) {
  const sections = Array.isArray(product?.detail_sections) ? product.detail_sections : []
  if (sections.length) return sections
  return [{ title: '商品说明', body: product?.description || '卖家暂未补充更多说明。' }]
}

export function normalizeSpecs(product) {
  return Array.isArray(product?.specs) ? product.specs : []
}

export function normalizeDelivery(product) {
  return Array.isArray(product?.delivery_options) ? product.delivery_options : []
}

export function normalizeRiskFlags(product) {
  return Array.isArray(product?.risk_flags) ? product.risk_flags : []
}

export function productGalleryImages(product) {
  return Array.isArray(product?.images) ? product.images.filter(Boolean) : []
}
