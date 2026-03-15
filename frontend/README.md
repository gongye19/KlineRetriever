# frontend

Next.js 前端，调用后端 API 完成：

- 选择股票/周期/时间区间
- 查看目标 K 线归一化走势
- 执行相似检索并显示 Top10

## 本地运行

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Railway

- Root Directory：`frontend`
- Build Command：`npm install && npm run build`
- Start Command：`npm run start`
- 关键环境变量：`NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>`
