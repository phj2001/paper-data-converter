<template>
  <div class="file-upload">
    <div class="upload-layout">
      <div class="card">
        <h2 class="card-title">上传表格图片</h2>
        <p class="card-description">
          支持选择文件夹或多选图片文件，支持 JPG、PNG、BMP、WebP 格式
        </p>

        <!-- 拖拽上传区域 -->
        <div
          class="upload-area"
          :class="{ dragging: isDragging }"
          @click="selectFiles"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" class="upload-icon">
            <rect width="64" height="64" rx="16" fill="#EEF0F2"/>
            <path d="M32 24v16m-8-8l8-8 8 8" stroke="#0066FF" stroke-width="2.5" stroke-linecap="round"/>
            <rect x="20" y="44" width="24" height="4" rx="2" fill="#0066FF"/>
          </svg>

          <div class="upload-text">
            <p class="upload-title">点击或拖拽上传</p>
            <p class="upload-hint">支持选择文件夹上传多个图片</p>
          </div>

          <input
            ref="fileInputRef"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/bmp,image/webp"
            webkitdirectory
            @change="handleFileSelect"
            style="display: none"
          />
        </div>

        <!-- 文件列表 -->
        <div v-if="selectedFiles.length > 0" class="file-list">
          <div class="file-list-header">
            <span>已选择 {{ selectedFiles.length }} 个文件</span>
            <button class="btn-text" @click="clearFiles">清空</button>
          </div>

          <div class="file-list-items">
            <div v-for="file in selectedFiles.slice(0, 10)" :key="file.name" class="file-item">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect width="16" height="16" rx="4" fill="#EEF0F2"/>
                <path d="M4.5 11.5V4.5l3.5 3.5 3.5-3.5v7" stroke="#666" stroke-width="1" stroke-linecap="round"/>
              </svg>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatSize(file.size) }}</span>
            </div>

            <div v-if="selectedFiles.length > 10" class="file-item file-item-more">
              <span>还有 {{ selectedFiles.length - 10 }} 个文件...</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="actions">
          <button
            class="btn btn-primary"
            :disabled="selectedFiles.length === 0 || isUploading"
            @click="handleUpload"
          >
            <span v-if="isUploading" class="spinner"></span>
            <span v-else>继续</span>
          </button>
        </div>
      </div>

      <!-- 使用说明 -->
      <div class="card card-info">
        <h3>使用步骤</h3>
        <ul class="info-list">
          <li>先点击模型配置，选择自己要使用的大模型，并配置API Key</li>
          <li>再点击“试运行”，上传一张样本图，系统生成表头与提示词，确认格式与效果</li>
          <li>回到“上传表格图片”，选择文件夹或多张图片并上传</li>
          <li>配置列并开始处理，等待识别完成后下载 Excel</li>
          <li>拍照尽量对齐、清晰、光线均匀，效果更稳定</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  isUploading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['upload'])

const fileInputRef = ref(null)
const isDragging = ref(false)
const selectedFiles = ref([])

// 选择文件
const selectFiles = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || [])

  // 过滤图片文件
  const imageFiles = files.filter(file => file.type.startsWith('image/'))

  selectedFiles.value = imageFiles
}

// 处理拖拽
const handleDrop = (event) => {
  isDragging.value = false

  const files = Array.from(event.dataTransfer.files || [])

  // 过滤图片文件
  const imageFiles = files.filter(file => file.type.startsWith('image/'))

  selectedFiles.value = imageFiles
}

// 清空文件
const clearFiles = () => {
  selectedFiles.value = []
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 上传文件
const handleUpload = () => {
  if (selectedFiles.value.length === 0) return
  emit('upload', selectedFiles.value)
}
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.upload-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 0.9fr);
  gap: 24px;
  align-items: start;
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
  margin-bottom: 24px;
}

.upload-icon {
  margin-bottom: 16px;
}

.upload-text {
  margin-bottom: 8px;
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.upload-hint {
  color: var(--text-secondary);
  font-size: 14px;
}

.file-list {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}

.btn-text:hover {
  text-decoration: underline;
}

.file-list-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.file-item-more {
  justify-content: center;
  color: var(--text-tertiary);
}

.file-name {
  flex: 1;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: var(--text-tertiary);
  font-size: 12px;
}

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.card-info {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.05) 0%, rgba(0, 102, 255, 0.02) 100%);
}

.card-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.info-list {
  list-style: none;
}

.info-list li {
  position: relative;
  padding-left: 24px;
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.info-list li::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-color);
}

.info-list li:last-child {
  margin-bottom: 0;
}

@media (max-width: 900px) {
  .upload-layout {
    grid-template-columns: 1fr;
  }
}
</style>
