INSERT INTO roles (id, name, code, created_at, updated_at) VALUES
  (1, 'Administrator', 'ADMIN', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 'Moderator', 'MODERATOR', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO permissions (id, code, name) VALUES
  (1, 'product.audit', 'Audit products'),
  (2, 'report.review', 'Review reports'),
  (3, 'appeal.review', 'Review appeals'),
  (4, 'recommendation.manage', 'Manage recommendations'),
  (5, 'search.manage', 'Manage search');

INSERT INTO users (id, email, password_hash, display_name, status, is_admin, created_at, updated_at) VALUES
  (1, 'admin@example.com', '$pbkdf2-sha256$29000$AkCo9X5v7X1vDaE0ZmyNEQ$FlPbm7KGfQbT34FV2IfiA8niWutxHCNvCvXylZPl5Js', 'System Admin', 'ACTIVE', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 'seller@example.com', '$pbkdf2-sha256$29000$QkjJWev9f29tzblXaq1Vig$/fwwJBsYGL849AfM0A9sHxAuHmNOZF4/Uf.3vSCoztE', 'Demo Seller', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 'buyer@example.com', '$pbkdf2-sha256$29000$b43xXsvZm3NOyZkT4pwTgg$JtTlcDE3lLJW0pFYPDyeZtxi.oQTFwI2ihPiaST87J8', 'Demo Buyer', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, 'moderator@example.com', '$pbkdf2-sha256$29000$idGa0/p/DwFAyLl3bu19bw$uuEedMolIaVTHSGSrydBIQoMBqIpD5OiS5BNSFf65aw', 'Audit Operator', 'ACTIVE', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO user_roles (user_id, role_id) VALUES
  (1, 1),
  (4, 2);

INSERT INTO role_permissions (role_id, permission_id) VALUES
  (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
  (2, 1), (2, 2), (2, 3);

INSERT INTO categories (id, name, created_at, updated_at) VALUES
  (1, '数码', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, '图书', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, '家居', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, '潮玩', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO products (id, seller_id, category_id, title, description, price, stock, product_status, audit_status, tags, created_at, updated_at) VALUES
  (1, 2, 1, 'Nintendo Switch OLED 九成新', '含原装底座、手柄和收纳包，支持现场验机。', 1799.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["switch","oled","九成新"]}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 2, 2, '算法竞赛进阶指南', '书页完整，有少量笔记，适合刷题入门。', 68.0, 2, 'ACTIVE', 'APPROVED', '{"keywords":["算法","图书"]}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 2, 4, '限定款手办展示件', '盒损轻微，主体完好，等待管理员审核。', 399.0, 1, 'DRAFT', 'PENDING', '{"keywords":["手办","限定"]}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO audit_tasks (id, task_type, entity_type, entity_id, status, payload, created_at, updated_at) VALUES
  (1, 'PRODUCT_AUDIT', 'PRODUCT', 3, 'PENDING', '{"title":"限定款手办展示件"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 'APPEAL_REVIEW', 'APPEAL', 1, 'PENDING', '{"reason":"已补充更多细节图，申请复核"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO reports (id, reporter_id, target_type, target_id, reason, status, decision, created_at, updated_at) VALUES
  (1, 3, 'PRODUCT', 1, '商品描述与成色信息可能不一致', 'PROCESSED', '已提醒卖家补充说明并记录一次治理事件', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO appeals (id, report_id, applicant_id, reason, status, decision, created_at, updated_at) VALUES
  (1, 1, 2, '已补充更多细节图，申请复核', 'PENDING', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO orders (id, buyer_id, seller_id, product_id, total_amount, status, created_at, updated_at) VALUES
  (1, 3, 2, 1, 1799.0, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  (1, 1, 1, 1799.0);

INSERT INTO reviews (order_id, product_id, user_id, rating, content, created_at, updated_at) VALUES
  (1, 1, 3, 5, '成色很好，沟通顺畅，和描述基本一致。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO favorites (user_id, product_id, created_at, updated_at) VALUES
  (3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO browse_history (user_id, product_id, created_at, updated_at) VALUES
  (3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO chat_sessions (id, product_id, buyer_id, seller_id, created_at, updated_at) VALUES
  (1, 1, 3, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO chat_messages (session_id, sender_id, content, status, created_at, updated_at) VALUES
  (1, 3, '这台机器还在吗？', 'READ', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (1, 2, '还在，可以现场验机。', 'SENT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO notifications (user_id, event_type, title, content, created_at, updated_at) VALUES
  (3, 'AUDIT', '举报处理完成', '你提交的举报已经进入处理完成状态。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO recommendation_materials (user_id, product_id, material_type, payload, created_at, updated_at) VALUES
  (3, 1, 'ORDER', '{"order_id":1}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO recommendation_snapshots (user_id, scene, payload, created_at, updated_at) VALUES
  (3, 'HOME', '{"items":[{"product_id":1,"title":"Nintendo Switch OLED 九成新"}]}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO job_run_logs (job_name, status, details, created_at, updated_at) VALUES
  ('recommendation_rebuild', 'COMPLETED', '{"scene":"HOME"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO ai_task_logs (task_name, prompt, result, status, created_at, updated_at) VALUES
  ('product_draft', 'switch, 九成新, 原装配件', '{"title":"Nintendo Switch OLED 九成新","risk_level":"LOW"}', 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
