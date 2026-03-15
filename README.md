# stock-kline-search

前后端分离目录结构，便于 Railway 分别监督与部署。

## 目录结构

- `backend/`：FastAPI + 自动同步 + 相似检索
- `frontend/`：Next.js 页面

## Railway 双 Service 配置

### 1) Backend Service

- 仓库：`gongye19/KlineRetriever`
- Root Directory：`backend`
- 依赖安装：`pip install -r requirements.txt`
- 启动命令：使用 `backend/Procfile`
- 环境变量：
  - `DATABASE_URL`（Postgres 插件自动注入）
  - `SYNC_INTERVAL_HOURS=12`
  - `CORS_ORIGINS=https://<你的前端域名>`

### 2) Frontend Service

- 仓库：`gongye19/KlineRetriever`
- Root Directory：`frontend`
- Build Command：`npm install && npm run build`
- Start Command：`npm run start`
- 环境变量：
  - `NEXT_PUBLIC_API_BASE_URL=https://<你的后端域名>`

## 验证

- 后端：`https://<backend-domain>/health`
- 前端：`https://<frontend-domain>/`

详细说明见：

- `backend/README.md`
- `frontend/README.md`

