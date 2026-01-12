<template>
  <div class="process-progress">
    <div class="card">
      <!-- 处理状态 -->
      <div class="status-header">
        <div class="status-icon" :class="statusIconClass">
          <component :is="statusIcon" />
        </div>
        <div class="status-info">
          <h2 class="status-title">{{ statusTitle }}</h2>
          <p class="status-message">{{ taskStatus.message || '正在处理中...' }}</p>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-info">
          <span class="progress-label">处理进度</span>
          <span class="progress-value">{{ taskStatus.progress }}%</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-bar-fill"
            :style="{ width: taskStatus.progress + '%' }"
          ></div>
        </div>
      </div>

      <!-- 文件信息 -->
      <div class="file-info">
        <div class="info-row">
          <span class="info-label">总文件数</span>
          <span class="info-value">{{ taskStatus.totalFiles }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">已处理</span>
          <span class="info-value">{{ taskStatus.processedFiles }}/{{ taskStatus.totalFiles }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">成功</span>
          <span class="info-value success">{{ taskStatus.successCount }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">失败</span>
          <span class="info-value error">{{ taskStatus.failCount }}</span>
        </div>
      </div>

      <!-- 成功率 -->
      <div class="success-rate-section">
        <div class="rate-info">
          <span class="rate-label">当前成功率</span>
          <span class="rate-value" :class="rateClass">{{ successRate }}%</span>
        </div>
        <div class="rate-bar">
          <div
            class="rate-bar-fill"
            :class="rateClass"
            :style="{ width: successRate + '%' }"
          ></div>
        </div>
      </div>

      <!-- 当前处理文件 -->
      <div v-if="taskStatus.currentFile && taskStatus.status === 'processing'" class="current-file">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect width="16" height="16" rx="4" fill="#EEF0F2"/>
          <path d="M4.5 11.5V4.5l3.5 3.5 3.5-3.5v7" stroke="#666" stroke-width="1" stroke-linecap="round"/>
        </svg>
        <span class="current-file-text">正在处理：{{ taskStatus.currentFile }}</span>
        <span class="current-file-index">({{ taskStatus.processedFiles }}/{{ taskStatus.totalFiles }})</span>
      </div>
    </div>

    <!-- 提示信息 -->
    <div v-if="taskStatus.status === 'processing'" class="card card-tip">
      <p>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="9" stroke="#0066FF" stroke-width="1.5"/>
          <path d="M10 6v5m0 3v.5" stroke="#0066FF" stroke-width="2" stroke-linecap="round"/>
        </svg>
        正在调用OCR API识别表格，这可能需要几分钟时间，请耐心等待...
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'

const props = defineProps({
  taskStatus: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['complete'])

// 状态图标组件
const ProcessingIcon = () => h('svg', {
  width: '48',
  height: '48',
  viewBox: '0 0 48 48',
  fill: 'none'
}, [
  h('circle', {
    cx: '24',
    cy: '24',
    r: '20',
    stroke: '#0066FF',
    'stroke-width': '2.5',
    fill: 'none'
  }),
  h('path', {
    d: 'M24 14v10l6 4',
    stroke: '#0066FF',
    'stroke-width': '2.5',
    'stroke-linecap': 'round'
  })
])

const CompletedIcon = () => h('svg', {
  width: '48',
  height: '48',
  viewBox: '0 0 48 48',
  fill: 'none'
}, [
  h('circle', {
    cx: '24',
    cy: '24',
    r: '20',
    fill: '#00C853'
  }),
  h('path', {
    d: 'M15 24l6 6 12-12',
    stroke: 'white',
    'stroke-width': '3',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round'
  })
])

const FailedIcon = () => h('svg', {
  width: '48',
  height: '48',
  viewBox: '0 0 48 48',
  fill: 'none'
}, [
  h('circle', {
    cx: '24',
    cy: '24',
    r: '20',
    fill: '#FF5252'
  }),
  h('path', {
    d: 'M15 15l18 18M33 15l-18 18',
    stroke: 'white',
    'stroke-width': '3',
    'stroke-linecap': 'round'
  })
])

// 状态图标
const statusIcon = computed(() => {
  switch (props.taskStatus.status) {
    case 'processing':
      return ProcessingIcon
    case 'completed':
      return CompletedIcon
    case 'failed':
      return FailedIcon
    default:
      return ProcessingIcon
  }
})

const statusIconClass = computed(() => {
  switch (props.taskStatus.status) {
    case 'processing':
      return 'processing'
    case 'completed':
      return 'completed'
    case 'failed':
      return 'failed'
    default:
      return 'processing'
  }
})

const statusTitle = computed(() => {
  switch (props.taskStatus.status) {
    case 'processing':
      return '正在处理...'
    case 'completed':
      return '处理完成'
    case 'failed':
      return '处理失败'
    default:
      return '处理中'
  }
})

// 计算成功率
const successRate = computed(() => {
  const processed = props.taskStatus.processedFiles || 0
  if (processed === 0) return 0
  return Math.round((props.taskStatus.successCount / processed) * 100)
})

// 成功率颜色类
const rateClass = computed(() => {
  if (successRate.value >= 80) return 'rate-high'
  if (successRate.value >= 50) return 'rate-medium'
  return 'rate-low'
})
</script>

<style scoped>
.process-progress {
  max-width: 600px;
  margin: 0 auto;
}

.status-header {
  display: flex;
  gap: 20px;
  margin-bottom: 32px;
}

.status-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon.processing {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.status-info {
  flex: 1;
}

.status-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.status-message {
  color: var(--text-secondary);
  font-size: 15px;
}

.progress-section {
  margin-bottom: 32px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
}

.file-info {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-value.success {
  color: var(--success-color);
}

.info-value.error {
  color: var(--error-color);
}

.current-file {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.08) 0%, rgba(0, 102, 255, 0.03) 100%);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  border-left: 3px solid var(--primary-color);
}

.current-file-text {
  flex: 1;
  font-weight: 500;
}

.current-file-index {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(0, 102, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.success-rate-section {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.rate-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.rate-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.rate-value {
  font-size: 16px;
  font-weight: 700;
}

.rate-value.rate-high {
  color: var(--success-color);
}

.rate-value.rate-medium {
  color: #FFA726;
}

.rate-value.rate-low {
  color: var(--error-color);
}

.rate-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.rate-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease, background-color 0.3s ease;
}

.rate-bar-fill.rate-high {
  background: linear-gradient(90deg, #00C853 0%, #69F0AE 100%);
}

.rate-bar-fill.rate-medium {
  background: linear-gradient(90deg, #FFA726 0%, #FFD54F 100%);
}

.rate-bar-fill.rate-low {
  background: linear-gradient(90deg, #FF5252 0%, #FF8A80 100%);
}

.card-tip {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.05) 0%, rgba(0, 102, 255, 0.02) 100%);
}

.card-tip p {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .file-info {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
