<template>
  <div class="trial-run" @click.self="$emit('close')">
    <div class="trial-card">
      <div class="trial-header">
        <div class="trial-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <h2>试运行</h2>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="trial-body">
        <div v-if="!result" class="trial-upload">
          <p class="trial-desc">上传一张样本图片，系统将根据图片自动生成最佳提示词，并展示试运行结果。</p>
          <div class="upload-box" @click="selectFile">
            <input ref="fileInputRef" type="file" accept="image/*" @change="handleFileSelect" />
            <div v-if="!selectedFile" class="upload-placeholder">
              <span>点击选择图片</span>
              <small>仅支持单张图片</small>
            </div>
            <div v-else class="upload-selected">
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
            </div>
          </div>

          <div class="trial-actions">
            <button class="btn btn-primary" :disabled="!selectedFile || isRunning" @click="startTrial">
              <span v-if="isRunning" class="spinner"></span>
              <span v-if="isRunning">运行中</span>
              <span v-else>开始试运行</span>
            </button>
          </div>
          <p v-if="isRunning" class="run-status">
            <span class="run-dot"></span>
            <span>{{ statusMessage }}</span>
            <span class="run-time">已运行 {{ elapsedSeconds }}s</span>
          </p>
          <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
        </div>

        <div v-else class="trial-result">
          <div class="result-summary">
            <div class="summary-item">
              <span class="label">列数</span>
              <span class="value">{{ result.column_count }}</span>
            </div>
            <div class="summary-item">
              <span class="label">数据行</span>
              <span class="value">{{ result.total_rows }}</span>
            </div>
            <div class="summary-item">
              <span class="label">轮次</span>
              <span class="value">{{ runCount }}</span>
            </div>
          </div>

          <div class="preview-table">
            <div class="preview-row preview-header">
              <div v-for="(header, index) in result.headers" :key="index" class="preview-cell">
                {{ header }}
              </div>
            </div>
            <div v-for="(row, rowIndex) in result.rows" :key="rowIndex" class="preview-row">
              <div v-for="(cell, cellIndex) in row" :key="cellIndex" class="preview-cell">
                {{ cell }}
              </div>
            </div>
          </div>

          <div class="prompt-notes">
            <h3>提示词要点</h3>
            <ul>
              <li v-for="(note, index) in result.prompt_profile?.column_notes || []" :key="index">
                {{ note }}
              </li>
            </ul>
          </div>

          <div class="feedback-panel">
            <h3>反馈与优化</h3>
            <p class="feedback-hint">
              请使用自然语言描述你希望的表格结构，例如“应该有4列，列名为项目/数值1/数值2/备注，最后一列可为空”。
            </p>
            <textarea
              v-model="feedbackText"
              class="feedback-input"
              placeholder="请输入自然语言反馈..."
              rows="4"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="trial-footer" v-if="result">
        <button class="btn btn-primary" :disabled="isRunning || !feedbackText.trim()" @click="refineTrial">
          继续优化
        </button>
        <button class="btn btn-secondary" @click="resetTrial">重新试运行</button>
        <button class="btn btn-secondary" @click="downloadTrial">下载结果</button>
        <button class="btn btn-secondary" :disabled="isDefault" @click="setAsDefault">
          {{ isDefault ? '已设为默认' : '设为默认' }}
        </button>
        <button class="btn btn-primary" @click="applyProfile">使用此试运行配置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { runTrial, setDefaultProfile, getRuntimeLLMConfig } from '../api'

const emit = defineEmits(['close', 'apply'])

const fileInputRef = ref(null)
const selectedFile = ref(null)
const isRunning = ref(false)
const result = ref(null)
const feedbackText = ref('')
const runCount = ref(0)
const errorMessage = ref('')
const isDefault = ref(false)
const statusMessage = ref('')
const elapsedSeconds = ref(0)
const statusTimers = []
let elapsedTimer = null

const updateResult = (data, isFirst = false) => {
  result.value = data
  isDefault.value = false
  if (isFirst) {
    runCount.value = 1
  } else {
    runCount.value += 1
  }
}

const startStatusFlow = (initialMessage = '??????...') => {
  statusMessage.value = initialMessage
  elapsedSeconds.value = 0
  statusTimers.push(setTimeout(() => {
    statusMessage.value = '正在分析表格结构...'
  }, 1200))
  statusTimers.push(setTimeout(() => {
    statusMessage.value = '正在识别表格内容...'
  }, 4500))
  statusTimers.push(setTimeout(() => {
    statusMessage.value = '正在生成预览结果...'
  }, 9000))
  statusTimers.push(setTimeout(() => {
    statusMessage.value = '仍在处理中，请耐心等待...'
  }, 15000))
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value += 1
  }, 1000)
}

const stopStatusFlow = () => {
  while (statusTimers.length) {
    clearTimeout(statusTimers.pop())
  }
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
  statusMessage.value = ''
}

const selectFile = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  selectedFile.value = file || null
}

const startTrial = async () => {
  if (!selectedFile.value) return
  errorMessage.value = ''

  const llmConfig = getRuntimeLLMConfig()
  if (!llmConfig || !llmConfig.provider || !llmConfig.model || !llmConfig.api_key) {
    errorMessage.value = '请先在模型配置中填写 API Key'
    return
  }

  isRunning.value = true
  startStatusFlow()
  try {
    const data = await runTrial(selectedFile.value, llmConfig)
    updateResult(data, true)
    feedbackText.value = ''
  } catch (error) {
    errorMessage.value = error.message || '试运行失败'
  } finally {
    isRunning.value = false
    stopStatusFlow()
  }
}

const refineTrial = async () => {
  if (!selectedFile.value || !result.value?.profile_id) return
  const feedback = feedbackText.value.trim()
  if (!feedback) {
    errorMessage.value = '请输入反馈内容'
    return
  }

  errorMessage.value = ''
  const llmConfig = getRuntimeLLMConfig()
  if (!llmConfig || !llmConfig.provider || !llmConfig.model || !llmConfig.api_key) {
    errorMessage.value = '请先在模型配置中填写 API Key'
    return
  }

  isRunning.value = true
  startStatusFlow()
  try {
    const data = await runTrial(selectedFile.value, llmConfig, {
      feedback_text: feedback,
      base_profile_id: result.value.profile_id
    })
    updateResult(data)
    feedbackText.value = ''
  } catch (error) {
    errorMessage.value = error.message || '优化失败'
  } finally {
    isRunning.value = false
    stopStatusFlow()
  }
}

const resetTrial = () => {
  selectedFile.value = null
  result.value = null
  feedbackText.value = ''
  runCount.value = 0
  errorMessage.value = ''
  isDefault.value = false
  stopStatusFlow()
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const downloadTrial = () => {
  if (!result.value?.trial_id) return
  window.open(`/api/trial/download/${result.value.trial_id}`, '_blank')
}

const applyProfile = () => {
  if (!result.value?.profile_id) return
  emit('apply', {
    profile_id: result.value.profile_id,
    headers: result.value.headers
  })
}

const setAsDefault = async () => {
  if (!result.value?.profile_id) return
  try {
    await setDefaultProfile(result.value.profile_id)
    isDefault.value = true
  } catch (error) {
    errorMessage.value = error.message || '设置默认失败'
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.trial-run {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.trial-card {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 820px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.trial-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-color);
}

.trial-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trial-title h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.trial-body {
  padding: 22px;
  overflow-y: auto;
}

.trial-desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 16px;
}

.upload-box {
  border: 1.5px dashed var(--border-color);
  border-radius: 12px;
  padding: 20px;
  background: var(--bg-secondary);
  text-align: center;
  cursor: pointer;
}

.upload-box input {
  display: none;
}

.upload-placeholder span {
  display: block;
  font-weight: 600;
  color: var(--text-primary);
}

.upload-placeholder small {
  color: var(--text-tertiary);
}

.upload-selected {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-weight: 600;
  color: var(--text-primary);
}

.file-size {
  color: var(--text-tertiary);
  font-size: 12px;
}

.trial-actions {
  margin-top: 16px;
}

.run-status {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.run-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: pulse 1.2s ease-in-out infinite;
}

.run-time {
  color: var(--text-tertiary);
}

.error-text {
  margin-top: 12px;
  color: var(--error-color);
  font-size: 13px;
}

.result-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.summary-item {
  flex: 1;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 10px;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-item .value {
  font-size: 18px;
  font-weight: 600;
}

.preview-table {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
  background: white;
}

.preview-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  border-bottom: 1px solid var(--border-color);
}

.preview-row:last-child {
  border-bottom: none;
}

.preview-header {
  background: var(--bg-secondary);
  font-weight: 600;
}

.preview-cell {
  padding: 10px 12px;
  font-size: 13px;
  border-right: 1px solid var(--border-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-cell:last-child {
  border-right: none;
}

.prompt-notes {
  margin-top: 18px;
  padding: 12px;
  background: #f3f6fb;
  border-radius: 10px;
}

.prompt-notes h3 {
  font-size: 14px;
  margin-bottom: 8px;
}

.prompt-notes ul {
  list-style: none;
  padding-left: 0;
}

.prompt-notes li {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.feedback-panel {
  margin-top: 18px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 10px;
}

.feedback-panel h3 {
  font-size: 14px;
  margin-bottom: 6px;
}

.feedback-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  line-height: 1.5;
}

.feedback-input {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  resize: vertical;
  background: white;
}

.trial-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 22px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

@media (max-width: 768px) {
  .trial-footer {
    flex-direction: column;
  }
}

@keyframes pulse {
  0% {
    opacity: 0.4;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0.4;
    transform: scale(0.8);
  }
}
</style>
