# stock-kline-search

Railway 可部署的美股 K 线比例相似检索服务（个人项目轻量版）。

## 技术栈

- 后端 API：`FastAPI` + `Uvicorn`
- 数据获取：`yfinance`
- 数据库存储：`PostgreSQL`（Railway）/ `SQLite`（本地无 `DATABASE_URL` 时自动回退）
- 计算：`pandas` / `numpy` / `scipy`
- 定时任务：`APScheduler`

## 存储计划与原因

- Railway 上默认使用 `PostgreSQL`，原因：
  - 部署端稳定：Railway 原生托管，自动注入 `DATABASE_URL`。
  - 数据可持续：服务重启不丢数据，适合线上持续增量同步。
  - 后续可扩展：股票池扩大后查询和索引能力优于本地文件库。
- 本地开发保留 `SQLite` 自动回退，原因：
  - 无需先安装 Postgres，开箱即用。
  - 仍可直接验证完整流程。

## 功能

1. 服务启动后自动执行一次增量同步。
2. 按配置的间隔（默认 12 小时）自动检查并更新数据。
3. 提供 K 线查询接口和相似检索接口。
4. 检索按“比例变化”进行（归一化后比较），不是按绝对价格比较。

## 本地运行

```bash
cd stock-kline-search
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 关键环境变量

- `DATABASE_URL`: Railway Postgres 连接串（线上必填）
- `SYNC_INTERVAL_HOURS`: 自动增量同步间隔（默认 `12`）
- `DEFAULT_SYMBOLS`: 默认股票池，逗号分隔（可选）

## 主要接口

- `GET /health`
- `POST /sync`（按 start/end 执行同步）
- `POST /sync/incremental`（增量同步）
- `GET /kline?symbol=AAPL&interval=1d&start=2024-01-01&end=2024-06-30`
- `POST /search`

`/search` 请求示例：

```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "start": "2024-01-01",
  "end": "2024-06-30",
  "top_n": 10
}
```

## Railway 部署

1. 在 Railway 新建项目并添加 Postgres。
2. 连接本仓库。
3. 确认环境变量 `DATABASE_URL` 已注入。
4. 启动命令使用 `Procfile`（见仓库根目录）。

