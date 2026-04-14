CREATE VIEW IF NOT EXISTS v_product_overview AS
SELECT
  p.id,
  p.title,
  p.price,
  p.stock,
  p.product_status,
  p.audit_status,
  u.display_name AS seller_name,
  c.name AS category_name,
  p.created_at
FROM products p
LEFT JOIN users u ON u.id = p.seller_id
LEFT JOIN categories c ON c.id = p.category_id;

CREATE VIEW IF NOT EXISTS v_order_summary AS
SELECT
  o.id,
  o.status,
  o.total_amount,
  buyer.display_name AS buyer_name,
  seller.display_name AS seller_name,
  p.title AS product_title,
  o.created_at
FROM orders o
LEFT JOIN users buyer ON buyer.id = o.buyer_id
LEFT JOIN users seller ON seller.id = o.seller_id
LEFT JOIN products p ON p.id = o.product_id;

CREATE VIEW IF NOT EXISTS v_governance_queue AS
SELECT
  task_type,
  entity_type,
  status,
  COUNT(*) AS task_count
FROM audit_tasks
GROUP BY task_type, entity_type, status;

