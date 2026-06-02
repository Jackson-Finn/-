# Advanced Marketplace

一个基于 `Vue 3 + Vite + Pinia + Element Plus` 和 `FastAPI + SQLAlchemy + Celery` 的二手交易平台示例项目，包含搜索、推荐、实时聊天、通知、审核、举报、申诉和权限管理的基础实现。

当前版本已切换为 `MySQL + Alembic` 的数据库工作流：
- 应用启动不再动态建表或补列
- 数据库结构统一通过 `alembic upgrade head` 管理
- 后端测试默认运行在 MySQL 测试库上

## 默认演示账号

- 管理员：`admin@example.com` / `Admin123!`
- 审核员：`moderator@example.com` / `Mod123456!`
- 卖家：`seller@example.com` / `Seller123!`
- 买家：`buyer@example.com` / `Buyer123!`

## 本地开发

1. 准备环境变量

```bash
cp backend/.env.example backend/.env
```

2. 准备 MySQL

项目默认使用下面这条连接串：

```text
mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/advanced_marketplace?charset=utf8mb4
```

如果你本机已经有可用的 MySQL 8，可以先执行：

```sql
CREATE DATABASE IF NOT EXISTS advanced_marketplace CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'marketplace'@'127.0.0.1' IDENTIFIED BY 'marketplace';
GRANT ALL PRIVILEGES ON advanced_marketplace.* TO 'marketplace'@'127.0.0.1';
FLUSH PRIVILEGES;
```

3. 迁移数据库并启动后端

```bash
conda activate advanced-marketplace
make migrate
make api
```

4. 启动前端

```bash
make install-frontend
make frontend
```

本地常用地址：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- 健康检查：`http://localhost:8000/health`

## Docker Compose

如果你想一次拉起 MySQL、Redis、MinIO、OpenSearch、API、worker、前端和网关：

```bash
cp backend/.env.example backend/.env
docker compose up --detach --wait --wait-timeout 300
```

Compose 里的后端服务会在启动时自动执行：

```bash
alembic upgrade head
```

Docker 模式下的入口：
- 网关：`http://localhost:8080`
- API：`http://localhost:8000`
- 前端开发服务：`http://localhost:5173`
- MySQL（宿主机映射）：`127.0.0.1:3308`
- MinIO 控制台：`http://localhost:9001`
- OpenSearch：`http://localhost:9200`

## 测试

后端测试默认读取两个环境变量：

```text
TEST_DATABASE_ADMIN_URL
TEST_DATABASE_URL
```

默认值指向本机 `3306`。如果你的机器上 `3306` 已被别的 MySQL 占用，可以在运行测试前覆盖成别的端口，例如 `3307`：

```bash
export TEST_DATABASE_ADMIN_URL='mysql+pymysql://root:root@127.0.0.1:3307/mysql?charset=utf8mb4'
export TEST_DATABASE_URL='mysql+pymysql://marketplace:marketplace@127.0.0.1:3307/advanced_marketplace_test?charset=utf8mb4'
make test
```

## 常用命令

```bash
make migrate
make api
make frontend
make test
make build
make docker-up
make docker-down
make docker-logs
make docker-config
```

## 说明

- `backend/database/sql/` 下的 SQL 文件现在更适合作为参考资源；运行时以 `SQLAlchemy models + Alembic migrations` 为准。
- 本地默认使用 `STORAGE_BACKEND=local`，上传文件会写入 `backend/storage/uploads`。
- 容器模式会切到 `STORAGE_BACKEND=minio`。
- 搜索在 OpenSearch 不可用时会自动回退到数据库模式。
