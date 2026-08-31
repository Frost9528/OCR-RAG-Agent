# AOCR-RAG-Agent Backend

多模态 RAG 系统后端服务，支持 PDF 和图片文档的解析、索引和问答。

## 技术栈

- **FastAPI**: REST API 框架
- **PaddleOCR-VL**: 多模态文档解析（文本、表格、图像、公式）
- **ChromaDB**: 向量数据库
- **LangChain**: RAG 编排
- **Alibaba Cloud DashScope**: Qwen 大语言模型 + Embedding 模型

## 功能特性

- ✅ 支持 PDF、PNG、JPG 等格式的文档解析
- ✅ 自动识别文本、表格、图像、公式等多种内容类型
- ✅ 向量化索引，支持语义检索
- ✅ 完美的引用溯源（包含页码、块ID、位置坐标）
- ✅ 基于 Qwen 的智能问答
- ✅ 流式响应支持
- ✅ 异步处理，进度跟踪

## 安装步骤

> **环境要求**: Python **3.13+**，推荐使用虚拟环境

### 1. 创建虚拟环境并安装依赖

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活（Windows）
.venv\Scripts\activate
# 激活（Linux/Mac）
# source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，**cloud 模式**（推荐，无需本地 GPU）最少只需填写：

```env
# 阿里云百炼 API Key（Qwen 模型 + Embedding，必填）
DASHSCOPE_API_KEY=your_dashscope_api_key

# OCR 模式：cloud（飞桨云端 API）或 local（本地 PaddleOCRVL）
OCR_MODE=cloud

# 飞桨云端 OCR（cloud 模式必填）
PADDLEOCR_API_TOKEN=your_paddleocr_token
PADDLEOCR_API_URL=https://t7leseh0b8e85b24.aistudio-app.com/layout-parsing
```

**local 模式**（需要 Linux + GPU）额外配置：

```env
OCR_MODE=local
PADDLEOCR_VL_MODEL_DIR=/path/to/PaddleOCR-VL-0.9B
LAYOUT_DETECTION_MODEL_DIR=/path/to/PP-DocLayoutV2
```

### 3. 启动服务

```bash
# 推荐方式（使用虚拟环境内的 Python）
python start_backend.py

# 或手动指定
python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

服务启动后访问：
- API 文档: http://localhost:8100/docs
- 健康检查: http://localhost:8100/

## API 端点

### 1. 上传文档
```http
POST /api/upload
Content-Type: multipart/form-data

file: [PDF/PNG/JPG 文件]
```

返回：
```json
{
  "doc_id": "uuid",
  "file_name": "example.pdf",
  "status": "processing",
  "message": "文档上传成功，正在处理中..."
}
```

### 2. 查询进度
```http
GET /api/progress/{doc_id}
```

返回：
```json
{
  "doc_id": "uuid",
  "status": "completed",
  "progress": 100,
  "message": "索引构建完成！",
  "stats": {
    "doc_id": "uuid",
    "text_blocks": 45,
    "table_blocks": 3,
    "image_blocks": 5,
    "formula_blocks": 2,
    "total_blocks": 55
  }
}
```

### 3. 文档问答
```http
POST /api/query
Content-Type: application/json

{
  "doc_id": "uuid",
  "query": "这篇论文的主要发现是什么？"
}
```

返回：
```json
{
  "answer": "这篇论文提出了三个主要发现：...",
  "citations": [
    {
      "id": 1,
      "source": "example.pdf",
      "page": 3,
      "snippet": "...",
      "type": "text",
      "score": 0.95
    }
  ],
  "doc_id": "uuid"
}
```

### 4. 流式问答
```http
POST /api/query/stream
Content-Type: application/json

{
  "doc_id": "uuid",
  "query": "解释一下第二章的内容"
}
```

返回 SSE 流式响应。

### 5. 删除文档
```http
DELETE /api/documents/{doc_id}
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用主入口
│   ├── config.py               # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic 数据模型
│   └── services/
│       ├── __init__.py
│       ├── ocr_service.py      # PaddleOCR 服务
│       ├── rag_service.py      # RAG 索引与检索
│       └── llm_service.py      # Qwen 模型服务
├── .env.example                # 环境变量模板
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 开发说明

### 日志

日志会输出到控制台，包含以下信息：
- 服务启动/关闭
- 文档上传和处理进度
- OCR 解析结果
- 向量索引构建
- 查询请求和响应

### 数据持久化

- **上传文件**: `./uploads/{doc_id}/`
- **ChromaDB**: `./data/chroma_db/`
- **OCR 输出**: `./uploads/{doc_id}/*.json` 和 `*.md`

### 性能优化

- OCR 和 Embedding 在线程池中异步执行，避免阻塞
- 支持批量向量化
- ChromaDB 使用 HNSW 索引加速检索

## 常见问题

**Q: 如何获取阿里云百炼 API Key？**
A: 访问 https://dashscope.console.aliyun.com/ 注册并获取 API Key。

**Q: PaddleOCR 模型太大怎么办？**
A: 可以使用 PaddleOCR 提供的轻量级模型，或使用云端 OCR API。

**Q: 支持哪些文档格式？**
A: 目前支持 PDF、PNG、JPG、JPEG。可以通过修改 `settings.allowed_extensions` 扩展。

**Q: 如何调整检索数量？**
A: 在 `.env` 中设置 `RETRIEVAL_TOP_K=10`（默认 5）。

**Q: 使用的是哪个 Embedding 模型？**
A: 使用阿里云 DashScope 的 `text-embedding-v3` 模型，支持中英文，维度 1024，无需本地部署。

## License

MIT
