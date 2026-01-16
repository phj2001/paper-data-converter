<template>
  <div class="column-config">
    <div class="card">
      <h2 class="card-title">配置表格列结构</h2>
      <p class="card-description">
        设置表格的列数和列标题，所有图片将使用统一的列格式
      </p>

      <!-- 列数设置 -->
      <div class="form-group">
        <label class="form-label">
          列数
          <span class="form-hint">（1-20列）</span>
        </label>
        <input
          v-model.number="columnCount"
          type="number"
          min="1"
          max="20"
          class="input"
          :disabled="useSuggested"
          placeholder="请输入列数"
          @input="updateHeaders"
        />
      </div>

      <!-- 列标题设置 -->
      <div v-if="suggestedHeaders.length" class="trial-toggle">
        <label class="checkbox-label">
          <input type="checkbox" v-model="useSuggested" />
          <span>使用试运行表头与提示词</span>
        </label>
        <p class="trial-hint">启用后将锁定列配置，并自动使用试运行生成的提示词。</p>
      </div>

      <div v-if="columnCount > 0" class="form-group">
        <label class="form-label">列标题</label>
        <div class="headers-grid">
          <div
            v-for="(header, index) in headers"
            :key="index"
            class="header-item"
          >
            <span class="header-label">第 {{ index + 1 }} 列</span>
            <input
              v-model="headers[index]"
              type="text"
              class="input"
              :disabled="useSuggested"
              :placeholder="`列${index + 1}标题`"
            />
          </div>
        </div>
      </div>

      <!-- 预览 -->
      <div v-if="columnCount > 0 && headers.some(h => h)" class="preview-section">
        <h3 class="preview-title">预览</h3>
        <div class="preview-table">
          <div class="preview-row preview-header">
            <div
              v-for="(header, index) in headers"
              :key="index"
              class="preview-cell"
            >
              {{ header || `列${index + 1}` }}
            </div>
          </div>
          <div class="preview-row">
            <div
              v-for="(header, index) in headers"
              :key="index"
              class="preview-cell preview-cell-data"
            >
              数据示例
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button class="btn btn-secondary" @click="$emit('back')">
          返回
        </button>
        <button
          class="btn btn-primary"
          :disabled="!isValid || isProcessing"
          @click="handleConfigure"
        >
          <span v-if="isProcessing" class="spinner"></span>
          <span v-else>开始处理</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  isProcessing: {
    type: Boolean,
    default: false
  },
  suggestedHeaders: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['configure', 'back'])

const columnCount = ref(4)
const headers = ref(['序号', '品名', '数量', '单位'])
const useSuggested = ref(false)

// 更新列标题数组
const updateHeaders = () => {
  if (useSuggested.value) return
  const count = Math.max(1, Math.min(20, columnCount.value || 1))
  const current = headers.value.length

  if (count > current) {
    for (let i = current; i < count; i++) {
      headers.value.push(`列${i + 1}`)
    }
  } else if (count < current) {
    headers.value = headers.value.slice(0, count)
  }
}

// 验证配置是否有效
const isValid = computed(() => {
  return (
    columnCount.value >= 1 &&
    columnCount.value <= 20 &&
    headers.value.length === columnCount.value &&
    headers.value.every(h => h && h.trim().length > 0)
  )
})

// 处理配置
const handleConfigure = () => {
  if (!isValid.value) return
  emit('configure', {
    headers: headers.value.map(h => h.trim()),
    useTrialProfile: useSuggested.value
  })
}

// 监听列数变化
watch(columnCount, updateHeaders)

const applySuggestedHeaders = () => {
  if (!props.suggestedHeaders.length) return
  columnCount.value = props.suggestedHeaders.length
  headers.value = [...props.suggestedHeaders]
}

watch(() => props.suggestedHeaders, (newHeaders) => {
  if (newHeaders && newHeaders.length) {
    useSuggested.value = true
    applySuggestedHeaders()
  }
})

watch(useSuggested, (enabled) => {
  if (enabled) {
    applySuggestedHeaders()
  }
})

// 初始化
updateHeaders()
</script>

<style scoped>
.column-config {
  max-width: 700px;
  margin: 0 auto;
}

.card-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.card-description {
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: 32px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-size: 15px;
}

.form-hint {
  color: var(--text-tertiary);
  font-weight: 400;
  font-size: 14px;
}

.headers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}

.header-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.preview-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.trial-toggle {
  margin-bottom: 20px;
  padding: 12px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
}

.trial-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.preview-table {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: white;
}

.preview-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  border-bottom: 1px solid var(--border-color);
}

.preview-row:last-child {
  border-bottom: none;
}

.preview-header {
  background: var(--bg-secondary);
}

.preview-cell {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  align-items: center;
}

.preview-cell:last-child {
  border-right: none;
}

.preview-cell-data {
  font-weight: 400;
  color: var(--text-tertiary);
}

.actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .headers-grid {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  }
}
</style>
