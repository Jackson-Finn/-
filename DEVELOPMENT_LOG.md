# 开发日志

本文档记录 `Advanced Marketplace` 从环境准备、架构搭建到高级功能落地的主要开发进展，适合作为阶段汇报、课程答辩和后续维护参考。

## 阶段 1：开发环境与工程初始化

### 1.1 Miniconda 与虚拟环境
- 安装 `Miniconda` 到 `~/miniconda3`
- 创建项目独立环境 `advanced-marketplace`
- 修复 `zsh` 下的 `conda` 初始化，使登录 shell 和交互式 shell 都可直接使用
- 新增根目录 [environment.yml](/Users/yzj/vs-workspace/db-design/environment.yml:1)，统一管理 Python 与 Node.js 开发依赖

### 1.2 Git 与基础忽略规则
- 配置根目录 [`.gitignore`](/Users/yzj/vs-workspace/db-design/.gitignore:1)
- 忽略 `conda` 环境、Python 缓存、前端构建产物、日志、上传目录、编辑器文件、`.env` 和本地数据库文件

### 1.3 后端打包与依赖管理
- 新增 [backend/pyproject.toml](/Users/yzj/vs-workspace/db-design/backend/pyproject.toml:1)
- 统一后端依赖入口，支持在 conda 环境中直接 `pip install -e ./backend`
- 补齐 `fastapi`、`sqlalchemy`、`pydantic`、`email-validator` 等关键依赖

## 阶段 2：高级版架构骨架落地

### 2.1 总体技术栈升级
- 前端升级为 `Vue 3 + Vite + Pinia + Element Plus + ECharts`
- 后端升级为 `FastAPI + SQLAlchemy 2 + Pydantic 2`
- 基础设施预留 `Redis + Celery + MinIO + OpenSearch + Nginx + Docker Compose`

### 2.2 模块化单体结构
- 后端按域拆分为 `identity`、`catalog`、`trade`、`interaction`、`governance`、`intelligence`、`platform`
- 落地 `controllers/routes -> services -> repositories -> models` 分层
- 约束跨模块协作方式，避免直接跨仓储写表
- 引入内部事件发布机制，支撑推荐、通知、搜索同步、治理留痕等异步能力

### 2.3 核心工程入口
- 新增后端应用入口 [backend/app/main.py](/Users/yzj/vs-workspace/db-design/backend/app/main.py:1)
- 新增前端工程入口 [frontend/src/main.js](/Users/yzj/vs-workspace/db-design/frontend/src/main.js:1)
- 新增路由、状态管理、HTTP 客户端和布局骨架

## 阶段 3：数据库、种子数据与演示数据体系

### 3.1 SQL 初始化资源
- 新增 [backend/database/sql](/Users/yzj/vs-workspace/db-design/backend/database/sql:1)
- 补齐 `tables.sql`、`indexes.sql`、`views.sql`、`triggers.sql`、`seed_data.sql`、`init.sql`
- 固化核心业务表、治理表、推荐表、聊天表、通知表、媒体表与事件表

### 3.2 应用级种子数据
- 新增 [backend/app/core/seed.py](/Users/yzj/vs-workspace/db-design/backend/app/core/seed.py:1)
- 启动时自动生成默认账号、商品、订单、评价、聊天、举报、申诉、推荐快照等演示数据
- 让项目开箱即可进入可展示状态

### 3.3 安全与配置稳定性
- 调整密码哈希到更稳定的 `pbkdf2_sha256`，避免 `bcrypt` 兼容问题，见 [backend/app/core/security.py](/Users/yzj/vs-workspace/db-design/backend/app/core/security.py:1)
- 强化默认 `SECRET_KEY`，见 [backend/app/core/config.py](/Users/yzj/vs-workspace/db-design/backend/app/core/config.py:1)
- 新增 [backend/.env.example](/Users/yzj/vs-workspace/db-design/backend/.env.example:1)
- 修复配置解析对非标准环境值的兼容问题

## 阶段 4：核心业务闭环实现

### 4.1 身份与权限
- 实现登录、注册、当前用户信息查询
- 用户信息接口返回权限列表，前端可据此决定管理端入口和功能可见性
- 实现 RBAC 权限体系，支持管理员多角色、多权限点

### 4.2 商品与交易主链路
- 实现商品发布、审核、上架、商品详情、收藏、下单、确认收货、评价
- 打通完整演示路径：
  - 卖家发布商品
  - 管理员审核商品
  - 买家浏览、收藏、聊天、下单
  - 买家确认收货并评价

### 4.3 举报与申诉闭环
- 实现用户举报商品或对象
- 实现管理员处理举报
- 实现卖家发起申诉
- 实现管理员申诉复核
- 接入审核任务流和操作留痕，保证治理流程完整可追踪

## 阶段 5：智能化与高级功能落地

### 5.1 推荐系统
- 实现首页推荐和商品相关推荐接口
- 推荐结果从占位数据升级为真实商品数据
- 匿名用户也可访问首页推荐，登录用户可结合行为和演示快照得到更贴近场景的结果
- 推荐结果返回推荐原因，便于展示“可解释推荐”

### 5.2 搜索与联想
- 实现商品搜索接口
- 支持按关键词检索商品
- 增强搜索建议逻辑，从商品标题和标签生成联想词
- 前端首页接入联想搜索输入框，提升展示效果与交互真实感

### 5.3 AI 辅助能力
- 预留并接入 AI 接口分组
- 支持商品文案草稿、风险提示、聊天摘要等高级能力入口
- 商品详情页已接入聊天摘要能力，能直接展示“智能化增强”

### 5.4 实时通知与 WebSocket
- 落地全局实时连接管理，见 [frontend/src/App.vue](/Users/yzj/vs-workspace/db-design/frontend/src/App.vue:1)
- 新增 [frontend/src/stores/ui.js](/Users/yzj/vs-workspace/db-design/frontend/src/stores/ui.js:1)，统一维护通知列表、未读数、连接状态和实时事件
- 用户端和管理端布局均已接入通知状态
- 支持收到聊天或治理事件后刷新界面内容

## 阶段 6：前端联调与展示体验增强

### 6.1 用户端页面完善
- 完成首页、登录、注册、商品详情、发布商品、我的订单、收藏、个人中心等页面基础能力
- 首页改为真实商品流和真实推荐流，不再依赖静态占位
- 商品详情页支持：
  - 收藏
  - 下单
  - 聊天
  - 举报
  - 相关推荐
  - 聊天摘要

### 6.2 数据状态组件
- 新增 [frontend/src/components/DataStateCard.vue](/Users/yzj/vs-workspace/db-design/frontend/src/components/DataStateCard.vue:1)
- 为加载中、空态、错误态提供统一展示容器
- 减少页面散乱状态判断，提高可维护性

### 6.3 通知中心组件
- 新增 [frontend/src/components/NotificationCenter.vue](/Users/yzj/vs-workspace/db-design/frontend/src/components/NotificationCenter.vue:1)
- 将站内通知做成统一组件，接入布局层
- 支持未读数、列表查看和已读操作

## 阶段 7：后台治理工作台深化

### 7.1 仪表盘增强
- 管理后台 [Dashboard.vue](/Users/yzj/vs-workspace/db-design/frontend/src/views/admin/Dashboard.vue:1) 已接入统计概览、图表、审核任务、操作日志
- 支撑展示系统的治理、统计和运营视角

### 7.2 举报处理工作台
- 重构 [ReportManage.vue](/Users/yzj/vs-workspace/db-design/frontend/src/views/admin/ReportManage.vue:1)
- 管理员现在可以在同一界面查看：
  - 举报详情
  - 处理备注
  - 关联审核任务
  - 操作时间线
- 使“处理动作”从简单按钮升级为“上下文驱动决策”

### 7.3 申诉复核工作台
- 重构 [AppealManage.vue](/Users/yzj/vs-workspace/db-design/frontend/src/views/admin/AppealManage.vue:1)
- 支持联动查看原举报、申诉内容、复核备注、任务时间线和操作记录
- 更适合课程答辩中展示“治理闭环”和“审计留痕”

### 7.4 治理上下文接口
- 新增后台接口：
  - `GET /api/admin/reports/{report_id}/context`
  - `GET /api/admin/appeals/{appeal_id}/context`
- 接口返回举报或申诉实体、关联任务、操作时间线等完整上下文
- 同时补齐 `entity_type`、`entity_id` 等任务字段，保证前后端契约完整

### 7.5 操作日志增强
- 治理服务现在会把处理备注和操作者一起写入操作日志
- 提高后台时间线信息密度，方便排查、展示和后续扩展

## 阶段 8：测试、验证与开发流程完善

### 8.1 自动化测试
- 新增 smoke tests：[backend/tests/test_api_smoke.py](/Users/yzj/vs-workspace/db-design/backend/tests/test_api_smoke.py:1)
- 新增端到端业务测试：[backend/tests/test_e2e_flow.py](/Users/yzj/vs-workspace/db-design/backend/tests/test_e2e_flow.py:1)
- 覆盖以下关键流程：
  - 健康检查
  - 默认账号登录
  - 商品列表与搜索
  - 匿名首页推荐
  - 商品发布与审核
  - 下单、聊天、收货、评价
  - 举报、申诉、管理员复核
  - 后台治理上下文接口

### 8.2 本地启动与快捷命令
- 新增根目录 [Makefile](/Users/yzj/vs-workspace/db-design/Makefile:1)
- 支持 `make api`、`make frontend`、`make test`、`make build`、`make demo`
- 降低本地演示和联调门槛

### 8.3 真实联调验证
- 实际拉起过本地 `uvicorn` 和 `vite` 开发服务
- 实测通过：
  - `/health`
  - `/api/products`
  - `/api/admin/statistics/overview`
  - `/api/recommendations/home`
  - `/api/notifications`
- 后端测试当前通过：`5 passed`
- 前端构建当前通过：`npm run build`

## 阶段 9：基础设施与容器化准备

### 9.1 Docker Compose
- 新增 [docker-compose.yml](/Users/yzj/vs-workspace/db-design/docker-compose.yml:1)
- 编排 API、worker、frontend、Redis、MinIO、OpenSearch、Nginx
- 增强健康检查、依赖顺序和数据卷配置

### 9.2 Nginx 网关
- 新增 [infra/nginx/default.conf](/Users/yzj/vs-workspace/db-design/infra/nginx/default.conf:1)
- 提供统一网关入口，支撑前后端和基础设施协同演示

### 9.3 文档与运行说明
- 更新 [README.md](/Users/yzj/vs-workspace/db-design/README.md:1)
- 补充默认账号、SQL 资源、本地开发、Docker 启动、快捷命令和建议演示路径

### 9.4 当前已知限制
- 当前机器未安装 `docker`，因此尚未做 `docker compose up` 的本机实跑验证
- 前端构建存在较大的 `charts` 和 `ui` chunk warning，主要由 `ECharts` 与 `Element Plus` 引起，但不影响开发与演示

## 当前阶段结论

项目已经从“高级版规划”推进到“可运行、可联调、可演示、可测试”的阶段，具备以下特征：
- 有完整的前后端骨架和模块边界
- 有默认演示数据和可直接使用的账号
- 有商品、交易、聊天、通知、推荐、举报、申诉、权限等核心能力
- 有后台治理工作台和操作留痕
- 有自动化测试和基础容器化方案

## 建议的后续开发方向

如果继续迭代，最值得优先推进的是：

1. 推荐解释工作台
- 在后台增加“推荐素材来源”和“推荐命中原因”可视化页面

2. 搜索与索引实跑
- 真正接通 OpenSearch，同步索引与联想词热度统计

3. 媒体上传链路
- 接通 MinIO，补齐图片上传、回填、缩略图生成和审核状态

4. 异步任务链
- 让 Celery 真实承担推荐刷新、索引重建、媒体处理和 AI 任务

5. 前端性能优化
- 对 `ECharts` 和大型 UI 依赖进行拆包与按需加载
