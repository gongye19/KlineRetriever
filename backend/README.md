# backend

Railway 可部署的 K 线检索后端服务。

## 技术栈

- `FastAPI` + `Uvicorn`
- `PostgreSQL`（Railway）/ `SQLite`（本地回退）
- `APScheduler` 定时增量同步
- `yfinance` 数据获取

## 股票池配置

- 文件：`backend/config/symbols.txt`
- 一行一个股票代码
- 支持注释行（以 `#` 开头）
- `DEFAULT_SYMBOLS` 环境变量只作为临时覆盖

## 本地运行

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 关键环境变量

- `DATABASE_URL`
- `SYNC_INTERVAL_HOURS`（默认 12）
- `CORS_ORIGINS`（默认 `*`）

## API

- `GET /health`
- `GET /symbols`
- `POST /sync`
- `POST /sync/incremental`
- `GET /kline`
- `POST /search`
