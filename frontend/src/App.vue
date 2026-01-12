<template>
  <div class="app">
    <!-- 头部 -->
    <header class="header">
      <div class="container">
        <div class="header-content">
          <div class="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="#0066FF"/>
              <path d="M9 10h14v2H9v-2zm0 5h14v2H9v-2zm0 5h10v2H9v-2z" fill="white"/>
            </svg>
            <h1>纸质数据转换工具</h1>
          </div>
          <div class="header-meta">
            <button class="config-btn" @click="showConfig = true" title="模型配置">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 5a2 2 0 114 0 2 2 0 01-4 0zM10 12a2 2 0 114 0 2 2 0 01-4 0zM10 19a2 2 0 114 0 2 2 0 01-4 0z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <span>模型配置</span>
            </button>
            <span class="tag tag-primary">V3.0</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main">
      <div class="container">
        <!-- 步骤指示器 -->
        <div class="steps">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{ active: currentStep === index, completed: currentStep > index }"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-label">{{ step }}</div>
          </div>
        </div>

        <!-- 步骤 1: 上传文件 -->
        <div v-if="currentStep === 0" class="fade-in">
          <FileUpload
            :is-uploading="isUploading"
            @upload="handleUpload"
          />
        </div>

        <!-- 步骤 2: 配置列 -->
        <div v-if="currentStep === 1" class="fade-in">
          <ColumnConfig
            :is-processing="isProcessing"
            @configure="handleConfigure"
            @back="currentStep = 0"
          />
        </div>

        <!-- 步骤 3: 处理进度 -->
        <div v-if="currentStep === 2" class="fade-in">
          <ProcessProgress
            :task-status="taskStatus"
            @complete="handleComplete"
          />
        </div>

        <!-- 步骤 4: 完成 -->
        <div v-if="currentStep === 3" class="fade-in">
          <CompletionView
            :task-status="taskStatus"
            @reset="handleReset"
            @download="handleDownload"
          />
        </div>
      </div>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <p>基于大模型API · 表格智能识别</p>
      </div>
    </footer>

    <!-- 配置弹窗 -->
    <LLMConfig v-if="showConfig" @close="showConfig = false" @saved="onConfigSaved" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import FileUpload from './components/FileUpload.vue'
import ColumnConfig from './components/ColumnConfig.vue'
import ProcessProgress from './components/ProcessProgress.vue'
import CompletionView from './components/CompletionView.vue'
import LLMConfig from './components/LLMConfig.vue'
import { uploadFiles, startProcess, getStatus } from './api'

// 步骤定义
const steps = ['上传文件', '配置列', '处理中', '完成']

// 当前步骤
const currentStep = ref(0)

// 配置弹窗状态
const showConfig = ref(false)

// 状态
const isUploading = ref(false)
const isProcessing = ref(false)
const taskId = ref(null)
const taskStatus = reactive({
  status: 'pending',
  progress: 0,
  currentFile: null,
  totalFiles: 0,
  processedFiles: 0,
  successCount: 0,
  failCount: 0,
  message: null
})

// 处理文件上传
const handleUpload = async (files) => {
  isUploading.value = true
  try {
    const result = await uploadFiles(files)
    taskId.value = result.task_id
    taskStatus.totalFiles = result.file_count
    currentStep.value = 1
  } catch (error) {
    alert('上传失败：' + error.message)
  } finally {
    isUploading.value = false
  }
}

// 处理列配置
const handleConfigure = async (headers) => {
  isProcessing.value = true
  currentStep.value = 2

  try {
    await startProcess(taskId.value, {
      task_id: taskId.value,
      column_config: {
        headers: headers,
        column_count: headers.length
      }
    })

    // 开始轮询状态
    pollStatus()
  } catch (error) {
    alert('启动处理失败：' + error.message)
    isProcessing.value = false
    currentStep.value = 1
  }
}

// 轮询任务状态
const pollStatus = async () => {
  let isPolling = true

  const doPoll = async () => {
    if (!isPolling) return

    try {
      const status = await getStatus(taskId.value)
      // 映射后端 snake_case 到前端 camelCase
      taskStatus.status = status.status
      taskStatus.progress = status.progress
      taskStatus.currentFile = status.current_file
      taskStatus.totalFiles = status.total_files
      taskStatus.processedFiles = status.processed_files
      taskStatus.successCount = status.success_count
      taskStatus.failCount = status.fail_count
      taskStatus.message = status.message

      if (status.status === 'completed' || status.status === 'failed') {
        isPolling = false
        isProcessing.value = false
        currentStep.value = 3
        return
      }

      // 继续轮询，间隔2秒
      setTimeout(doPoll, 2000)
    } catch (error) {
      console.error('获取状态失败:', error)
      // 出错后继续轮询
      setTimeout(doPoll, 3000)
    }
  }

  doPoll()
}

// 处理完成
const handleComplete = () => {
  currentStep.value = 3
}

// 下载文件
const handleDownload = () => {
  window.open(`/api/download/${taskId.value}`, '_blank')
}

// 重置
const handleReset = () => {
  currentStep.value = 0
  taskId.value = null
  Object.assign(taskStatus, {
    status: 'pending',
    progress: 0,
    currentFile: null,
    totalFiles: 0,
    processedFiles: 0,
    successCount: 0,
    failCount: 0,
    message: null
  })
}

// 配置保存后的处理
const onConfigSaved = () => {
  // 可以在这里添加配置保存后的处理逻辑
  console.log('配置已保存')
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: white;
  border-bottom: 1px solid var(--border-color);
  padding: 20px 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.config-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--primary-color);
}

.main {
  flex: 1;
  padding: 40px 0;
}

.steps {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 40px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step-item.active .step-number {
  background: var(--primary-color);
  color: white;
}

.step-item.completed .step-number {
  background: var(--success-color);
  color: white;
}

.step-label {
  font-size: 14px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.step-item.active .step-label,
.step-item.completed .step-label {
  color: var(--text-primary);
}

.footer {
  background: white;
  border-top: 1px solid var(--border-color);
  padding: 20px 0;
  margin-top: auto;
}

.footer p {
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
