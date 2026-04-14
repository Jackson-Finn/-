# Advanced Marketplace

一个基于 `Vue 3 + Vite + Pinia + Element Plus` 和 `FastAPI + SQLAlchemy + Celery` 的高级版二手交易平台骨架，包含搜索、推荐、实时聊天、通知、审核、举报、申诉和权限管理的基础实现。

完整开发过程记录见 [DEVELOPMENT_LOG.md](/Users/yzj/vs-workspace/db-design/DEVELOPMENT_LOG.md:1)。

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

## 快捷命令

根目录已经提供 [Makefile](/Users/yzj/vs-workspace/db-design/Makefile:1)：

```bash
make api
make frontend
make test
make build
make demo
make docker-up
make docker-down
make docker-config
```

## Docker 启动说明

- 网关入口：`http://localhost:8080`
- 后端接口：`http://localhost:8000`
- 前端开发服务：`http://localhost:5173`
- MinIO 控制台：`http://localhost:9001`
- OpenSearch：`http://localhost:9200`
- Redis：`localhost:6379`

compose 默认会同时拉起 API、worker、前端、Redis、MinIO、OpenSearch 和 Nginx。API、前端和网关都配置了健康检查，`docker compose up --wait` 会等到核心服务就绪后再返回。

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
2. 用卖家账号登录，进入“发布商品”页，使用 AI 生成文案并提交新商品。
3. 切回管理员账号审核通过商品。
4. 用买家账号打开商品详情页，发起聊天、收藏、下单、确认收货并评价。
5. 用买家账号提交举报，再用卖家账号提交申诉，最后由管理员完成复核。
6. 回到后台查看统计、推荐重建和搜索重建入口。
