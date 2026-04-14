CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_products_seller_id ON products(seller_id);
CREATE INDEX IF NOT EXISTS idx_products_title ON products(title);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_reporter_id ON reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_appeals_report_id ON appeals(report_id);
CREATE INDEX IF NOT EXISTS idx_audit_tasks_entity ON audit_tasks(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_snapshots_scene ON recommendation_snapshots(scene);
CREATE INDEX IF NOT EXISTS idx_domain_events_type ON domain_events(event_type);

