# 测试文档 (Test Documentation)

> Advanced Marketplace 后端测试套件
> FastAPI + SQLAlchemy + Pytest

---

## 1. 测试环境

### 1.1 技术栈

| 组件 | 技术 | 版本要求 |
|------|------|----------|
| 测试框架 | pytest | >= 8.3.3 |
| HTTP 客户端 | fastapi.testclient | (随 FastAPI 安装) |
| 数据库 | SQLite (测试临时文件) | 内置 |
| ORM | SQLAlchemy | >= 2.0.36 |
| Python | | >= 3.11 |

### 1.2 测试配置

测试通过设置环境变量 `DATABASE_URL` 来使用独立的临时 SQLite 数据库文件，确保每次测试运行互不干扰。

```python
# 测试专用数据库 URL 示例
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_xxxxxx/test.db"
```

pytest 配置 (`pyproject.toml`):

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

### 1.3 依赖安装

```bash
# 安装后端及开发依赖
cd backend
pip install -e ".[dev]"

# 或通过 Conda
make install
```

### 1.4 运行测试

```bash
# 标准运行（所有测试，简洁输出）
make test

# 或直接运行 pytest
cd backend
pytest -q

# 运行所有测试（详细输出）
pytest -v

# 运行所有测试（详细输出 + 本地变量展示）
pytest -vv

# 运行特定文件
pytest tests/test_api_smoke.py -v
pytest tests/test_e2e_flow.py -v

# 运行特定测试函数
pytest tests/test_e2e_flow.py::test_marketplace_core_flow -v

# 在测试失败时立即停止
pytest -x

# 运行匹配关键词的测试
pytest -k "chat" -v
pytest -k "order" -v

# 生成覆盖率报告（需安装 pytest-cov）
pytest --cov=app --cov-report=term-missing
```

---

## 2. 测试文件结构

```
backend/tests/
├── conftest.py              # pytest fixtures（可选）
├── test_api_smoke.py        # API 冒烟测试（14 个测试函数）
└── test_e2e_flow.py         # 端到端流程测试（1 个测试函数）
```

### 2.1 `test_api_smoke.py` — 冒烟测试套件

覆盖系统各核心模块的健康检查和基本功能验证：

| 测试函数 | 测试内容 |
|----------|----------|
| `test_health_endpoint` | 健康检查端点返回 `{"status": "ok"}` |
| `test_seeded_admin_login_and_me` | 管理员登录 → 获取 JWT → 调用 `/api/auth/me` 验证身份与权限 |
| `test_seeded_product_listing_and_search` | 商品列表 >= 3 条；关键词搜索 "Switch" 能命中结果 |
| `test_anonymous_home_recommendations` | 匿名用户首页推荐接口正常返回 |
| `test_admin_recommendation_workbench` | 管理员推荐工作台返回材料数量和图表数据 |
| `test_admin_search_reindex_route` | 搜索重建路由支持多模式（database-fallback/opensearch/celery/sync-fallback） |
| `test_admin_recommendation_rebuild_route` | 推荐重建路由返回任务状态和 job_id |
| `test_admin_platform_ops_route` | 平台运维面板返回就绪检查、搜索模式、运行信息、运行手册 |
| `test_admin_product_list_and_detail_context` | 管理员商品列表支持 audit_status 过滤；详情包含 tasks、operations |
| `test_request_changes_and_resubmit_flow` | 管理员要求修改 → 卖家更新商品 → 卖家重新提交 → 审核状态回退为 PENDING |
| `test_my_products_handles_legacy_null_tags` | 历史遗留的 `tags=NULL` 数据能正常序列化（不报错） |
| `test_my_products_route_is_not_shadowed_by_product_detail` | `/api/products/mine` 路由未被 `/api/products/{id}` 路由覆盖；卖家/买家返回正确子集 |
| `test_public_seller_profile_and_products` | 公开卖家资料接口返回完整信息（display_name、avatar、trust_score 等） |

### 2.2 `test_e2e_flow.py` — 端到端流程测试

验证从商品发布到平台治理的完整业务闭环：

```
test_marketplace_core_flow
├── 1. 媒体上传
│   ├── POST /api/media/upload-init        → 获取 asset_id
│   ├── POST /api/media/{id}/file          → 上传文件，stage="uploaded"
│   └── POST /api/media/complete           → 完成上传，生成 preview + compressed 变体
│
├── 2. 商品发布
│   ├── POST /api/products                 → 创建商品（status=PENDING，未上架）
│   ├── GET  /api/admin/products/pending  → 管理员待审核列表包含该商品
│   └── GET  /api/admin/products          → 关键词过滤能命中
│
├── 3. 管理员审核流程
│   ├── GET  /api/admin/products/{id}      → 审核前上下文
│   ├── POST /api/admin/products/{id}/audit (REQUEST_CHANGES) → 要求修改
│   ├── POST /api/products/{id}/resubmit  → 卖家重新提交
│   └── POST /api/admin/products/{id}/audit (APPROVE)       → 审核通过
│
├── 4. 订单流程
│   ├── POST /api/orders                  → 买家下单（status=CREATED）
│   └── POST /api/orders/{id}/confirm     → 买家确认收货（status=COMPLETED）
│
├── 5. 评价流程
│   ├── POST /api/reviews                 → 首次评价（rating=5）
│   ├── GET  /api/orders                 → 订单包含 can_review_product=True 和已提交的评价
│   ├── POST /api/reviews                 → 修改评价（rating=3）
│   └── GET  /api/reviews/products/{id}   → 商品评价列表返回最新评价
│
├── 6. 即时通讯
│   ├── POST /api/chat/sessions           → 买家发起会话（与卖家）
│   ├── POST /api/chat/sessions           → 再次发起同一会话，返回同一 session_id（幂等性）
│   └── POST /api/chat/sessions/{id}/messages → 发送消息
│
├── 7. 举报与申诉
│   ├── POST /api/reports                 → 买家举报商品
│   ├── POST /api/admin/reports/{id}/process    → 管理员处理举报（approved=True）
│   ├── GET  /api/admin/reports/{id}/context    → 举报详情上下文（包含 tasks 和 operations）
│   ├── POST /api/appeals                 → 卖家对举报提起申诉
│   ├── POST /api/admin/appeals/{id}/review    → 管理员审核申诉（approved=True）
│   └── GET  /api/admin/appeals/{id}/context   → 申诉详情上下文
│
├── 8. 推荐与历史
│   ├── GET  /api/recommendations/products/{id}/related → 相关商品推荐
│   ├── POST /api/history/products/{id}/view    → 记录浏览历史（去重：多次浏览同一商品返回同一 id）
│   └── GET  /api/history/recent             → 历史列表只包含一条该商品记录
│
└── 9. 管理员下架
    └── POST /api/admin/products/{id}/off-shelf → 管理员强制下架（product_status=OFF_SHELF）
```

---

## 3. 测试夹具 (Fixtures)

### 3.1 客户端构建器 (`build_client`)

每个测试函数通过 `tmp_path` fixture 获取唯一的临时目录用于存放 SQLite 数据库文件，确保测试之间完全隔离。

```python
def build_client(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    # 清除已导入的 app 模块缓存，强制重新导入
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    module = importlib.import_module("app.main")
    return TestClient(module.app)
```

关键机制：
- **隔离数据库**: 每个测试函数分配独立的 SQLite 文件
- **模块重载**: 清除 `sys.modules` 中的 `app.*` 缓存，确保 `app.main` 重新初始化（包括 lifespan 中的 seed_defaults）
- **TestClient 上下文管理**: 使用 `with` 语句确保连接正确关闭

### 3.2 认证辅助函数

```python
def login(client: TestClient, email: str, password: str) -> str:
    """登录并返回 access_token"""
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]

def auth_header(token: str) -> dict[str, str]:
    """将 token 转换为 Authorization 请求头"""
    return {"Authorization": f"Bearer {token}"}
```

### 3.3 预置测试数据

所有测试共享由 `app/core/seed.py` 中的 `seed_defaults()` 函数在应用启动时自动植入的种子数据：

| 数据 | 数量 | 登录凭证 |
|------|------|----------|
| 管理员 | 1 | admin@example.com / Admin123! |
| 仲裁员 | 1 | moderator@example.com / Mod123456! |
| 卖家 | 2 | seller@example.com / Seller123! <br> studio@example.com / Studio123! <br> home@example.com / Home123!! |
| 买家 | 1 | buyer@example.com / Buyer123! |
| 商品 | 8+ | 含 tags JSON 字段（keywords、specs、trust_snapshot 等） |
| 评价 | 若干 | rating 1-5，含 product_review 和 seller_review |
| 聊天会话 | 若干 | 买家与卖家之间的真实对话 |
| 收藏/历史 | 若干 | 用于推荐系统测试 |

### 3.4 自定义 fixtures (conftest.py)

如需扩展，可在 `tests/conftest.py` 中定义：

```python
import pytest
from fastapi.testclient import TestClient

from tests.test_api_smoke import build_client

@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return build_client(tmp_path)

@pytest.fixture
def admin_token(client: TestClient) -> str:
    return client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    ).json()["data"]["access_token"]

@pytest.fixture
def seller_token(client: TestClient) -> str:
    return client.post(
        "/api/auth/login",
        json={"email": "seller@example.com", "password": "Seller123!"},
    ).json()["data"]["access_token"]

@pytest.fixture
def buyer_token(client: TestClient) -> str:
    return client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "Buyer123!"},
    ).json()["data"]["access_token"]
```

---

## 4. 逐模块测试用例详解

### 4.1 认证与身份 (`auth`)

| 用例 | 方法 + 路径 | 前置条件 | 验证点 |
|------|------------|----------|--------|
| 注册新用户 | POST /api/auth/register | 无 | 邮箱格式验证、密码强度、返回 JWT |
| 登录 | POST /api/auth/login | 已注册用户 | 返回 access_token 和用户信息 |
| 获取当前用户 | GET /api/auth/me | 持有 JWT | 返回用户详情 + 完整 permissions 列表 |
| 无效凭证 | POST /api/auth/login | 错误密码 | HTTP 401，message 包含认证失败信息 |
| 过期 token | GET /api/auth/me | 伪造 token | HTTP 401 或 403 |
| 权限检查 | GET /api/admin/... | 无 admin 权限用户 | HTTP 403 Forbidden |

> **RBAC 权限树**:
> - `ADMIN` → 全部权限
> - `MODERATOR` → `product.audit` + `report.review` + `appeal.review`
> - 普通用户 → 无管理端权限

### 4.2 商品管理 (`products`)

| 用例 | 方法 + 路径 | 角色 | 验证点 |
|------|------------|------|--------|
| 浏览商品列表 | GET /api/products | 公开 | 只返回 APPROVED + ACTIVE 商品 |
| 浏览我的商品 | GET /api/products/mine | 卖家 | 只返回当前卖家的商品 |
| 商品详情 | GET /api/products/{id} | 公开 | 包含 images、seller、category |
| 创建商品 | POST /api/products | 卖家 | status=PENDING，生成 ProductImage 关联 |
| 更新商品 | PUT /api/products/{id} | 卖家本人 | 非 PENDING 状态不可更新 |
| 下架商品 | POST /api/products/{id}/off-shelf | 卖家 | product_status → OFF_SHELF |
| 重新提交 | POST /api/products/{id}/resubmit | 卖家 | 仅 CHANGES_REQUESTED 状态可用 |
| 空 tags 处理 | GET /api/products/mine | 卖家 | tags=NULL 的历史数据返回空 dict 而非报错 |

**商品状态机**:
```
[创建] → PENDING
         ↓
    APPROVED ←→ CHANGES_REQUESTED
         ↓              ↓
     ACTIVE    [更新后 resubmit] → PENDING
         ↓
   OFF_SHELF
```

### 4.3 订单与评价 (`orders`, `reviews`)

| 用例 | 方法 + 路径 | 角色 | 验证点 |
|------|------------|------|--------|
| 创建订单 | POST /api/orders | 买家 | status=CREATED，idempotency via request_id |
| 取消订单 | POST /api/orders/{id}/cancel | 买家/卖家 | status→CANCELLED（仅 CREATED 可取消） |
| 确认收货 | POST /api/orders/{id}/confirm | 买家 | status→COMPLETED |
| 提交评价 | POST /api/reviews | 买家 | 创建 product_review（order_id 唯一约束） |
| 更新评价 | POST /api/reviews | 买家 | 替换已有评价内容（upsert 语义） |
| 商品评价列表 | GET /api/reviews/products/{id} | 公开 | 按时间倒序返回所有评价 |
| 订单详情含评价 | GET /api/orders | 买家 | can_review_product、product_review 字段 |

**评价约束**:
- 每笔订单每个用户最多提交一条 product_review 和一条 seller_review
- rating 范围 1-5
- 已完成订单（COMPLETED）才可评价

### 4.4 搜索与推荐 (`search`, `recommendations`)

| 用例 | 方法 + 路径 | 角色 | 验证点 |
|------|------------|------|--------|
| 关键词搜索 | GET /api/search/products | 公开 | OpenSearch 全文检索，降级为 SQL LIKE |
| 首页推荐 | GET /api/recommendations/home | 公开 | 基于订单/评价/浏览历史的聚合推荐 |
| 相关商品 | GET /api/recommendations/products/{id}/related | 公开 | 同类别/同标签相似商品 |
| 搜索重建 | POST /api/admin/search/reindex | 管理员 | 触发 Celery 任务或同步重建 |
| 推荐重建 | POST /api/admin/recommendations/rebuild | 管理员 | 重新聚合历史数据生成推荐材料 |
| 推荐工作台 | GET /api/admin/recommendations/workbench | 管理员 | 查看材料统计和分布图表 |

**搜索降级路径**:
```
OpenSearch 可用 → 全文检索（权重: title 3x, description 1x）
        ↓ 不可用
SQLAlchemy LIKE 查询（数据库降级）
```

**推荐流过滤策略**（2026-04-23 修复）:
- 所有推荐接口（首页推荐、相关商品推荐）**仅返回已审核通过且状态为 ACTIVE 的商品**
- `popular_products` 在数据库层过滤 `audit_status == APPROVED` + `product_status == ACTIVE`
- `recommend_related` 同样在内存层过滤 `audit_status == APPROVED` + `product_status == ACTIVE`
- `_hydrate_recommendation_items`（从快照加载推荐结果时）也做同样的状态校验，防止快照中引用的商品在后续被下架后仍出现在推荐中

### 4.5 收藏与历史 (`favorites`, `history`)

| 用例 | 方法 + 路径 | 验证点 |
|------|------------|--------|
| 添加收藏 | POST /api/favorites | product_id + user_id 唯一约束 |
| 移除收藏 | DELETE /api/favorites/{id} | 幂等：不存在时不报错 |
| 收藏列表 | GET /api/favorites | 返回商品详情 |
| 记录浏览 | POST /api/history/products/{id}/view | 去重：同一用户对同一商品多次浏览只产生一条记录 |
| 浏览历史 | GET /api/history/recent | 按时间倒序 |

### 4.6 即时通讯 (`chat`)

| 用例 | 方法 + 路径 | 验证点 |
|------|------------|--------|
| 创建会话 | POST /api/chat/sessions | 同一买家+卖家+商品 幂等返回同一 session_id |
| 发送消息 | POST /api/chat/sessions/{id}/messages | 返回消息详情含 sender_id |
| 获取消息 | GET /api/chat/sessions/{id}/messages | 分页支持，按时间正序 |
| 会话列表 | GET /api/chat/sessions | 返回关联商品和最后一条消息预览 |
| WebSocket | WS /api/ws?user_id=X | 实时消息推送（需独立测试连接） |

### 4.7 通知 (`notifications`)

| 用例 | 方法 + 路径 | 验证点 |
|------|------------|--------|
| 获取通知 | GET /api/notifications | 返回用户所有通知（未读优先） |
| 标记已读 | POST /api/notifications/mark-read | 批量标记支持 |
| 广播通知 | POST /api/admin/notifications | 管理员向全站用户广播 |
| 广播列表 | GET /api/admin/notifications | 查看历史广播记录 |

### 4.8 内容治理 (`governance`)

| 用例 | 方法 + 路径 | 验证点 |
|------|------------|--------|
| 举报商品 | POST /api/reports | 记录 reporter_id、target_type、reason |
| 处理举报 | POST /api/admin/reports/{id}/process | approved=True/False，记录 note |
| 举报上下文 | GET /api/admin/reports/{id}/context | 返回关联 tasks 和 operations 日志 |
| 申诉 | POST /api/appeals | 卖家对已处理举报提起申诉（关联 report_id） |
| 审核申诉 | POST /api/admin/appeals/{id}/review | approved=True/False |
| 申诉上下文 | GET /api/admin/appeals/{id}/context | 包含原始举报、申诉内容、相关操作记录 |

**举报状态机**:
```
PENDING → PROCESSED (approved=True/False)
              ↓
         APPEALED (卖家申诉)
              ↓
         REVIEWED (管理员审核)
```

### 4.9 管理员运营 (`admin`)

| 用例 | 方法 + 路径 | 验证点 |
|------|------------|--------|
| 仪表盘统计 | GET /api/admin/statistics/overview | 用户数、商品数、订单数、举报数 |
| 图表数据 | GET /api/admin/statistics/charts | ECharts 兼容的时序/分布数据 |
| 待审核队列 | GET /api/admin/products/pending | audit_status=PENDING 的商品列表 |
| 商品详情（管理） | GET /api/admin/products/{id} | 包含 tasks、operations、reports |
| 审核操作 | POST /api/admin/products/{id}/audit | APPROVE / REJECT / REQUEST_CHANGES |
| 管理员下架 | POST /api/admin/products/{id}/off-shelf | 强制下架，记录 note |
| 任务队列 | GET /api/admin/audit/tasks | audit task 列表（task_type 分组） |
| 任务决策 | POST /api/admin/audit/tasks/{id}/decision | 更新 task status |
| 操作日志 | GET /api/admin/operations | 分页查看所有管理操作记录 |
| 平台健康 | GET /api/admin/platform/ops | readiness checks（database/redis/opensearch/minio） |
| 访问控制 | GET /api/admin/users <br> GET /api/admin/roles <br> GET /api/admin/permissions | 列出所有用户/角色/权限 |
| 分配角色 | POST /api/admin/users/{id}/roles | 为用户分配/撤销角色 |

---

## 5. 测试数据设计

### 5.1 种子数据 (`seed_defaults`)

`app/core/seed.py` 中的 `seed_defaults()` 在每次应用启动时（lifespan）执行，向数据库写入完整的演示数据：

```
角色 (2): ADMIN, MODERATOR
权限 (6): product.audit, report.review, appeal.review,
          recommendation.manage, search.manage, notification.manage
用户 (6): admin, moderator, seller(林川), seller(工作室), seller(家居), buyer
分类 (4): 数码, 图书, 家居, 潮玩
商品 (8+): 含完整 tags JSON（keywords/sections/specs/delivery/trust/risk）
评价: 多条，rating 1-5，含 product_review 和 seller_review
订单: 已完成订单（支持推荐系统）
聊天: 买卖双方真实会话
收藏/历史: 用于推荐系统计算
推荐材料: ORDER / REVIEW / HISTORY 三类
```

### 5.2 测试隔离策略

| 策略 | 实现方式 |
|------|----------|
| 数据库隔离 | 每个测试函数使用 `tmp_path` 创建独立 SQLite 文件 |
| 模块重载 | `sys.modules` 清除 `app.*` 缓存，强制 `app.main` 重新初始化 |
| 数据隔离 | seed_defaults() 在独立数据库上重新执行，不依赖外部数据 |
| 会话隔离 | TestClient 在 `with` 块中自动管理连接生命周期 |
| 并发安全 | SQLite 单 writer，无并发写入冲突 |

---

## 6. CI/CD 集成建议

### 6.1 GitHub Actions 示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          cd backend
          pytest -q --tb=short

      - name: Upload coverage
        if: always()
        run: |
          cd backend
          pytest --cov=app --cov-report=xml || true
      - uses: codecov/codecov-action@v4
        if: always()
```

### 6.2 本地预提交钩子

```bash
# .git/hooks/pre-commit
#!/bin/sh
cd backend && pytest -q
```

---

## 7. 测试覆盖范围总结

| 模块 | 单元/集成/E2E | 覆盖状态 |
|------|-------------|----------|
| 认证与授权 | 集成 | ✅ 核心路径已覆盖 |
| 商品管理 | 集成 | ✅ CRUD + 审核流程已覆盖 |
| 订单与评价 | E2E | ✅ 完整生命周期已覆盖 |
| 搜索与推荐 | 集成 | ✅ 推荐工作台 + 搜索重建已覆盖；推荐流仅展示 APPROVED+ACTIVE 商品 |
| 即时通讯 | E2E | ✅ 会话 + 消息已覆盖 |
| 收藏与历史 | 集成 | ✅ 去重逻辑已覆盖 |
| 通知系统 | 集成 | ✅ 广播 + 标记已读已覆盖 |
| 内容治理 | E2E | ✅ 举报 + 申诉完整闭环已覆盖 |
| 管理员运营 | 集成 | ✅ 仪表盘 + 健康检查 + 访问控制已覆盖 |
| 媒体上传 | E2E | ✅ 三阶段上传 + 缩略图生成已覆盖 |
| WebSocket | 手动 | ⚠️ 需独立 WebSocket 客户端测试 |
| OpenSearch | 降级覆盖 | ✅ 降级路径已测试 |
| Celery 任务 | 降级覆盖 | ✅ 同步降级已测试 |
| MinIO 存储 | 降级覆盖 | ✅ local 降级已测试 |

---

## 8. 常见问题 (FAQ)

**Q: 测试运行时 `seed_defaults` 报错怎么办？**
A: 检查 `DATABASE_URL` 是否正确指向了可写的临时路径。确保 `tmp_path` fixture 正常工作（pytest 内置，无需额外安装）。

**Q: 如何在调试模式下运行单个测试？**
A: 使用 `pytest tests/test_e2e_flow.py::test_marketplace_core_flow -vv -s` （`-s` 输出 print 语句）。

**Q: 测试数据库文件在哪里？**
A: 由 pytest 的 `tmp_path` fixture 管理，通常在 `/tmp/pytest-...` 目录下。每次测试结束后自动清理。

**Q: 如何添加新的测试用例？**
A: 在 `tests/test_api_smoke.py` 或 `tests/test_e2e_flow.py` 中添加新的测试函数。参考现有函数的 `build_client` 用法，使用 `login()` 和 `auth_header()` 辅助函数处理认证。

**Q: 测试通过但生产环境有问题？**
A: 注意测试使用 SQLite 而生产可能使用 PostgreSQL/MySQL。关注 SQLAlchemy ORM 兼容性，避免使用 SQLite 特定语法（如 `GENERATED` 列、`RETURNING` 语法差异）。应用层逻辑无差别。

---

*文档生成时间: 2026-04-23*
*最后更新: 随代码同步维护*
