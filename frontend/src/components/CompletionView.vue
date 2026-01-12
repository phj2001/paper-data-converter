<template>
  <div class="completion-view">
    <div class="card">
      <!-- 结果图标 -->
      <div class="result-icon" :class="resultClass">
        <component :is="resultIcon" />
      </div>

      <!-- 标题 -->
      <h2 class="result-title">{{ resultTitle }}</h2>
      <p class="result-message">{{ resultMessage }}</p>

      <!-- 统计信息 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon success">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ taskStatus.successCount }}</div>
            <div class="stat-label">成功</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon error">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ taskStatus.failCount }}</div>
            <div class="stat-label">失败</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon primary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ taskStatus.totalFiles }}</div>
            <div class="stat-label">总文件</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" :class="rateIconClass">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value" :class="rateValueClass">{{ successRate }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button class="btn btn-secondary" @click="$emit('reset')">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M1 8h16M9 1v16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          新建任务
        </button>

        <button
          v-if="taskStatus.status === 'completed'"
          class="btn btn-success"
          @click="$emit('download')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 12v-9M9 12l3-3M9 12l-3-3M2 14v2a2 2 0 002 2h10a2 2 0 002-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          下载 Excel
        </button>
      </div>
    </div>

    <!-- 详细说明 -->
    <div class="card card-details">
      <h3>处理详情</h3>
      <div class="details-list">
        <div class="detail-item">
          <span class="detail-label">任务状态</span>
          <span class="tag" :class="statusTagClass">{{ statusText }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">处理进度</span>
          <span class="detail-value">{{ taskStatus.progress }}%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">成功率</span>
          <span class="detail-value">{{ successRate }}%</span>
        </div>
      </div>
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

const emit = defineEmits(['reset', 'download'])

// 结果图标组件
const SuccessIcon = () => h('svg', {
  width: '64',
  height: '64',
  viewBox: '0 0 64 64',
  fill: 'none'
}, [
  h('circle', {
    cx: '32',
    cy: '32',
    r: '28',
    fill: '#E8F5E9'
  }),
  h('circle', {
    cx: '32',
    cy: '32',
    r: '24',
    fill: '#00C853'
  }),
  h('path', {
    d: 'M20 32l8 8 16-16',
    stroke: 'white',
    'stroke-width': '4',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round'
  })
])

const ErrorIcon = () => h('svg', {
  width: '64',
  height: '64',
  viewBox: '0 0 64 64',
  fill: 'none'
}, [
  h('circle', {
    cx: '32',
    cy: '32',
    r: '28',
    fill: '#FFEBEE'
  }),
  h('circle', {
    cx: '32',
    cy: '32',
    r: '24',
    fill: '#FF5252'
  }),
  h('path', {
    d: 'M22 22l20 20M42 22l-20 20',
    stroke: 'white',
    'stroke-width': '4',
    'stroke-linecap': 'round'
  })
])

// 计算结果
const resultIcon = computed(() => {
  return props.taskStatus.status === 'completed' ? SuccessIcon : ErrorIcon
})

const resultClass = computed(() => {
  return props.taskStatus.status === 'completed' ? 'success' : 'error'
})

const resultTitle = computed(() => {
  return props.taskStatus.status === 'completed' ? '处理完成！' : '处理失败'
})

const resultMessage = computed(() => {
  if (props.taskStatus.status === 'completed') {
    return `成功识别 ${props.taskStatus.successCount} 个表格，已生成 Excel 文件`
  }
  return props.taskStatus.message || '处理过程中发生错误'
})

const statusTagClass = computed(() => {
  switch (props.taskStatus.status) {
    case 'completed':
      return 'tag-success'
    case 'failed':
      return 'tag-error'
    default:
      return 'tag-warning'
  }
})

const statusText = computed(() => {
  switch (props.taskStatus.status) {
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    default:
      return '处理中'
  }
})

const successRate = computed(() => {
  if (props.taskStatus.totalFiles === 0) return 0
  return Math.round((props.taskStatus.successCount / props.taskStatus.totalFiles) * 100)
})

// 成功率图标颜色类
const rateIconClass = computed(() => {
  if (successRate.value >= 80) return 'success'
  if (successRate.value >= 50) return 'warning'
  return 'error'
})

// 成功率数值颜色类
const rateValueClass = computed(() => {
  if (successRate.value >= 80) return 'rate-high'
  if (successRate.value >= 50) return 'rate-medium'
  return 'rate-low'
})
</script>

<style scoped>
.completion-view {
  max-width: 600px;
  margin: 0 auto;
}

.result-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
}

.result-icon.success {
  animation: successBounce 0.6s ease;
}

.result-icon.error {
  animation: errorShake 0.5s ease;
}

@keyframes successBounce {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes errorShake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-10px);
  }
  75% {
    transform: translateX(10px);
  }
}

.result-title {
  font-size: 28px;
  font-weight: 600;
  text-align: center;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.result-message {
  text-align: center;
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.success {
  background: rgba(0, 200, 83, 0.1);
  color: var(--success-color);
}

.stat-icon.error {
  background: rgba(255, 82, 82, 0.1);
  color: var(--error-color);
}

.stat-icon.primary {
  background: rgba(0, 102, 255, 0.1);
  color: var(--primary-color);
}

.stat-icon.warning {
  background: rgba(255, 167, 38, 0.1);
  color: #FFA726;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.rate-high {
  color: var(--success-color);
}

.stat-value.rate-medium {
  color: #FFA726;
}

.stat-value.rate-low {
  color: var(--error-color);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.card-details {
  background: var(--bg-secondary);
}

.card-details h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.detail-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
