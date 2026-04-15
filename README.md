<<<<<<< HEAD
# Advanced Marketplace

一个基于 `Vue 3 + Vite + Pinia + Element Plus` 和 `FastAPI + SQLAlchemy + Celery` 的高级版二手交易平台骨架，包含搜索、推荐、实时聊天、通知、审核、举报、申诉和权限管理的基础实现。

完整开发过程记录见 [DEVELOPMENT_LOG.md](/Users/yzj/vs-workspace/db-design/DEVELOPMENT_LOG.md:1)。
联调与排障手册见 [RUNBOOK.md](/Users/yzj/vs-workspace/db-design/RUNBOOK.md:1)。

当前前端已启用 Element Plus 按需引入与图表拆包，构建体积相比早期版本更稳定，适合继续往演示和交付收口。

## 默认演示账号

- 管理员：`admin@example.com` / `Admin123!`
- 审核员：`moderator@example.com` / `Mod123456!`
- 卖家：`seller@example.com` / `Seller123!`
- 买家：`buyer@example.com` / `Buyer123!`

## SQL 资源

SQL 初始化资源位于 [backend/database/sql](/Users/yzj/vs-workspace/db-design/backend/database/sql:1)：

- `tables.sql`：核心建表
- `indexes.sql`：索引
- `views.sql`：演示视图
- `triggers.sql`：更新时间与日志触发器
- `seed_data.sql`：静态演示数据
- `init.sql`：执行顺序说明

## 本地开发

1. 激活环境

```bash
conda activate advanced-marketplace
```

2. 启动后端

```bash
cd backend
uvicorn app.main:app --reload
```

3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

4. 可选：启动整套基础设施

```bash
docker compose up --detach --wait --wait-timeout 300
```

说明：
- 本地默认使用 `STORAGE_BACKEND=local`，图片会落到 `backend/storage/uploads`
- 本地开发与 `docker compose` 现在默认共用 `backend/data/advanced_marketplace.db`，避免收藏、浏览记录分散到两份 SQLite
- `docker compose` 环境会自动切到 `STORAGE_BACKEND=minio`
- 在容器模式下，商品图片通过 `http://localhost:8080/uploads/...` 由 Nginx 转发到 MinIO bucket
- 上传完成后会自动生成 `preview` 和 `compressed` 变体，商品卡片默认使用预览图
- 搜索默认支持 OpenSearch，同步失败时会自动回退到数据库搜索，不会阻塞主业务链路
- 推荐重建和搜索重建已接入 Celery 任务；当本地没有 Redis/Celery 时，会自动回退到同步执行
- `/admin/platform` 会直接显示数据库、Redis、异步任务、媒体存储和搜索索引的就绪度与降级原因

## 快捷命令

根目录已经提供 [Makefile](/Users/yzj/vs-workspace/db-design/Makefile:1)：

```bash
make api
make frontend
make test
make build
make demo
make docker-pull
make docker-up
make docker-down
make docker-config
make docker-smoke
make docker-reset
```

## Docker 启动说明

- 网关入口：`http://localhost:8080`
- 后端接口：`http://localhost:8000`
- 前端开发服务：`http://localhost:5173`
- MinIO 控制台：`http://localhost:9001`
- OpenSearch：`http://localhost:9200`
- Redis：`localhost:6379`

compose 默认会同时拉起 API、worker、前端、Redis、MinIO、OpenSearch 和 Nginx。API、前端和网关都配置了健康检查，`docker compose up --wait` 会等到核心服务就绪后再返回。
对象存储默认走 MinIO，并已在应用启动时自动确保 bucket 存在并设置公开读策略，便于直接展示商品图片。
如果你之前已经把本地数据写进旧路径 `backend/advanced_marketplace.db`，应用启动时会自动迁移到 `backend/data/advanced_marketplace.db`。
第一次启动建议先执行一次 `make docker-pull`，尤其是 `OpenSearch` 镜像较大，首次拉取会明显更久。
服务起来后，可以用 `make docker-smoke` 快速验证网关、API、商品列表、推荐、MinIO 和 OpenSearch 是否可用。

如果你是在 Linux 上跑 OpenSearch，通常还需要提前执行一次：

```bash
sudo sysctl -w vm.max_map_count=262144
```

如果要重置本地数据卷，可以使用：

```bash
docker compose down -v
```

## 建议演示路径

1. 用管理员账号登录，进入 `/admin` 查看概览、待审核商品、举报和申诉队列。
2. 在 `/admin/recommendations` 查看推荐素材流、推荐快照解释、推荐任务和 AI 日志。
3. 在 `/admin/platform` 查看事件分布、作业状态、失败任务、搜索索引状态和当前存储后端。
4. 用卖家账号登录，进入“发布商品”页，使用 AI 生成文案、上传商品图片并提交新商品。
5. 切回管理员账号审核通过商品。
6. 用买家账号打开商品详情页，发起聊天、收藏、下单、确认收货并评价。
7. 用买家账号提交举报，再用卖家账号提交申诉，最后由管理员完成复核。
8. 回到后台查看统计、推荐重建和搜索重建入口。
9. 打开 `/admin/platform`，确认平台依赖状态、查看排障手册和最近作业记录。
=======
# -
>>>>>>> df6d64ab930dcbe2716af5403be6ccc59ab23e7a
