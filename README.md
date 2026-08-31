# AgenticRAGOCR

基于多模态 OCR + RAG 的智能文档问答系统。支持 PDF、图片等文档的结构化解析（文本、表格、图像、公式），并通过向量检索 + 大语言模型实现带引用溯源的问答。

## ✨ 核心特性

- 🔍 **多模态版面理解**：基于 PaddleOCR-VL + PP-DocLayoutV2 将页面拆解为文本 / 表格 / 图像 / 公式等结构化版面块
- 🎯 **可信引用溯源**：答案关键信息可一键回溯到原文精确位置（页码、块坐标、图片预览）
- ⚡ **流式生成**：SSE 逐字推送，首字响应快、交互流畅
- 🧩 **双 OCR 模式**：云端 API（免 GPU）与本地 GPU 推理可配置切换
- 📊 **多类型内容渲染**：表格转 HTML、公式用 KaTeX、图片原样展示


## 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- 阿里云 DashScope API Key（Qwen 模型 + Embedding）
- 飞桨云端 OCR API Token（cloud 模式，无需本地 GPU）

### 方式一：一键启动（推荐）

```bash
# 1. 先完成下方"环境配置"步骤
# 2. 然后运行启动脚本

# Linux / Mac
bash start.sh

# Windows PowerShell
.\start.ps1
```

启动脚本自动从 `backend/.env` 读取 `PORT`，从 `frontend/.env` 读取 `VITE_PORT`，无需手动修改端口。

### 方式二：手动启动

#### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（cloud 模式，无需本地模型）
cp .env.example .env
# 编辑 .env，填写 DASHSCOPE_API_KEY、PADDLEOCR_API_TOKEN、SERVER_BASE_URL

# 启动（默认端口 8100）
python start_backend.py
```

详细说明见 [backend/README.md](backend/README.md)

#### 2. 启动前端

```bash
cd frontend
npm install
# 可选：复制并修改 .env
cp .env.example .env
npm run dev
# 访问 http://localhost:3000
```

### 端口配置

| 配置项 | 文件 | 默认值 | 说明 |
|--------|------|--------|------|
| `PORT` | `backend/.env` | 8100 | 后端监听端口 |
| `SERVER_BASE_URL` | `backend/.env` | http://localhost:8100 | 资源链接基础 URL，公网部署时改为实际地址 |
| `VITE_PORT` | `frontend/.env` | 3000 | 前端开发服务器端口 |
| `VITE_API_BASE_URL` | `frontend/.env` | http://localhost:8100 | 前端请求后端的基础 URL |

### 3. 使用流程

1. 打开前端页面，上传 PDF 或图片文档
2. 系统自动进行 OCR 解析（cloud 模式调用飞桨 API）并建立向量索引
3. 在右侧问答框输入问题，获得带【引用】标注的回答
4. 点击引用数字查看原文来源（含页码、位置坐标、图片预览）

## 系统架构

```
前端 (React + Vite)
  │
  ├─ 文件上传 → POST /api/upload
  ├─ 进度轮询 → GET /api/progress/{doc_id}
  └─ 流式问答 → POST /api/query/stream (SSE)

后端 (FastAPI)
  │
  ├─ OCR Service    → 飞桨云端 API（cloud 模式）/ PaddleOCRVL（local 模式）
  ├─ RAG Service    → ChromaDB 向量库 + DashScope Embedding
  └─ LLM Service    → Qwen（DashScope）流式生成
```

## 项目结构

```
AgenticRAGOCR/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   └── services/
│   ├── docs/
│   ├── requirements.txt
│   └── README.md
├── frontend/         # React 前端
│   ├── src/
│   │   ├── components/
│   │   └── contexts/
│   └── README.md
└── README.md         # 本文件
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [backend/README.md](backend/README.md) | 后端安装、双 OCR 模式、API 端点说明 |
| [frontend/README.md](frontend/README.md) | 前端开发说明 |

## 待办

- [ ] 左侧历史文件列表：支持查看已上传文档，点击切换对话上下文

## License

MIT
