from app.core.enums import AppealStatus, AuditStatus, MessageStatus, OrderStatus, PresenceStatus, ProductStatus, ReportStatus, TaskStatus
from app.core.security import hash_password
from app.models.entities import (
    AITaskLog,
    Appeal,
    AuditTask,
    BrowseHistory,
    Category,
    ChatMessage,
    ChatSession,
    Favorite,
    JobRunLog,
    Notification,
    Order,
    OrderItem,
    Permission,
    Product,
    ProductImage,
    RecommendationMaterial,
    RecommendationSnapshot,
    Report,
    Review,
    Role,
    RolePermission,
    User,
    UserRole,
)


def _product_tags(
    *,
    keywords: list[str],
    hero_summary: str,
    condition_label: str,
    detail_sections: list[dict],
    specs: list[dict],
    delivery_options: list[dict],
    trust_snapshot: dict,
    risk_flags: list[dict],
) -> dict:
    return {
        "keywords": keywords,
        "hero_summary": hero_summary,
        "condition_label": condition_label,
        "detail_sections": detail_sections,
        "specs": specs,
        "delivery_options": delivery_options,
        "trust_snapshot": trust_snapshot,
        "risk_flags": risk_flags,
    }


def _attach_images(db, product: Product, names: list[str]) -> None:
    db.add_all([ProductImage(product_id=product.id, url=f"/marketplace/products/{name}") for name in names])


def seed_defaults(db) -> None:
    if db.query(User).first():
        return

    permission_specs = [
        ("product.audit", "Audit products"),
        ("report.review", "Review reports"),
        ("appeal.review", "Review appeals"),
        ("recommendation.manage", "Manage recommendations"),
        ("search.manage", "Manage search"),
        ("notification.manage", "Manage notifications"),
    ]
    permission_map = {permission.code: permission for permission in db.query(Permission).all()}
    for code, name in permission_specs:
        if code not in permission_map:
            permission_map[code] = Permission(code=code, name=name)
            db.add(permission_map[code])

    admin_role = db.query(Role).filter_by(code="ADMIN").first()
    if not admin_role:
        admin_role = Role(name="Administrator", code="ADMIN")
        db.add(admin_role)
    moderator_role = db.query(Role).filter_by(code="MODERATOR").first()
    if not moderator_role:
        moderator_role = Role(name="Moderator", code="MODERATOR")
        db.add(moderator_role)
    db.flush()

    existing_role_permissions = {
        (item.role_id, item.permission_id)
        for item in db.query(RolePermission).all()
    }
    for permission in permission_map.values():
        if (admin_role.id, permission.id) not in existing_role_permissions:
            db.add(RolePermission(role_id=admin_role.id, permission_id=permission.id))
    moderator_allowed = {"product.audit", "report.review", "appeal.review"}
    for code in moderator_allowed:
        permission = permission_map[code]
        if (moderator_role.id, permission.id) not in existing_role_permissions:
            db.add(RolePermission(role_id=moderator_role.id, permission_id=permission.id))

    permissions = list(permission_map.values())

    admin = User(
        email="admin@example.com",
        password_hash=hash_password("Admin123!"),
        display_name="System Admin",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=True,
    )
    seller = User(
        email="seller@example.com",
        password_hash=hash_password("Seller123!"),
        display_name="林川",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=False,
    )
    buyer = User(
        email="buyer@example.com",
        password_hash=hash_password("Buyer123!"),
        display_name="周末买家",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=False,
    )
    reviewer = User(
        email="moderator@example.com",
        password_hash=hash_password("Mod123456!"),
        display_name="Audit Operator",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=True,
    )
    studio_seller = User(
        email="studio@example.com",
        password_hash=hash_password("Studio123!"),
        display_name="乔木工作室",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=False,
    )
    home_seller = User(
        email="home@example.com",
        password_hash=hash_password("Home123!!"),
        display_name="予然的闲置角",
        presence_status=PresenceStatus.ONLINE.value,
        is_admin=False,
    )

    categories = [
        Category(name="数码"),
        Category(name="图书"),
        Category(name="家居"),
        Category(name="潮玩"),
    ]

    db.add_all([admin_role, moderator_role, admin, seller, buyer, reviewer, studio_seller, home_seller, *permissions, *categories])
    db.flush()

    code_to_permission = {permission.code: permission for permission in permissions}
    db.add_all(
        [
            UserRole(user_id=admin.id, role_id=admin_role.id),
            UserRole(user_id=reviewer.id, role_id=moderator_role.id),
        ]
    )

    category_map = {category.name: category.id for category in categories}

    approved_product = Product(
        seller_id=seller.id,
        category_id=category_map["数码"],
        title="Nintendo Switch OLED 白色套装 95 新",
        description="2024 年 8 月京东自营入手，周末聚会用过几次，主机和 Joy-Con 无漂移，机器已恢复出厂。",
        price=1799.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["switch", "oled", "95新", "原装配件"],
            hero_summary="原装底座、手柄腕带、收纳包都在，适合想省去新机磨合期、又希望能现场验机的买家。",
            condition_label="95 新",
            detail_sections=[
                {"title": "商品说明", "body": "白色 OLED 国行版，屏幕无亮点，机身边框有正常轻微使用痕迹，拍照都尽量放大给你看。"},
                {"title": "使用情况", "body": "主要玩《塞尔达》和《马里奥赛车》，累计使用大约 60 小时，最近半年基本闲置放在防潮箱。"},
                {"title": "配件与瑕疵", "body": "含原装底座、电源、HDMI、腕带和收纳包；右侧手柄背面有一处不到 3mm 的浅痕，不影响使用。"},
                {"title": "交易备注", "body": "支持上海徐汇工作日晚间面交验机，外地可顺丰保价，发出前会再录一段开机视频。"},
            ],
            specs=[
                {"label": "购买来源", "value": "京东自营 2024/08"},
                {"label": "版本", "value": "国行 OLED 白色"},
                {"label": "使用时长", "value": "约 60 小时"},
                {"label": "电池/手柄状态", "value": "续航正常，双手柄无漂移"},
                {"label": "配件完整度", "value": "原装配件齐全，另送收纳包"},
                {"label": "适合人群", "value": "想入门主机、接受面交验机的玩家"},
            ],
            delivery_options=[
                {"label": "同城面交", "value": "支持", "note": "上海徐汇/静安地铁口可约，当面验机再确认。"},
                {"label": "顺丰保价", "value": "支持", "note": "确认尾款后 24 小时内发出，默认拍开机视频。"},
                {"label": "是否接受议价", "value": "小刀可谈", "note": "只接受礼貌议价，不考虑大幅砍价。"},
            ],
            trust_snapshot={
                "audit_label": "平台已审核通过",
                "audit_note": "图片、价格和基础成色信息已通过平台审核，支持继续沟通验机细节。",
                "support_label": "支持交易留痕",
                "support_note": "若面交或邮寄与描述明显不符，可凭会话与订单记录发起申诉。",
                "report_entry": "发现图文不符可直接举报",
                "dispute_entry": "订单后支持申诉与平台介入",
            },
            risk_flags=[
                {"level": "low", "title": "二手电子产品建议面交验机", "detail": "建议现场测试按键、屏幕和联网状态，外地交易请要求卖家发出开机视频。"},
                {"level": "medium", "title": "存在轻微使用痕迹", "detail": "右侧手柄背面有浅痕，介意外观完美度的买家建议先看细节图。"},
            ],
        ),
    )
    second_product = Product(
        seller_id=seller.id,
        category_id=category_map["图书"],
        title="算法竞赛进阶指南（第二版）含笔记",
        description="大学备赛阶段自用书，章节边缘有少量铅笔笔记，适合准备蓝桥杯和 ICPC 入门的同学。",
        price=68.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["算法", "图书", "竞赛", "笔记"],
            hero_summary="书页平整、书脊无爆裂，少量铅笔标注已集中在图里拍出，适合买来直接刷题用。",
            condition_label="近新有笔记",
            detail_sections=[
                {"title": "商品说明", "body": "第二版正版纸书，书页完整，没有缺页和水渍，封面边角有轻微放置痕迹。"},
                {"title": "使用情况", "body": "自己备赛时按章节做过题目索引，重点部分用铅笔做了页码标记，橡皮可以擦掉。"},
                {"title": "配件与瑕疵", "body": "随书附一张整理过的题单索引；书背上端有一点压痕，但翻阅完全正常。"},
                {"title": "交易备注", "body": "支持快递或校园附近面交，如果你想看某一章的目录，我可以先拍给你确认。"},
            ],
            specs=[
                {"label": "出版社", "value": "清华大学出版社"},
                {"label": "购买时间", "value": "2023/09"},
                {"label": "笔记情况", "value": "少量铅笔笔记，可擦"},
                {"label": "适合阶段", "value": "竞赛入门到进阶刷题"},
            ],
            delivery_options=[
                {"label": "发货方式", "value": "普通快递", "note": "拍下后通常当日或次日寄出。"},
                {"label": "同城面交", "value": "支持", "note": "工作日晚上可在上海西岸附近面交。"},
            ],
            trust_snapshot={
                "audit_label": "图书信息已审核",
                "audit_note": "版本、价格和卖家描述已通过平台基础校验。",
                "support_label": "支持图文核验",
                "support_note": "若收到后版本或装订与描述不符，可通过订单记录申请复核。",
                "report_entry": "可举报盗版或虚假版本",
                "dispute_entry": "支持订单申诉",
            },
            risk_flags=[
                {"level": "low", "title": "有真实笔记痕迹", "detail": "更适合注重内容而非收藏完美度的买家。"},
            ],
        ),
    )
    pending_product = Product(
        seller_id=seller.id,
        category_id=category_map["潮玩"],
        title="初号机限定款手办展示件",
        description="长期展示在封闭柜里，盒角有轻微磕碰，正在补充底座细节图和包装信息。",
        price=399.0,
        stock=1,
        product_status=ProductStatus.DRAFT.value,
        audit_status=AuditStatus.PENDING.value,
        tags=_product_tags(
            keywords=["手办", "限定", "展示件"],
            hero_summary="主体完好、漆面稳定，当前处于审核中，适合愿意等补齐细节图再做决定的收藏玩家。",
            condition_label="展示级",
            detail_sections=[
                {"title": "商品说明", "body": "限定版展示件，主体长期摆放在封闭展示柜中，未暴晒，没有明显掉漆。"},
                {"title": "使用情况", "body": "仅拆封展示，没有反复把玩，最近在整理盒内吸塑和说明书。"},
                {"title": "配件与瑕疵", "body": "盒角有轻微磕碰，底座边缘需要补拍特写，平台审核完成前不会开放交易。"},
                {"title": "交易备注", "body": "预计审核通过后支持同城面交，届时会补充 360 度实拍和盒损细节。"},
            ],
            specs=[
                {"label": "版本", "value": "限定款展示件"},
                {"label": "包装状态", "value": "盒角轻微磕碰"},
                {"label": "主体状态", "value": "无明显掉漆，待补细节图"},
            ],
            delivery_options=[
                {"label": "当前状态", "value": "暂不可交易", "note": "需待平台审核结束后开放沟通与下单。"},
            ],
            trust_snapshot={
                "audit_label": "审核中",
                "audit_note": "平台正在核对盒损、版本和图片完整度，暂不建议直接成交。",
                "support_label": "资料待补充",
                "support_note": "审核通过前不会开放交易入口，避免买卖双方信息不对称。",
                "report_entry": "若发现盗图可举报",
                "dispute_entry": "审核结果可申诉",
            },
            risk_flags=[
                {"level": "high", "title": "当前信息尚未补齐", "detail": "底座和包装盒细节图仍在补充，审核通过前不建议付款或线下交易。"},
            ],
        ),
    )
    headphone_product = Product(
        seller_id=studio_seller.id,
        category_id=category_map["数码"],
        title="Sony WH-1000XM5 银色 95 新",
        description="工作室样品机，试听次数不多，耳罩干净无塌陷，收纳盒和音频线都在。",
        price=1650.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["sony", "xm5", "耳机", "降噪"],
            hero_summary="耳罩和头梁状态都很整，适合想要旗舰降噪但不想按新机价入手的人。",
            condition_label="95 新",
            detail_sections=[
                {"title": "商品说明", "body": "银色国行版，工作室试听样机，累计使用时间不到两周，没有长时间暴汗佩戴。"},
                {"title": "使用情况", "body": "主要在室内试听人声和通勤降噪效果，最近升级设备所以整理出售。"},
                {"title": "配件与瑕疵", "body": "原装硬壳盒、Type-C 线和 3.5mm 音频线齐全，外壳有一处非常轻微的指甲划痕。"},
                {"title": "交易备注", "body": "支持深圳福田面交试听，也可顺丰保价寄出，发货前会录一段功能演示视频。"},
            ],
            specs=[
                {"label": "购买来源", "value": "索尼直营店样机流转"},
                {"label": "电池状态", "value": "续航正常，降噪与触控功能都已测试"},
                {"label": "配件完整度", "value": "收纳盒、充电线、音频线齐全"},
                {"label": "适合人群", "value": "通勤、居家办公、需要主动降噪的用户"},
            ],
            delivery_options=[
                {"label": "同城试听", "value": "支持", "note": "深圳福田可预约试听 15 分钟。"},
                {"label": "顺丰保价", "value": "支持", "note": "默认双层包装，保护耳罩不受压。"},
            ],
            trust_snapshot={
                "audit_label": "平台已审核通过",
                "audit_note": "机身状态、配件完整度和价格区间均已校验。",
                "support_label": "支持争议留痕",
                "support_note": "试听或快递细节可在站内会话确认，后续申诉可引用完整记录。",
                "report_entry": "支持举报图文不符",
                "dispute_entry": "订单争议可提交平台复核",
            },
            risk_flags=[
                {"level": "medium", "title": "耳机类商品建议先试听", "detail": "佩戴松紧和听感偏好因人而异，同城买家建议先试听再决定。"},
            ],
        ),
    )
    camera_product = Product(
        seller_id=studio_seller.id,
        category_id=category_map["数码"],
        title="Fujifilm X-T30 II 银色单机身",
        description="快门约 6100 次，机身边角有轻微磕点，传感器干净，适合想入门富士直出的用户。",
        price=4680.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["fujifilm", "相机", "xt30", "微单"],
            hero_summary="快门次数不高，机身成色在线，适合想要轻便街拍机身、又接受正常使用痕迹的买家。",
            condition_label="9 成新",
            detail_sections=[
                {"title": "商品说明", "body": "机身单出，不含镜头；快门约 6100 次，传感器和取景器状态都正常，按键反馈利落。"},
                {"title": "使用情况", "body": "主要用于周末扫街和店铺静物拍摄，没有拍过重度视频，最近换全画幅所以出售。"},
                {"title": "配件与瑕疵", "body": "含原电一块、肩带、充电头和包装盒；机身右下角有一处轻微磕点，图里已单独拍出。"},
                {"title": "交易备注", "body": "支持深圳线下面交试拍，也可视频连线展示快门数和传感器状态。"},
            ],
            specs=[
                {"label": "购买时间", "value": "2023/03"},
                {"label": "快门次数", "value": "约 6100 次"},
                {"label": "套装情况", "value": "单机身，不含镜头"},
                {"label": "适合人群", "value": "街拍、旅行和富士直出爱好者"},
            ],
            delivery_options=[
                {"label": "面交试拍", "value": "支持", "note": "可自带存储卡现场试拍和导图。"},
                {"label": "快递发货", "value": "支持", "note": "默认顺丰保价，发前会拍机身编号与功能视频。"},
            ],
            trust_snapshot={
                "audit_label": "审核已完成",
                "audit_note": "快门次数、外观状态和配件信息已完成基础审核。",
                "support_label": "支持验货记录",
                "support_note": "建议在会话中确认编号、快门数和是否含发票，减少交付分歧。",
                "report_entry": "可举报序列号或状态描述异常",
                "dispute_entry": "支持提交验货视频申诉",
            },
            risk_flags=[
                {"level": "medium", "title": "机身有轻微磕点", "detail": "追求收藏级外观的买家建议先看细节图或线下确认。"},
            ],
        ),
    )
    chair_product = Product(
        seller_id=home_seller.id,
        category_id=category_map["家居"],
        title="Herman Miller Sayl 办公椅 灰黑配色",
        description="2022 年购入自用，网背弹性正常，扶手与底盘无异响，因搬家换布局所以转出。",
        price=2380.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["办公椅", "sayl", "家居", "自提"],
            hero_summary="坐感和支撑性都在线，更适合同城自提或面交确认的买家，避免大件运输磕碰。",
            condition_label="9 成新",
            detail_sections=[
                {"title": "商品说明", "body": "灰黑配色，网背弹性和气压杆升降都正常，脚轮顺滑，没有烟味和宠物抓痕。"},
                {"title": "使用情况", "body": "过去两年主要放在书房办公，每天大概使用 4-5 小时，保养比较勤，定期清洁网面。"},
                {"title": "配件与瑕疵", "body": "无原箱，椅背下侧有一处轻微擦痕，平时基本看不到；坐垫海绵支撑仍然稳定。"},
                {"title": "交易备注", "body": "杭州滨江优先自提，也可以同城拉货，暂不建议外地快递。"},
            ],
            specs=[
                {"label": "购买时间", "value": "2022/06"},
                {"label": "使用环境", "value": "无烟书房，定期清洁"},
                {"label": "运输建议", "value": "优先自提或同城搬运"},
                {"label": "适合人群", "value": "居家办公、久坐需要腰背支撑的人"},
            ],
            delivery_options=[
                {"label": "同城自提", "value": "优先支持", "note": "杭州滨江可上门看实物后自提。"},
                {"label": "同城拉货", "value": "可协商", "note": "需买家承担搬运或跑腿费用。"},
                {"label": "外地邮寄", "value": "暂不支持", "note": "大件运输磕碰风险高，不建议异地购买。"},
            ],
            trust_snapshot={
                "audit_label": "平台已审核",
                "audit_note": "家居类商品以实拍和同城交易信息为主，平台已完成基础审核。",
                "support_label": "建议同城验货",
                "support_note": "大件商品更适合看实物后成交，平台保留会话与订单记录供后续复核。",
                "report_entry": "可举报尺寸或状态描述不实",
                "dispute_entry": "支持提交交付照片申诉",
            },
            risk_flags=[
                {"level": "medium", "title": "大件商品更适合同城交易", "detail": "外地运输成本高且有磕碰风险，平台建议先确认交付方案。"},
            ],
        ),
    )
    coffee_product = Product(
        seller_id=home_seller.id,
        category_id=category_map["家居"],
        title="HARIO V60 手冲咖啡全套出",
        description="包含玻璃滤杯、分享壶、电子秤和手冲壶，自用约半年，器具无磕裂。",
        price=420.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["手冲", "咖啡", "hario", "家居"],
            hero_summary="一套就能直接开冲，适合刚入门手冲、不想零散凑器具的买家。",
            condition_label="近新",
            detail_sections=[
                {"title": "商品说明", "body": "整套包含 V60 玻璃滤杯、600ml 分享壶、细口壶和电子秤，器具都可正常使用。"},
                {"title": "使用情况", "body": "自用半年，平均每周冲 2-3 次，搬家后厨房空间变小所以整理出售。"},
                {"title": "配件与瑕疵", "body": "玻璃器具无裂痕，秤面有正常使用细纹；滤纸只剩少量，不作为完整配件计算。"},
                {"title": "交易备注", "body": "杭州可面交看实物，邮寄会分层包裹并加防震材料。"},
            ],
            specs=[
                {"label": "套装内容", "value": "滤杯、分享壶、手冲壶、电子秤"},
                {"label": "使用频率", "value": "每周约 2-3 次"},
                {"label": "适合人群", "value": "手冲入门或升级基础套装"},
            ],
            delivery_options=[
                {"label": "面交", "value": "支持", "note": "杭州城西可工作日晚间面交。"},
                {"label": "快递", "value": "支持", "note": "默认做双层防震包装。"},
            ],
            trust_snapshot={
                "audit_label": "平台已审核",
                "audit_note": "器具完整度与实拍图已通过基础审核。",
                "support_label": "破损可协商申诉",
                "support_note": "如快递造成明显破损，请保留开箱视频并联系平台介入。",
                "report_entry": "支持举报图片与实物不符",
                "dispute_entry": "快递破损支持申诉",
            },
            risk_flags=[
                {"level": "low", "title": "玻璃器具建议确认包装", "detail": "邮寄前建议在会话里确认包裹方式，收到后请及时验货。"},
            ],
        ),
    )
    tablet_product = Product(
        seller_id=seller.id,
        category_id=category_map["数码"],
        title="iPad mini 6 64G 紫色 WLAN 版",
        description="主要用来看文档和漫画，屏幕贴膜使用，边框有一处轻微磕碰，原盒和充电线都在。",
        price=2380.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags=_product_tags(
            keywords=["ipad", "mini6", "平板", "紫色"],
            hero_summary="尺寸轻巧、阅读手感很好，适合通勤看文档、刷漫画或做随身副屏的人。",
            condition_label="9 成新",
            detail_sections=[
                {"title": "商品说明", "body": "64G WLAN 版紫色机型，屏幕长期贴膜，指纹和扬声器功能正常。"},
                {"title": "使用情况", "body": "主要在通勤和咖啡店阅读文档、看漫画，没有重度游戏和长期充电玩机。"},
                {"title": "配件与瑕疵", "body": "含原盒、数据线和一个第三方保护壳；右下角有一处轻微磕碰，贴近看才明显。"},
                {"title": "交易备注", "body": "支持上海地铁沿线面交验机，也可顺丰保价发出。"},
            ],
            specs=[
                {"label": "购买时间", "value": "2022/12"},
                {"label": "版本", "value": "64G WLAN 版"},
                {"label": "电池状态", "value": "日常阅读续航正常"},
                {"label": "适合人群", "value": "轻办公、阅读、随身娱乐"},
            ],
            delivery_options=[
                {"label": "同城面交", "value": "支持", "note": "上海地铁沿线可约现场验机。"},
                {"label": "顺丰保价", "value": "支持", "note": "确认付款后 24 小时内发出。"},
            ],
            trust_snapshot={
                "audit_label": "平台已审核通过",
                "audit_note": "容量、颜色和成色信息已通过基础校验。",
                "support_label": "支持会话留痕",
                "support_note": "建议在会话中确认序列号和电池体验，再决定是否成交。",
                "report_entry": "支持举报序列号或机况异常",
                "dispute_entry": "支持订单申诉",
            },
            risk_flags=[
                {"level": "medium", "title": "边框有轻微磕碰", "detail": "完美主义买家建议先看细节图或同城验机。"},
            ],
        ),
    )

    products = [
        approved_product,
        second_product,
        pending_product,
        headphone_product,
        camera_product,
        chair_product,
        coffee_product,
        tablet_product,
    ]
    db.add_all(products)
    db.flush()

    _attach_images(db, approved_product, ["switch-1.jpg", "switch-2.jpg", "switch-3.jpg"])
    _attach_images(db, second_product, ["book-1.jpg", "book-2.jpg", "book-3.jpg"])
    _attach_images(db, pending_product, ["figure-1.jpg", "figure-2.jpg", "figure-3.jpg"])
    _attach_images(db, headphone_product, ["headphone-1.jpg", "headphone-2.jpg", "headphone-3.jpg"])
    _attach_images(db, camera_product, ["camera-1.jpg", "camera-2.jpg", "camera-3.jpg"])
    _attach_images(db, chair_product, ["chair-1.jpg", "chair-2.jpg", "chair-3.jpg"])
    _attach_images(db, coffee_product, ["coffee-1.jpg", "coffee-2.jpg", "coffee-3.jpg"])
    _attach_images(db, tablet_product, ["tablet-1.jpg", "tablet-2.jpg", "tablet-3.jpg"])

    audit_task = AuditTask(
        task_type="PRODUCT_AUDIT",
        entity_type="PRODUCT",
        entity_id=pending_product.id,
        status=TaskStatus.PENDING.value,
        payload={"title": pending_product.title},
    )
    report = Report(
        reporter_id=buyer.id,
        target_type="PRODUCT",
        target_id=approved_product.id,
        reason="卖家已补充细节图前，我对手柄磨损位置描述还有疑问，想请平台复核记录。",
        status=ReportStatus.PROCESSED.value,
        decision="已提醒卖家补充细节图并保留治理记录。",
    )
    db.add_all([audit_task, report])
    db.flush()

    appeal = Appeal(
        report_id=report.id,
        applicant_id=seller.id,
        reason="已补充手柄细节图与近景说明，申请复核。",
        status=AppealStatus.PENDING.value,
    )
    db.add(appeal)
    db.flush()

    appeal_task = AuditTask(
        task_type="APPEAL_REVIEW",
        entity_type="APPEAL",
        entity_id=appeal.id,
        status=TaskStatus.PENDING.value,
        payload={"reason": appeal.reason},
    )
    db.add(appeal_task)
    db.flush()

    switch_order = Order(
        buyer_id=buyer.id,
        seller_id=seller.id,
        product_id=approved_product.id,
        total_amount=1799.0,
        status=OrderStatus.COMPLETED.value,
    )
    headphone_order = Order(
        buyer_id=buyer.id,
        seller_id=studio_seller.id,
        product_id=headphone_product.id,
        total_amount=1650.0,
        status=OrderStatus.COMPLETED.value,
    )
    chair_order = Order(
        buyer_id=buyer.id,
        seller_id=home_seller.id,
        product_id=chair_product.id,
        total_amount=2380.0,
        status=OrderStatus.COMPLETED.value,
    )
    db.add_all([switch_order, headphone_order, chair_order])
    db.flush()

    db.add_all(
        [
            OrderItem(order_id=switch_order.id, product_id=approved_product.id, quantity=1, unit_price=1799.0),
            OrderItem(order_id=headphone_order.id, product_id=headphone_product.id, quantity=1, unit_price=1650.0),
            OrderItem(order_id=chair_order.id, product_id=chair_product.id, quantity=1, unit_price=2380.0),
        ]
    )
    db.add_all(
        [
            Review(
                order_id=switch_order.id,
                product_id=approved_product.id,
                user_id=buyer.id,
                rating=5,
                content="现场验机很顺，机器和描述基本一致，卖家还提前把收纳包和配件摆好了。",
            ),
            Review(
                order_id=headphone_order.id,
                product_id=headphone_product.id,
                user_id=buyer.id,
                rating=5,
                content="耳罩很干净，试听后再决定的，卖家把功能键和降噪都演示得很细。",
            ),
            Review(
                order_id=chair_order.id,
                product_id=chair_product.id,
                user_id=buyer.id,
                rating=4,
                content="椅子状态不错，自提过程顺利，卖家对磨损点也提前说明了。",
            ),
        ]
    )

    db.add_all(
        [
            Favorite(user_id=buyer.id, product_id=approved_product.id),
            Favorite(user_id=buyer.id, product_id=camera_product.id),
            Favorite(user_id=buyer.id, product_id=tablet_product.id),
            BrowseHistory(user_id=buyer.id, product_id=approved_product.id),
            BrowseHistory(user_id=buyer.id, product_id=headphone_product.id),
            BrowseHistory(user_id=buyer.id, product_id=chair_product.id),
            BrowseHistory(user_id=buyer.id, product_id=tablet_product.id),
        ]
    )

    db.add_all(
        [
            RecommendationMaterial(user_id=buyer.id, product_id=approved_product.id, material_type="ORDER", payload={"order_id": switch_order.id}),
            RecommendationMaterial(user_id=buyer.id, product_id=headphone_product.id, material_type="REVIEW", payload={"rating": 5}),
            RecommendationMaterial(user_id=buyer.id, product_id=chair_product.id, material_type="HISTORY", payload={}),
        ]
    )
    db.add(
        RecommendationSnapshot(
            user_id=buyer.id,
            scene="HOME",
            payload={
                "items": [
                    {"product_id": approved_product.id, "reason": "你最近浏览和收藏过同类掌机设备"},
                    {"product_id": camera_product.id, "reason": "适合喜欢成色说明完整的数码设备"},
                    {"product_id": chair_product.id, "reason": "与你近期浏览的居家办公场景接近"},
                ]
            },
        )
    )

    session = ChatSession(product_id=approved_product.id, buyer_id=buyer.id, seller_id=seller.id)
    second_session = ChatSession(product_id=headphone_product.id, buyer_id=buyer.id, seller_id=studio_seller.id)
    db.add_all([session, second_session])
    db.flush()
    db.add_all(
        [
            ChatMessage(session_id=session.id, sender_id=buyer.id, content="这台机器还在吗？面交能验一下摇杆和联网吗？", status=MessageStatus.READ.value),
            ChatMessage(session_id=session.id, sender_id=seller.id, content="还在，今晚徐汇可以，当面测摇杆、读卡和联网都没问题。", status=MessageStatus.SENT.value),
            ChatMessage(session_id=second_session.id, sender_id=buyer.id, content="XM5 这副耳机可以先试听再定吗？", status=MessageStatus.READ.value),
            ChatMessage(session_id=second_session.id, sender_id=studio_seller.id, content="可以，福田这边可以现场试降噪和佩戴松紧。", status=MessageStatus.SENT.value),
        ]
    )
    db.add(
        Notification(
            user_id=buyer.id,
            event_type="AUDIT",
            title="举报处理已更新",
            content="平台已完成对商品 1 的复核，并提示卖家补充细节说明。",
        )
    )
    db.add(
        JobRunLog(
            job_name="recommendation_rebuild",
            status=TaskStatus.COMPLETED.value,
            details={"scene": "HOME"},
        )
    )
    db.add(
        AITaskLog(
            task_name="product_draft",
            prompt="switch, 95新, 原装配件",
            result={"title": "Nintendo Switch OLED 白色套装 95 新", "risk_level": "LOW"},
            status=TaskStatus.COMPLETED.value,
        )
    )
    db.commit()
