# Infra Runbook

这份手册用于本地开发、自检平台依赖、以及在有 Docker 的机器上完成整套基础设施联通验证。

## 本地开发

```bash
conda activate advanced-marketplace

cd /Users/yzj/vs-workspace/db-design/backend
uvicorn app.main:app --reload

cd /Users/yzj/vs-workspace/db-design/frontend
npm run dev
```

本地默认行为：
- `STORAGE_BACKEND=local`
- 商品图片写入 `backend/storage/uploads`
- Redis / Celery / OpenSearch 不可用时自动进入降级模式

## 本地验证

```bash
cd /Users/yzj/vs-workspace/db-design/backend
pytest -q
```

建议再手工检查这些页面和接口：
- `GET /health`
- `GET /api/products`
- `GET /api/recommendations/home`
- 管理端 `/admin/platform`
- 管理端 `/admin/recommendations`

## Docker 联调

```bash
cd /Users/yzj/vs-workspace/db-design
make docker-pull
docker compose up --detach --wait --wait-timeout 300
docker compose ps
docker compose logs -f api worker redis minio opensearch
make docker-smoke
```

预期服务：
- `api`
- `worker`
- `frontend`
- `redis`
- `minio`
- `opensearch`
- `nginx`

关键访问地址：
- 网关：`http://localhost:8080`
- API：`http://localhost:8000`
- Vite：`http://localhost:5173`
- MinIO Console：`http://localhost:9001`
- OpenSearch：`http://localhost:9200`

## 运维台判读

`/admin/platform` 现在会显示 5 类就绪度：
- `数据库`
- `Redis / Broker`
- `异步任务`
- `媒体存储`
- `搜索索引`

状态含义：
- `READY`：能力已真实接通
- `DEGRADED`：能力已降级，但主流程仍可运行
- `FAILED`：核心依赖或本地权限存在问题，建议优先处理

常见情况：
- `Redis / Broker = DEGRADED`
  说明：推荐重建和搜索重建会回退成同步执行
  处理：启动 Redis，或使用 `docker compose up`
- `异步任务 = BROKER_ONLY`
  说明：Redis 可用，但没有在线 Celery worker
  处理：启动 `celery -A app.tasks.worker.celery_app worker --loglevel=info`
- `搜索索引 = DEGRADED`
  说明：OpenSearch 不可用，搜索已回退数据库
  处理：启动 OpenSearch 后，在后台执行一次“重建搜索索引”
- `媒体存储 = MINIO / DEGRADED`
  说明：对象存储配置未接通
  处理：检查 `MINIO_ENDPOINT`、bucket、账号密码，或先切回 `local`

## 演示建议

建议按下面顺序走一遍：
1. 管理员登录后台，先看 `/admin/platform`
2. 查看 `/admin/recommendations` 和治理工作台
3. 卖家上传带图片的新商品
4. 管理员审核商品
5. 买家搜索、聊天、收藏、下单、评价
6. 买家举报，卖家申诉，管理员复核
7. 回后台触发推荐重建和搜索重建，观察作业变化

## 收尾命令

```bash
docker compose down --remove-orphans
docker compose down -v
make docker-reset
```

如果这台机器没有 `docker` 命令，项目依然可以本地启动；只是平台运维台会把 Redis、异步任务、搜索索引显示为降级或未接通状态。
