# 数据库对象说明

当前项目运行在 `MySQL 8 + Alembic` 上。除基础数据表外，本版本补充了课程作业常见的数据库对象，并让它们参与真实运行链路。

## 序列机制

MySQL 没有像 Oracle / PostgreSQL 那样默认使用独立 `SEQUENCE` 对象。本项目采用 `AUTO_INCREMENT` 作为主键序列生成机制，典型表包括：

- `users.id`
- `products.id`
- `orders.id`
- `reports.id`
- `audit_tasks.id`

这部分可以在课程报告里说明为“使用 MySQL 自增机制实现序列功能”。

## 视图

### `vw_active_product_catalog`

用途：

- 聚合 `products`、`users`、`categories`、`product_images`
- 输出商品标题、价格、成色、卖家、分类、封面图、展示状态
- 当前已接入商品搜索链路，`/api/search/products` 通过该视图检索商品摘要

### `vw_seller_operational_summary`

用途：

- 聚合 `users`、`products`、`orders`、`reviews`、`reports`
- 输出卖家总商品数、在售数、成交数、平均评分、举报量、信任等级
- 当前已接入卖家公开资料页，`/api/users/{id}` 会优先读取该视图

### `vw_admin_risk_overview`

用途：

- 聚合 `reports`、`appeals`、`audit_tasks`
- 输出待处理举报、待复核申诉、待办审核任务等治理数据
- 当前已接入后台概览与图表统计，`/api/admin/statistics/overview` 等接口会读取该视图

## 存储函数

### `fn_product_display_status(audit_status, product_status, stock)`

用途：

- 统一计算商品展示状态
- 避免前后台分别拼接 `APPROVED / ACTIVE / OFF_SHELF / SOLD_OUT` 逻辑
- 当前由 `vw_active_product_catalog` 调用

### `fn_seller_trust_level(completed_orders, average_rating, report_count)`

用途：

- 统一评估卖家信任等级
- 输出 `HIGH / MEDIUM / LOW`
- 当前由 `vw_seller_operational_summary` 调用

## 触发器

### `trg_reports_after_insert_audit_task`

触发时机：

- `AFTER INSERT ON reports`

用途：

- 当新举报以 `PENDING` 状态写入时，自动生成一条 `audit_tasks`
- 体现数据库层对治理待办的自动入队能力

### `trg_reports_after_insert_operation_log`

触发时机：

- `AFTER INSERT ON reports`

用途：

- 当新举报以 `PENDING` 状态写入时，自动生成一条 `operation_logs`
- 体现数据库层对治理审计链路的补充能力

## 约束

本版本新增了以下数据质量约束：

- `ck_products_price_non_negative`
- `ck_products_stock_non_negative`
- `ck_reviews_rating_range`
- `ck_order_items_quantity_positive`
- `uq_reviews_order_review_type`

这些约束分别用于限制商品价格、库存、评分范围、订单数量，以及防止同一订单同类评价重复写入。

## 索引

本版本新增了以下业务导向索引：

- `ix_products_audit_status_product_status_updated_at`
- `ix_products_category_status_price`
- `ix_orders_buyer_status_created_at`
- `ix_reports_status_created_at`
- `ix_audit_tasks_entity_status_created_at`
- `ix_reviews_product_created_at`

它们分别服务于商品流筛选、卖家订单查询、治理任务处理和评价读取。

## 建议截图清单

如果你需要交作业截图，建议按这套顺序准备：

- 数据库对象树总览
- 三个视图定义
- 两个函数定义
- 两个触发器定义
- 约束与索引列表
- `SELECT * FROM vw_active_product_catalog LIMIT 5;`
- `SELECT * FROM vw_seller_operational_summary;`
- `SELECT * FROM vw_admin_risk_overview;`
- 插入一条 `reports` 后，查看 `audit_tasks` 新增记录
- 插入一条 `reports` 后，查看 `operation_logs` 新增记录

## 建议演示 SQL

```sql
SELECT * FROM vw_active_product_catalog LIMIT 5;
SELECT * FROM vw_seller_operational_summary ORDER BY completed_orders DESC;
SELECT * FROM vw_admin_risk_overview;

SELECT fn_product_display_status('APPROVED', 'ACTIVE', 1);
SELECT fn_seller_trust_level(12, 4.8, 0);
```
