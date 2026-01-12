<template>
  <div class="llm-config" @click.self="closeAllDropdowns">
    <div class="config-card">
      <div class="config-header">
        <div class="config-title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 15V3m0 12l-4-4m4 4l4-4M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <h2>大模型配置</h2>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="config-body">
        <!-- 提供商选择 -->
        <div class="form-group">
          <label class="form-label">模型提供商</label>
          <div class="custom-select-wrapper">
            <div class="select-trigger" @click.stop="toggleProviderDropdown">
              <span>{{ currentProviderName }}</span>
              <svg class="arrow" :class="{ open: showProviderDropdown }" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <teleport to="body">
              <div v-if="showProviderDropdown" class="select-dropdown-fixed" :style="providerDropdownPosition">
                <div
                  v-for="provider in providers"
                  :key="provider.id"
                  class="select-option"
                  :class="{ selected: config.provider === provider.id, disabled: !provider.supports_vision }"
                  @click="selectProvider(provider)"
                >
                  {{ provider.name }}
                  <span v-if="!provider.supports_vision" class="vision-tag">(暂不支持视觉)</span>
                </div>
              </div>
            </teleport>
          </div>
        </div>

        <!-- 模型选择 -->
        <div class="form-group">
          <label class="form-label">
            {{ useEndpointId ? 'Endpoint ID' : '模型名称' }}
          </label>
          <!-- 如果有预定义模型且不使用endpoint，显示下拉 -->
          <div v-if="availableModels.length > 0 && !useEndpointId" class="custom-select-wrapper">
            <div class="select-trigger" @click.stop="toggleModelDropdown">
              <span>{{ config.model || '请选择模型' }}</span>
              <svg class="arrow" :class="{ open: showModelDropdown }" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <teleport to="body">
              <div v-if="showModelDropdown" class="select-dropdown-fixed" :style="modelDropdownPosition">
                <div
                  v-for="model in availableModels"
                  :key="model"
                  class="select-option"
                  :class="{ selected: config.model === model }"
                  @click="selectModel(model)"
                >
                  {{ model }}
                </div>
              </div>
            </teleport>
          </div>
          <!-- 否则显示输入框 -->
          <input
            v-else
            v-model="config.model"
            type="text"
            class="form-input"
            :placeholder="useEndpointId ? '请输入 Endpoint ID' : '请输入模型名称'"
          />
        </div>

        <!-- API密钥 -->
        <div class="form-group">
          <label class="form-label">API Key</label>
          <div class="input-with-toggle">
            <input
              v-model="config.api_key"
              :type="showApiKey ? 'text' : 'password'"
              class="form-input"
              placeholder="请输入 API Key"
            />
            <button class="toggle-btn" @click="showApiKey = !showApiKey" type="button">
              {{ showApiKey ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>

        <!-- 自定义API地址 (仅自定义提供商) -->
        <div v-if="config.provider === 'custom'" class="form-group">
          <label class="form-label">API 地址</label>
          <input
            v-model="config.base_url"
            type="text"
            class="form-input"
            placeholder="https://api.example.com/v1/chat/completions"
          />
        </div>

        <!-- 高级设置 -->
        <details class="advanced-settings">
          <summary>高级设置</summary>
          <div class="advanced-fields">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">温度 (Temperature)</label>
                <input v-model.number="config.temperature" type="number" step="0.01" min="0" max="2" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">最大 Tokens</label>
                <input v-model.number="config.max_tokens" type="number" min="1" class="form-input" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">超时时间 (秒)</label>
              <input v-model.number="config.timeout" type="number" min="10" class="form-input" />
            </div>
          </div>
        </details>

        <!-- 提示信息 -->
        <div class="config-tip">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 5v3M8 10.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>配置将自动保存，支持 OpenAI、Claude、豆包、通义千问、智谱AI 等主流模型</span>
        </div>
      </div>

      <div class="config-footer">
        <button class="btn btn-secondary" @click="$emit('close')" type="button">取消</button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="isSaving" type="button">
          {{ isSaving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getProviders, getCurrentConfig, updateConfig } from '../api'

const emit = defineEmits(['close', 'saved'])

// 状态
const providers = ref([])
const isSaving = ref(false)
const showApiKey = ref(false)
const showProviderDropdown = ref(false)
const showModelDropdown = ref(false)
const providerDropdownPosition = ref({})
const modelDropdownPosition = ref({})

// 配置数据
const config = reactive({
  provider: 'doubao',
  model: '',
  api_key: '',
  base_url: '',
  temperature: 0.01,
  max_tokens: 4096,
  timeout: 180
})

// 计算属性
const currentProvider = computed(() => {
  return providers.value.find(p => p.id === config.provider)
})

const currentProviderName = computed(() => {
  const provider = currentProvider.value
  if (!provider) return '请选择'
  return provider.name
})

const availableModels = computed(() => {
  return currentProvider.value?.models || []
})

const useEndpointId = computed(() => {
  return currentProvider.value?.use_endpoint_id || false
})

// 加载提供商列表
const loadProviders = async () => {
  try {
    const data = await getProviders()
    providers.value = data.providers
    console.log('加载的提供商列表:', providers.value)
  } catch (error) {
    console.error('加载提供商列表失败:', error)
  }
}

// 加载当前配置
const loadCurrentConfig = async () => {
  try {
    const data = await getCurrentConfig()
    Object.assign(config, data)
    console.log('当前配置:', config)
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 计算下拉框位置
const calculateDropdownPosition = (event) => {
  const trigger = event.target.closest('.select-trigger')
  if (!trigger) return null

  const rect = trigger.getBoundingClientRect()
  return {
    position: 'fixed',
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    zIndex: 10001
  }
}

// 切换提供商下拉
const toggleProviderDropdown = (event) => {
  if (showProviderDropdown.value) {
    showProviderDropdown.value = false
  } else {
    showModelDropdown.value = false
    showProviderDropdown.value = true
    nextTick(() => {
      providerDropdownPosition.value = calculateDropdownPosition(event)
    })
  }
}

// 切换模型下拉
const toggleModelDropdown = (event) => {
  if (showModelDropdown.value) {
    showModelDropdown.value = false
  } else {
    showProviderDropdown.value = false
    showModelDropdown.value = true
    nextTick(() => {
      modelDropdownPosition.value = calculateDropdownPosition(event)
    })
  }
}

// 关闭所有下拉
const closeAllDropdowns = () => {
  showProviderDropdown.value = false
  showModelDropdown.value = false
}

// 选择提供商
const selectProvider = (provider) => {
  if (!provider.supports_vision) return
  config.provider = provider.id
  config.model = ''
  if (provider.id !== 'custom') {
    config.base_url = ''
  }
  showProviderDropdown.value = false
}

// 选择模型
const selectModel = (model) => {
  config.model = model
  showModelDropdown.value = false
}

// 保存配置
const saveConfig = async () => {
  if (!config.provider) {
    alert('请选择模型提供商')
    return
  }
  if (!config.model) {
    alert('请输入模型名称')
    return
  }
  if (!config.api_key) {
    alert('请输入 API Key')
    return
  }

  isSaving.value = true
  try {
    await updateConfig(config)
    alert('配置保存成功！')
    emit('saved')
    emit('close')
  } catch (error) {
    alert('保存配置失败: ' + error.message)
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadProviders()
  loadCurrentConfig()
  document.addEventListener('click', closeAllDropdowns)
})

onUnmounted(() => {
  document.removeEventListener('click', closeAllDropdowns)
})
</script>

<style scoped>
.llm-config {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.config-card {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.config-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-title h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.config-title svg {
  color: var(--primary-color);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.config-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 20px;
  position: relative;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: white;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

/* 自定义下拉组件 */
.custom-select-wrapper {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
  user-select: none;
}

.select-trigger:hover {
  border-color: var(--primary-color);
}

.select-trigger .arrow {
  flex-shrink: 0;
  transition: transform 0.2s;
  color: var(--text-secondary);
}

.select-trigger .arrow.open {
  transform: rotate(180deg);
}

.input-with-toggle {
  display: flex;
  gap: 8px;
}

.input-with-toggle .form-input {
  flex: 1;
}

.toggle-btn {
  padding: 0 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.toggle-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.advanced-settings {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.advanced-settings summary {
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  user-select: none;
}

.advanced-settings summary:hover {
  color: var(--text-primary);
}

.advanced-fields {
  margin-top: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.config-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #E3F2FD;
  border-radius: 8px;
  font-size: 13px;
  color: #1565C0;
}

.config-tip svg {
  flex-shrink: 0;
  margin-top: 1px;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: white;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0052CC;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

<!-- 全局样式，不使用 scoped -->
<style>
/* Teleport 下拉框样式 - 全局生效 */
.select-dropdown-fixed {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  max-height: 250px;
  overflow-y: auto;
}

.select-dropdown-fixed .select-option {
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background-color 0.15s;
}

.select-dropdown-fixed .select-option:hover {
  background: var(--bg-secondary);
}

.select-dropdown-fixed .select-option.selected {
  background: #E3F2FD;
  color: var(--primary-color);
  font-weight: 500;
}

.select-dropdown-fixed .select-option.disabled {
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.select-dropdown-fixed .select-option.disabled:hover {
  background: transparent;
}

.select-dropdown-fixed .vision-tag {
  color: var(--text-tertiary);
  font-size: 12px;
}
</style>
