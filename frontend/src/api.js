/**
 * API 服务模块
 */

const API_BASE = '/api'

/**
 * 安全解析 JSON 响应
 */
async function safeParseJson(response) {
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return await response.json()
  }
  const text = await response.text()
  return { detail: text }
}

/**
 * 上传文件
 */
export async function uploadFiles(files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await safeParseJson(response)
    throw new Error(error.detail || `上传失败 (${response.status})`)
  }

  return await response.json()
}

/**
 * 开始处理
 * columnConfig 参数应该是完整的请求体，包含 task_id 和 column_config
 */
export async function startProcess(taskId, requestData) {
  const response = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestData)
  })

  if (!response.ok) {
    const error = await safeParseJson(response)
    // 处理 FastAPI 验证错误格式
    if (error.detail) {
      if (Array.isArray(error.detail)) {
        // FastAPI 验证错误数组格式
        const details = error.detail.map(e => e.msg || String(e)).join(', ')
        throw new Error(`请求参数错误: ${details}`)
      }
      throw new Error(error.detail)
    }
    throw new Error(`启动处理失败 (${response.status})`)
  }

  return await response.json()
}

/**
 * 获取任务状态
 */
export async function getStatus(taskId) {
  const response = await fetch(`${API_BASE}/status/${taskId}`)

  if (!response.ok) {
    throw new Error('获取状态失败')
  }

  return await response.json()
}

/**
 * 列出所有任务
 */
export async function listTasks() {
  const response = await fetch(`${API_BASE}/tasks`)

  if (!response.ok) {
    throw new Error('获取任务列表失败')
  }

  return await response.json()
}

/**
 * 删除任务
 */
export async function deleteTask(taskId) {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error('删除任务失败')
  }

  return await response.json()
}
