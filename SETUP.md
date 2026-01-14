# 纸质数据转换工具 - 使用指南

基于 OCR 的纸质表格识别与转换工具，支持批量上传图片并转换为 Excel 文件。

## 目录

- [功能特点](#功能特点)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [详细安装步骤](#详细安装步骤)
- [配置 API 密钥](#配置-api-密钥)
- [启动服务](#启动服务)
- [使用说明](#使用说明)
- [常见问题](#常见问题)
- [API 密钥申请指南](#api-密钥申请指南)

---

## 功能特点

- 🖼️ **批量上传**：支持选择文件夹或多选图片文件
- 📊 **智能识别**：基于大模型 OCR API 的高精度表格识别
- ⚙️ **灵活配置**：自定义表格列数和列标题
- 📈 **实时进度**：实时显示处理进度和状态
- 💾 **一键下载**：处理完成后直接下载 Excel 文件
- 🎨 **现代界面**：简洁美观的用户界面

---

## 前置要求

在开始之前，请确保您的电脑已安装以下软件：

| 软件 | 版本要求 | 用途 | 检查方法 |
|------|---------|------|---------|
| **Python** | 3.9 或更高 | 运行后端服务 | 在终端输入 `python --version` |
| **Node.js** | 16 或更高 | 运行前端服务 | 在终端输入 `node --version` |
| **npm** | 自动随 Node.js 安装 | 安装前端依赖 | 在终端输入 `npm --version` |

### 如何安装前置软件？

**Windows 用户：**
- Python：访问 https://www.python.org/downloads/ 下载安装
- Node.js：访问 https://nodejs.org/ 下载安装

**Mac 用户：**
```bash
# 使用 Homebrew 安装
brew install python
brew install node
```

**Linux 用户：**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm
```

---

## 快速开始

> ⚡ 如果您已经熟悉开发环境，可以按照以下步骤快速开始：

```bash
# 1. 克隆项目
git clone https://github.com/phj2001/paper-data-converter.git
cd paper-data-converter

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 3. 安装前端依赖
cd frontend
npm install
cd ..

# 4. 配置 API 密钥（重要！）
# 复制并编辑配置文件
cp config.json.example config.json
# 然后用文本编辑器打开 config.json，填入您的 API 密钥

# 5. 启动后端（终端 1）
cd backend
python app.py

# 6. 启动前端（终端 2，新开一个终端）
cd frontend
npm run dev

# 7. 访问应用
# 浏览器打开 http://localhost:5173
```

---

## 详细安装步骤

### 步骤 1：下载项目

**方式 A：使用 Git 克隆（推荐）**

在终端（命令行）中执行：

```bash
git clone https://github.com/phj2001/paper-data-converter.git
cd paper-data-converter
```

**方式 B：直接下载 ZIP**

1. 访问：https://github.com/phj2001/paper-data-converter
2. 点击绿色的 **Code** 按钮
3. 选择 **Download ZIP**
4. 解压到任意目录

### 步骤 2：安装后端依赖

```bash
# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt
```

> 💡 **提示**：如果安装速度慢，可以使用国内镜像：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 步骤 3：安装前端依赖

```bash
# 进入前端目录（从项目根目录）
cd ../frontend

# 安装 Node.js 依赖
npm install
```

> 💡 **提示**：如果安装速度慢，可以使用国内镜像：
> ```bash
> npm install --registry=https://registry.npmmirror.com
> ```

---

## 配置 API 密钥

> ⚠️ **重要**：您必须配置 API 密钥才能使用本工具！本工具支持多种大模型提供商。

### 支持的大模型提供商

| 提供商 | 名称 | 视觉能力 |
|--------|------|---------|
| doubao | 豆包（字节跳动） | ✅ |
| openai | OpenAI | ✅ |
| anthropic | Anthropic (Claude) | ✅ |
| qwen | 通义千问（阿里） | ✅ |
| zhipu | 智谱AI | ✅ |
| tencent | 腾讯混元 | ✅ |
| baidu | 百度文心 | ❌ |
| deepseek | DeepSeek | ❌ |
| moonshot | Moonshot (Kimi) | ❌ |

### 方式 A：使用配置文件（推荐）

1. 在项目根目录创建 `config.json` 文件
2. 复制 `config.json.example` 的内容到 `config.json`
3. 根据您使用的提供商，填入相应的 API 密钥

**示例 1：使用豆包**
```json
{
  "provider": "doubao",
  "model": "ep-20260104183112-xxxxx",
  "api_key": "您的豆包API密钥",
  "base_url": null,
  "temperature": 0.01,
  "max_tokens": 4096,
  "timeout": 180
}
```

**示例 2：使用 OpenAI**
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "您的OpenAI API密钥",
  "base_url": null,
  "temperature": 0.01,
  "max_tokens": 4096,
  "timeout": 180
}
```

**示例 3：使用通义千问**
```json
{
  "provider": "qwen",
  "model": "qwen-vl-max",
  "api_key": "您的通义千问API密钥",
  "base_url": null,
  "temperature": 0.01,
  "max_tokens": 4096,
  "timeout": 180
}
```

### 方式 B：使用环境变量

1. 在项目根目录创建 `.env` 文件
2. 复制 `.env.example` 的内容到 `.env`
3. 填入您的 API 密钥

**示例（豆包）：**
```bash
# 豆包配置
ARK_API_KEY=您的豆包API密钥
ARK_ENDPOINT_ID=您的EndpointID

# 默认提供商
LLM_PROVIDER=doubao
```

---

## 启动服务

您需要**同时启动后端和前端**两个服务，因此需要打开**两个终端窗口**。

### 终端 1：启动后端服务

```bash
cd backend
python app.py
```

看到以下信息表示启动成功：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 终端 2：启动前端服务

**打开一个新的终端窗口**，然后执行：

```bash
cd frontend
npm run dev
```

看到以下信息表示启动成功：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 使用说明

### 1. 访问应用

打开浏览器，访问：`http://localhost:5173`

### 2. 配置大模型

首次使用需要在页面中配置大模型：

1. 点击右上角的 **"设置"** 按钮
2. 选择您使用的提供商（如：豆包、OpenAI 等）
3. 输入 API 密钥
4. 输入模型名称（或 Endpoint ID）
5. 点击 **"保存配置"**

> 💡 **提示**：如果在 `config.json` 中已经配置过，这一步可以跳过。

### 3. 上传图片

- 点击上传区域选择文件夹
- 或直接拖拽多个图片文件到上传区域
- 支持的格式：JPG、PNG、BMP、WebP

### 4. 配置表格列结构

- 输入表格的列数（1-20）
- 为每列设置标题
- 预览表格结构

### 5. 开始处理

- 点击 **"开始处理"** 按钮
- 系统将逐个识别图片中的表格
- 实时显示处理进度和状态

### 6. 下载结果

- 处理完成后点击 **"下载 Excel"**
- 数据将以统一格式导出到 Excel 文件

---

## 常见问题

### ❓ Q1: 提示"API密钥不能为空"怎么办？

**A:** 请确保您已经配置了 API 密钥：
- 检查项目根目录是否有 `config.json` 文件
- 确认 `config.json` 中的 `api_key` 字段已填写
- 或者检查 `.env` 文件是否配置了对应的环境变量

### ❓ Q2: 端口 8000 或 5173 被占用怎么办？

**A:** 修改端口号：

**修改后端端口（8000）：**
编辑 `backend/app.py` 文件的最后一行：
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为其他端口
```

**修改前端端口（5173）：**
编辑 `frontend/vite.config.js` 文件：
```javascript
server: {
  port: 3000  // 改为其他端口
}
```

### ❓ Q3: npm install 速度很慢或失败？

**A:** 使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

### ❓ Q4: pip install 报错怎么办？

**A:** 尝试以下解决方案：

1. 升级 pip：
```bash
python -m pip install --upgrade pip
```

2. 使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. Windows 用户可能需要安装 [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### ❓ Q5: OCR 识别失败或效果不好？

**A:** 可能的原因：
- API 密钥无效或已过期
- 图片质量过低
- 图片格式不支持
- 超出 API 配额限制

**解决方法：**
- 检查 API 密钥是否正确
- 使用清晰度更高的图片
- 检查 API 提供商的配额使用情况

### ❓ Q6: 前端页面无法连接后端？

**A:** 检查：
1. 后端服务是否正常运行（终端 1）
2. 确认后端运行在 `http://localhost:8000`
3. 浏览器控制台（F12）是否有错误信息

---

## API 密钥申请指南

### 豆包（字节跳动）

1. 访问：https://console.volcengine.com/ark
2. 注册/登录账号
3. 创建推理接口（Endpoint）
4. 获取 API Key 和 Endpoint ID

### OpenAI

1. 访问：https://platform.openai.com/api-keys
2. 注册/登录账号
3. 点击 "Create new secret key"
4. 复制生成的 API Key

### 通义千问（阿里）

1. 访问：https://dashscope.aliyun.com/
2. 注册/登录账号
3. 进入控制台 → API-KEY 管理
4. 创建 API Key

### 智谱AI

1. 访问：https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入 API 密钥管理
4. 创建 API Key

---

## 项目结构

```
paper-data-converter/
├── backend/                 # 后端服务
│   ├── app.py              # FastAPI 主应用
│   ├── llm_config.py       # 大模型配置管理
│   ├── requirements.txt    # Python 依赖
│   └── ...
│
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   ├── package.json       # Node.js 依赖配置
│   └── ...
│
├── config.json.example     # 配置文件模板（需复制为 config.json）
├── .env.example           # 环境变量模板（需复制为 .env）
├── SETUP.md              # 本文档
└── README_WEB.md         # 项目说明文档
```

---

## 技术支持

如果遇到问题，可以：

1. 查看 [常见问题](#常见问题) 章节
2. 在 GitHub 上提 Issue：https://github.com/phj2001/paper-data-converter/issues
3. 查看项目 Wiki 和文档

---

## 许可证

MIT License

---

## 更新日志

### v1.0.0
- ✨ 初始版本发布
- ✅ 支持多种大模型提供商
- ✅ 批量图片上传和处理
- ✅ 实时进度显示
- ✅ 一键下载 Excel

---

**祝您使用愉快！** 🎉
