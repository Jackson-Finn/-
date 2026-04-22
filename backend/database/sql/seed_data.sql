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
  (2, 'seller@example.com', '$pbkdf2-sha256$29000$QkjJWev9f29tzblXaq1Vig$/fwwJBsYGL849AfM0A9sHxAuHmNOZF4/Uf.3vSCoztE', '林川', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 'buyer@example.com', '$pbkdf2-sha256$29000$b43xXsvZm3NOyZkT4pwTgg$JtTlcDE3lLJW0pFYPDyeZtxi.oQTFwI2ihPiaST87J8', '周末买家', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, 'moderator@example.com', '$pbkdf2-sha256$29000$idGa0/p/DwFAyLl3bu19bw$uuEedMolIaVTHSGSrydBIQoMBqIpD5OiS5BNSFf65aw', 'Audit Operator', 'ACTIVE', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, 'studio@example.com', '$pbkdf2-sha256$29000$QkjJWev9f29tzblXaq1Vig$/fwwJBsYGL849AfM0A9sHxAuHmNOZF4/Uf.3vSCoztE', '乔木工作室', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (6, 'home@example.com', '$pbkdf2-sha256$29000$QkjJWev9f29tzblXaq1Vig$/fwwJBsYGL849AfM0A9sHxAuHmNOZF4/Uf.3vSCoztE', '予然的闲置角', 'ACTIVE', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

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
  (1, 2, 1, 'Nintendo Switch OLED 白色套装 95 新', '2024 年 8 月京东自营入手，周末聚会用过几次，主机和 Joy-Con 无漂移，机器已恢复出厂。', 1799.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["switch","oled","95新","原装配件"],"hero_summary":"原装底座、手柄腕带、收纳包都在，适合想省去新机磨合期、又希望能现场验机的买家。","condition_label":"95 新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 2, 2, '算法竞赛进阶指南（第二版）含笔记', '大学备赛阶段自用书，章节边缘有少量铅笔笔记，适合准备蓝桥杯和 ICPC 入门的同学。', 68.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["算法","图书","竞赛","笔记"],"hero_summary":"书页平整、书脊无爆裂，少量铅笔标注已集中在图里拍出，适合买来直接刷题用。","condition_label":"近新有笔记"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 2, 4, '初号机限定款手办展示件', '长期展示在封闭柜里，盒角有轻微磕碰，正在补充底座细节图和包装信息。', 399.0, 1, 'DRAFT', 'PENDING', '{"keywords":["手办","限定","展示件"],"hero_summary":"主体完好、漆面稳定，当前处于审核中，适合愿意等补齐细节图再做决定的收藏玩家。","condition_label":"展示级"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, 5, 1, 'Sony WH-1000XM5 银色 95 新', '工作室样品机，试听次数不多，耳罩干净无塌陷，收纳盒和音频线都在。', 1650.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["sony","xm5","耳机","降噪"],"hero_summary":"耳罩和头梁状态都很整，适合想要旗舰降噪但不想按新机价入手的人。","condition_label":"95 新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, 5, 1, 'Fujifilm X-T30 II 银色单机身', '快门约 6100 次，机身边角有轻微磕点，传感器干净，适合想入门富士直出的用户。', 4680.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["fujifilm","相机","xt30","微单"],"hero_summary":"快门次数不高，机身成色在线，适合想要轻便街拍机身、又接受正常使用痕迹的买家。","condition_label":"9 成新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (6, 6, 3, 'Herman Miller Sayl 办公椅 灰黑配色', '2022 年购入自用，网背弹性正常，扶手与底盘无异响，因搬家换布局所以转出。', 2380.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["办公椅","sayl","家居","自提"],"hero_summary":"坐感和支撑性都在线，更适合同城自提或面交确认的买家，避免大件运输磕碰。","condition_label":"9 成新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (7, 6, 3, 'HARIO V60 手冲咖啡全套出', '包含玻璃滤杯、分享壶、电子秤和手冲壶，自用约半年，器具无磕裂。', 420.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["手冲","咖啡","hario","家居"],"hero_summary":"一套就能直接开冲，适合刚入门手冲、不想零散凑器具的买家。","condition_label":"近新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (8, 2, 1, 'iPad mini 6 64G 紫色 WLAN 版', '主要用来看文档和漫画，屏幕贴膜使用，边框有一处轻微磕碰，原盒和充电线都在。', 2380.0, 1, 'ACTIVE', 'APPROVED', '{"keywords":["ipad","mini6","平板","紫色"],"hero_summary":"尺寸轻巧、阅读手感很好，适合通勤看文档、刷漫画或做随身副屏的人。","condition_label":"9 成新"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO product_images (product_id, url, created_at, updated_at) VALUES
  (1, '/marketplace/products/switch-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (1, '/marketplace/products/switch-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (1, '/marketplace/products/switch-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, '/marketplace/products/book-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, '/marketplace/products/book-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, '/marketplace/products/book-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, '/marketplace/products/figure-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, '/marketplace/products/figure-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, '/marketplace/products/figure-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, '/marketplace/products/headphone-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, '/marketplace/products/headphone-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, '/marketplace/products/headphone-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, '/marketplace/products/camera-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, '/marketplace/products/camera-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, '/marketplace/products/camera-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (6, '/marketplace/products/chair-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (6, '/marketplace/products/chair-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (6, '/marketplace/products/chair-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (7, '/marketplace/products/coffee-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (7, '/marketplace/products/coffee-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (7, '/marketplace/products/coffee-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (8, '/marketplace/products/tablet-1.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (8, '/marketplace/products/tablet-2.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (8, '/marketplace/products/tablet-3.jpg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO audit_tasks (id, task_type, entity_type, entity_id, status, payload, created_at, updated_at) VALUES
  (1, 'PRODUCT_AUDIT', 'PRODUCT', 3, 'PENDING', '{"title":"初号机限定款手办展示件"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 'APPEAL_REVIEW', 'APPEAL', 1, 'PENDING', '{"reason":"已补充手柄细节图与近景说明，申请复核。"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO reports (id, reporter_id, target_type, target_id, reason, status, decision, created_at, updated_at) VALUES
  (1, 3, 'PRODUCT', 1, '卖家已补充细节图前，我对手柄磨损位置描述还有疑问，想请平台复核记录。', 'PENDING', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO appeals (id, report_id, applicant_id, reason, status, decision, created_at, updated_at) VALUES
  (1, 1, 2, '已补充手柄细节图与近景说明，申请复核。', 'PENDING', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO orders (id, buyer_id, seller_id, product_id, total_amount, status, created_at, updated_at) VALUES
  (1, 3, 2, 1, 1799.0, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 3, 5, 4, 1650.0, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 3, 6, 6, 2380.0, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  (1, 1, 1, 1799.0),
  (2, 4, 1, 1650.0),
  (3, 6, 1, 2380.0);

INSERT INTO reviews (order_id, product_id, user_id, rating, content, created_at, updated_at) VALUES
  (1, 1, 3, 5, '现场验机很顺，机器和描述基本一致，卖家还提前把收纳包和配件摆好了。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 4, 3, 5, '耳罩很干净，试听后再决定的，卖家把功能键和降噪都演示得很细。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 6, 3, 4, '椅子状态不错，自提过程顺利，卖家对磨损点也提前说明了。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO favorites (user_id, product_id, created_at, updated_at) VALUES
  (3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO browse_history (user_id, product_id, created_at, updated_at) VALUES
  (3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO chat_sessions (id, product_id, buyer_id, seller_id, created_at, updated_at) VALUES
  (1, 1, 3, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 4, 3, 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO chat_messages (session_id, sender_id, content, status, created_at, updated_at) VALUES
  (1, 3, '这台机器还在吗？面交能验一下摇杆和联网吗？', 'READ', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (1, 2, '还在，今晚徐汇可以，当面测摇杆、读卡和联网都没问题。', 'SENT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 3, 'XM5 这副耳机可以先试听再定吗？', 'READ', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 5, '可以，福田这边可以现场试降噪和佩戴松紧。', 'SENT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO notifications (user_id, event_type, title, content, created_at, updated_at) VALUES
  (3, 'AUDIT', '举报处理已更新', '平台已完成对商品 1 的复核，并提示卖家补充细节说明。', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO recommendation_materials (user_id, product_id, material_type, payload, created_at, updated_at) VALUES
  (3, 1, 'ORDER', '{"order_id":1}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 4, 'REVIEW', '{"rating":5}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 6, 'HISTORY', '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO recommendation_snapshots (user_id, scene, payload, created_at, updated_at) VALUES
  (3, 'HOME', '{"items":[{"product_id":1,"reason":"你最近浏览和收藏过同类掌机设备"},{"product_id":5,"reason":"适合喜欢成色说明完整的数码设备"},{"product_id":6,"reason":"与你近期浏览的居家办公场景接近"}]}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO job_run_logs (job_name, status, details, created_at, updated_at) VALUES
  ('recommendation_rebuild', 'COMPLETED', '{"scene":"HOME"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO ai_task_logs (task_name, prompt, result, status, created_at, updated_at) VALUES
  ('product_draft', 'switch, 95新, 原装配件', '{"title":"Nintendo Switch OLED 白色套装 95 新","risk_level":"LOW"}', 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
