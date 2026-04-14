CREATE TRIGGER IF NOT EXISTS trg_products_updated_at
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
  UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_orders_updated_at
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_tasks_updated_at
AFTER UPDATE ON audit_tasks
FOR EACH ROW
BEGIN
  UPDATE audit_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_reports_operation_log
AFTER INSERT ON reports
FOR EACH ROW
BEGIN
  INSERT INTO operation_logs (actor_id, action, details, created_at, updated_at)
  VALUES (NEW.reporter_id, 'report.submit', json_object('report_id', NEW.id, 'target_type', NEW.target_type), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
END;

