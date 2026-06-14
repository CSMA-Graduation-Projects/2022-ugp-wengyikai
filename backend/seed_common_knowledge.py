# seed_common_knowledge.py
"""
数据库知识库初始化脚本。
运行方式：python seed_common_knowledge.py
作用：创建 knowledge_module 表，并写入/更新通用软件业务知识模块。
"""
import json
from typing import Dict, List

from database import Base, engine, SessionLocal
from knowledge_models import KnowledgeModule


COMMON_KNOWLEDGE_MODULES: List[Dict] = [
    # 一、安全认证与用户体系
    {
        "module_name": "登录",
        "category": "安全认证",
        "aliases": ["认证", "用户登录", "账号登录", "登录系统", "注册登录", "登录注册", "注册登录类", "登录注册类"],
        "required_elements": ["账号密码输入", "验证码校验", "多因素认证", "密码加密存储", "错误重试限制"],
        "preconditions": ["用户已注册", "账号处于可用状态"],
        "exception_scenarios": ["密码错误", "验证码失效", "账号被冻结", "连续输入失败超过限制", "账号不存在"],
        "typical_tasks": ["设计登录页面", "实现登录接口", "设计用户表字段", "实现失败提示与重试限制", "接入验证码校验"],
        "security_constraints": "需进行身份认证、密码加密存储和失败次数限制"
    },
    {
        "module_name": "注册",
        "category": "安全认证",
        "aliases": ["用户注册", "账号注册", "新用户注册", "开户注册", "注册登录", "登录注册", "注册登录类", "登录注册类"],
        "required_elements": ["注册信息校验", "密码加密存储", "重复账号校验", "验证码验证", "用户协议确认"],
        "preconditions": ["用户未注册", "手机号或邮箱未被占用"],
        "exception_scenarios": ["手机号已存在", "验证码错误", "信息格式非法", "密码强度不足", "重复提交注册"],
        "typical_tasks": ["设计注册页面", "实现注册接口", "设计用户表", "实现验证码校验逻辑", "实现重复账号检查"],
        "security_constraints": "敏感信息需加密传输与存储，注册接口需限制高频请求"
    },
    {
        "module_name": "验证码",
        "category": "安全认证",
        "aliases": ["短信验证码", "邮箱验证码", "图形验证码", "验证码校验", "发送验证码"],
        "required_elements": ["验证码生成", "验证码发送", "有效期", "校验次数", "发送频率限制"],
        "preconditions": ["手机号或邮箱格式正确", "发送通道可用"],
        "exception_scenarios": ["验证码过期", "验证码错误", "发送频率过高", "发送失败"],
        "typical_tasks": ["实现验证码发送接口", "设计验证码记录表", "实现验证码校验逻辑", "限制发送频率"],
        "security_constraints": "验证码不能明文长期保存，需设置有效期和重试限制"
    },
    {
        "module_name": "密码找回",
        "category": "安全认证",
        "aliases": ["忘记密码", "重置密码", "找回密码", "修改密码"],
        "required_elements": ["身份校验", "验证码确认", "新密码设置", "密码强度校验"],
        "preconditions": ["账号存在", "用户可以接收验证码"],
        "exception_scenarios": ["账号不存在", "验证码错误", "验证码过期", "新密码强度不足"],
        "typical_tasks": ["设计找回密码页面", "实现重置密码接口", "更新密码字段", "记录密码修改日志"],
        "security_constraints": "密码重置需校验身份，旧密码和新密码不能明文传输或保存"
    },
    {
        "module_name": "用户管理",
        "category": "后台管理",
        "aliases": ["用户信息管理", "账号管理", "用户维护", "用户管理类", "管理用户", "用户列表", "用户状态"],
        "required_elements": ["用户信息查询", "用户信息修改", "用户状态管理", "权限校验", "用户列表分页"],
        "preconditions": ["管理员已登录", "目标用户存在"],
        "exception_scenarios": ["用户不存在", "无权限操作", "数据更新失败", "用户状态冲突"],
        "typical_tasks": ["设计用户管理页面", "实现用户查询接口", "实现用户状态修改接口", "设计用户信息表字段", "实现分页查询"],
        "security_constraints": "涉及个人信息的字段需遵循最小可见原则，管理员操作需记录日志"
    },
    {
        "module_name": "权限管理",
        "category": "后台管理",
        "aliases": ["角色权限", "访问控制", "权限控制", "RBAC", "菜单权限", "接口权限"],
        "required_elements": ["角色定义", "权限分配", "菜单权限控制", "接口访问校验", "权限变更记录"],
        "preconditions": ["系统存在角色体系", "管理员具备配置权限"],
        "exception_scenarios": ["越权访问", "角色未分配权限", "权限配置冲突", "权限缓存未刷新"],
        "typical_tasks": ["设计角色权限页面", "实现权限校验中间层", "设计角色表和权限表", "实现菜单权限控制"],
        "security_constraints": "所有敏感接口必须进行身份认证和权限校验"
    },
    {
        "module_name": "个人信息",
        "category": "用户中心",
        "aliases": ["个人资料", "个人中心", "用户资料", "个人信息维护", "修改资料"],
        "required_elements": ["信息展示", "信息修改", "头像更新", "联系方式校验", "敏感字段脱敏"],
        "preconditions": ["用户已登录", "用户信息存在"],
        "exception_scenarios": ["用户信息不存在", "修改失败", "联系方式格式错误", "头像上传失败"],
        "typical_tasks": ["设计个人中心页面", "实现个人信息查询接口", "实现个人信息修改接口", "设计用户扩展信息表"],
        "security_constraints": "个人敏感信息展示应做脱敏处理"
    },

    # 二、电商交易类
    {
        "module_name": "商品管理",
        "category": "电商交易",
        "aliases": ["商品维护", "商品信息管理", "商品录入", "电商商品", "SKU管理", "SPU管理"],
        "required_elements": ["商品新增", "商品修改", "商品删除", "商品状态管理", "商品分类"],
        "preconditions": ["管理员已登录", "商品分类已存在"],
        "exception_scenarios": ["商品不存在", "商品编号重复", "分类不存在", "商品已被订单引用"],
        "typical_tasks": ["设计商品管理页面", "实现商品增删改查接口", "设计商品表", "实现商品状态切换逻辑"],
        "security_constraints": "商品数据修改需记录操作日志"
    },
    {
        "module_name": "购物车",
        "category": "电商交易",
        "aliases": ["加入购物车", "购物车管理", "车篮", "选购商品", "电商购物车"],
        "required_elements": ["加入商品", "修改数量", "删除商品", "购物车列表展示", "商品库存校验"],
        "preconditions": ["用户已登录", "商品已上架"],
        "exception_scenarios": ["库存不足", "商品已下架", "购物车数据失效", "商品数量非法"],
        "typical_tasks": ["设计购物车页面", "实现购物车接口", "设计购物车表", "实现数量更新逻辑"],
        "security_constraints": "用户购物车数据必须与账号绑定，禁止越权访问"
    },
    {
        "module_name": "订单管理",
        "category": "电商交易",
        "aliases": ["订单", "订单处理", "订单维护", "下单", "创建订单", "电商订单", "电商订单支付类"],
        "required_elements": ["订单创建", "订单查询", "订单状态流转", "订单明细展示", "订单编号生成"],
        "preconditions": ["用户已登录", "商品和库存有效", "收货地址有效"],
        "exception_scenarios": ["订单不存在", "库存不足", "订单状态异常", "重复下单", "订单创建失败"],
        "typical_tasks": ["设计订单页面", "实现订单创建接口", "设计订单表和订单明细表", "实现订单状态更新逻辑"],
        "security_constraints": "订单数据需具备唯一标识并记录状态变更"
    },
    {
        "module_name": "支付",
        "category": "电商交易",
        "aliases": ["付款", "结算", "在线支付", "订单支付", "支付订单", "电商支付", "电商订单支付类"],
        "required_elements": ["流水对账", "支付状态轮询", "超时自动关闭", "支付结果回调", "支付金额校验"],
        "preconditions": ["订单已创建", "支付金额已确认", "订单处于待支付状态"],
        "exception_scenarios": ["支付失败", "支付超时", "重复支付", "支付回调异常", "支付金额不一致"],
        "typical_tasks": ["设计支付页面", "实现支付接口", "设计订单与支付流水表", "实现支付回调处理", "实现订单超时关闭"],
        "security_constraints": "金融级数据传输加密，支付回调需验签"
    },
    {
        "module_name": "库存管理",
        "category": "电商交易",
        "aliases": ["库存", "库存扣减", "库存预占", "库存同步", "防超卖"],
        "required_elements": ["库存数量", "商品编号", "库存状态", "扣减规则", "回滚机制"],
        "preconditions": ["商品存在", "库存数据有效"],
        "exception_scenarios": ["库存不足", "库存扣减失败", "并发超卖", "库存回滚失败"],
        "typical_tasks": ["设计库存表", "实现库存查询接口", "实现库存扣减逻辑", "处理库存回滚"],
        "security_constraints": "库存扣减需考虑并发一致性"
    },
    {
        "module_name": "优惠券",
        "category": "电商交易",
        "aliases": ["优惠活动", "满减券", "折扣券", "优惠码", "营销券"],
        "required_elements": ["优惠规则", "有效期", "使用门槛", "适用范围", "核销状态"],
        "preconditions": ["用户已登录", "优惠券处于有效期"],
        "exception_scenarios": ["优惠券过期", "不满足使用门槛", "优惠券已使用", "优惠规则冲突"],
        "typical_tasks": ["设计优惠券页面", "实现优惠券领取接口", "设计优惠券表", "实现优惠计算逻辑"],
        "security_constraints": "优惠券核销需防止重复使用"
    },
    {
        "module_name": "物流配送",
        "category": "电商交易",
        "aliases": ["物流", "配送", "快递", "发货", "物流跟踪"],
        "required_elements": ["收货地址", "物流单号", "配送状态", "承运方", "状态更新时间"],
        "preconditions": ["订单已支付", "收货地址有效"],
        "exception_scenarios": ["地址无效", "物流信息同步失败", "配送异常", "物流单号不存在"],
        "typical_tasks": ["设计物流信息页面", "实现物流查询接口", "设计物流表", "实现物流状态更新"],
        "security_constraints": "收货人联系方式展示需脱敏"
    },
    {
        "module_name": "售后退款",
        "category": "电商交易",
        "aliases": ["退款", "退货", "售后", "售后申请", "退款申请"],
        "required_elements": ["售后原因", "订单信息", "退款金额", "审核状态", "退款渠道"],
        "preconditions": ["订单存在", "订单满足售后条件"],
        "exception_scenarios": ["超过售后期限", "订单状态不允许退款", "退款失败", "重复申请售后"],
        "typical_tasks": ["设计售后申请页面", "实现售后接口", "设计售后记录表", "实现退款状态流转"],
        "security_constraints": "退款金额需与订单金额进行一致性校验"
    },

    # 三、内容互动与消息
    {
        "module_name": "搜索",
        "category": "通用功能",
        "aliases": ["查询", "关键字搜索", "检索", "筛选", "高级查询"],
        "required_elements": ["关键字输入", "结果列表展示", "分页", "筛选条件", "排序条件"],
        "preconditions": ["目标数据已建立", "数据可被检索"],
        "exception_scenarios": ["无搜索结果", "关键字非法", "分页参数异常", "查询超时"],
        "typical_tasks": ["设计搜索页面", "实现搜索接口", "实现分页与筛选逻辑", "优化查询语句"],
        "security_constraints": "搜索接口需防范恶意注入和高频刷接口行为"
    },
    {
        "module_name": "文件上传",
        "category": "通用功能",
        "aliases": ["上传文件", "上传图片", "附件上传", "图片上传", "导入附件"],
        "required_elements": ["文件类型校验", "文件大小限制", "上传路径管理", "上传结果反馈", "文件记录"],
        "preconditions": ["用户已登录", "上传目录可用"],
        "exception_scenarios": ["文件过大", "格式不支持", "上传失败", "存储空间不足"],
        "typical_tasks": ["设计上传组件", "实现文件上传接口", "设计文件记录表", "实现文件校验逻辑"],
        "security_constraints": "必须限制可上传文件类型，防止恶意脚本文件进入系统"
    },
    {
        "module_name": "消息通知",
        "category": "消息中心",
        "aliases": ["通知", "消息提醒", "站内消息", "消息推送", "通知公告"],
        "required_elements": ["消息生成", "消息列表展示", "已读未读状态", "消息触发规则", "通知对象"],
        "preconditions": ["用户存在", "触发条件成立"],
        "exception_scenarios": ["消息发送失败", "消息重复推送", "消息状态不同步", "接收人不存在"],
        "typical_tasks": ["设计通知页面", "实现消息接口", "设计消息表", "实现已读状态更新逻辑"],
        "security_constraints": "消息内容应避免泄露敏感业务信息"
    },
    {
        "module_name": "评论评价",
        "category": "内容互动",
        "aliases": ["评价", "评论", "用户评价", "商品评价", "评分"],
        "required_elements": ["评论内容", "评分", "评论对象", "发布时间", "审核状态"],
        "preconditions": ["用户已登录", "目标对象存在"],
        "exception_scenarios": ["评论内容为空", "重复评价", "目标对象不存在", "评论包含敏感词"],
        "typical_tasks": ["设计评论区域", "实现评论提交接口", "设计评论表", "实现评分统计逻辑"],
        "security_constraints": "评论内容需进行敏感词过滤和长度限制"
    },
    {
        "module_name": "收藏关注",
        "category": "内容互动",
        "aliases": ["收藏", "关注", "取消收藏", "取消关注", "我的收藏"],
        "required_elements": ["收藏对象", "用户标识", "收藏状态", "收藏时间"],
        "preconditions": ["用户已登录", "目标对象存在"],
        "exception_scenarios": ["重复收藏", "取消不存在的收藏", "目标对象已删除"],
        "typical_tasks": ["设计收藏按钮", "实现收藏接口", "设计收藏关系表", "实现收藏状态查询"],
        "security_constraints": "收藏关系必须与当前登录用户绑定"
    },

    # 四、后台管理与组织流程
    {
        "module_name": "内容管理",
        "category": "后台管理",
        "aliases": ["文章管理", "公告管理", "轮播图管理", "内容发布", "资讯管理"],
        "required_elements": ["标题", "正文", "发布状态", "发布时间", "内容分类"],
        "preconditions": ["管理员已登录", "内容信息完整"],
        "exception_scenarios": ["内容为空", "发布失败", "内容不存在", "标题重复"],
        "typical_tasks": ["设计内容管理页面", "实现内容增删改查接口", "设计内容表", "实现发布状态切换"],
        "security_constraints": "内容发布需记录操作人和操作时间"
    },
    {
        "module_name": "系统配置",
        "category": "后台管理",
        "aliases": ["配置管理", "参数配置", "系统参数", "站点配置", "基础配置"],
        "required_elements": ["配置键", "配置值", "配置说明", "生效范围", "配置状态"],
        "preconditions": ["管理员具备配置权限"],
        "exception_scenarios": ["配置项不存在", "配置值非法", "配置更新失败", "配置冲突"],
        "typical_tasks": ["设计配置页面", "实现配置查询接口", "设计配置表", "实现配置更新逻辑"],
        "security_constraints": "核心配置修改需记录审计日志"
    },
    {
        "module_name": "数据字典",
        "category": "后台管理",
        "aliases": ["字典管理", "枚举管理", "基础数据", "字典项", "数据项维护"],
        "required_elements": ["字典类型", "字典编码", "字典名称", "启用状态"],
        "preconditions": ["管理员已登录"],
        "exception_scenarios": ["字典编码重复", "字典项被引用", "状态更新失败", "字典类型不存在"],
        "typical_tasks": ["设计字典管理页面", "实现字典接口", "设计字典表", "实现字典缓存"],
        "security_constraints": "被业务引用的字典项不应直接删除"
    },
    {
        "module_name": "组织部门",
        "category": "后台管理",
        "aliases": ["部门管理", "组织架构", "机构管理", "部门树", "组织管理"],
        "required_elements": ["部门名称", "上级部门", "负责人", "启用状态", "层级关系"],
        "preconditions": ["管理员具备组织管理权限"],
        "exception_scenarios": ["部门名称重复", "上级部门不存在", "存在下级部门不允许删除", "层级循环"],
        "typical_tasks": ["设计部门树页面", "实现部门接口", "设计部门表", "实现层级查询"],
        "security_constraints": "部门数据修改需记录操作日志"
    },
    {
        "module_name": "审批流",
        "category": "流程协同",
        "aliases": ["审批", "审核", "流程审批", "多级审批", "请假审批", "报销审批"],
        "required_elements": ["申请人", "审批人", "审批状态", "审批意见", "流转记录"],
        "preconditions": ["申请记录已创建", "审批人具备审批权限"],
        "exception_scenarios": ["审批人不存在", "重复审批", "流程状态异常", "审批节点缺失"],
        "typical_tasks": ["设计审批页面", "实现审批接口", "设计审批记录表", "实现状态流转"],
        "security_constraints": "审批操作必须校验当前用户是否具备处理权限"
    },
    {
        "module_name": "工单管理",
        "category": "流程协同",
        "aliases": ["工单", "问题反馈", "客服工单", "处理工单", "服务工单"],
        "required_elements": ["工单标题", "问题描述", "处理人", "处理状态", "处理记录"],
        "preconditions": ["用户已登录", "问题描述完整"],
        "exception_scenarios": ["工单不存在", "重复提交", "处理状态冲突", "处理人为空"],
        "typical_tasks": ["设计工单页面", "实现工单创建接口", "设计工单表", "实现工单状态更新"],
        "security_constraints": "用户只能查看自己提交或被分配的工单"
    },

    # 五、数据统计与导入导出
    {
        "module_name": "报表统计",
        "category": "数据分析",
        "aliases": ["统计", "数据看板", "报表", "数据分析", "统计分析", "可视化看板"],
        "required_elements": ["统计维度", "时间范围", "指标口径", "图表展示", "数据汇总"],
        "preconditions": ["业务数据已产生", "用户具备查看权限"],
        "exception_scenarios": ["无统计数据", "时间范围非法", "统计口径不一致", "查询超时"],
        "typical_tasks": ["设计报表页面", "实现统计接口", "编写聚合查询", "实现图表展示"],
        "security_constraints": "统计数据应按用户权限范围展示"
    },
    {
        "module_name": "数据导出",
        "category": "数据分析",
        "aliases": ["导出", "Excel导出", "CSV导出", "下载报表", "导出报表"],
        "required_elements": ["导出字段", "导出格式", "筛选条件", "文件生成", "下载链接"],
        "preconditions": ["用户具备导出权限", "目标数据存在"],
        "exception_scenarios": ["导出数据为空", "文件生成失败", "导出数量超限", "导出权限不足"],
        "typical_tasks": ["设计导出按钮", "实现导出接口", "生成Excel文件", "限制导出数量"],
        "security_constraints": "敏感字段导出前需脱敏或进行权限校验"
    },
    {
        "module_name": "数据导入",
        "category": "数据处理",
        "aliases": ["导入", "Excel导入", "批量导入", "上传导入", "数据批量录入"],
        "required_elements": ["导入模板", "字段校验", "错误行反馈", "批量写入"],
        "preconditions": ["用户具备导入权限", "导入文件格式正确"],
        "exception_scenarios": ["模板不匹配", "字段缺失", "数据格式错误", "部分导入失败"],
        "typical_tasks": ["设计导入按钮", "实现文件解析接口", "设计导入记录表", "实现错误明细反馈"],
        "security_constraints": "导入文件需校验类型和大小，避免恶意文件上传"
    },

    # 六、教育、预约、医疗、政务等常见业务
    {
        "module_name": "课程学习",
        "category": "教育系统",
        "aliases": ["课程", "学习进度", "课程播放", "在线学习", "学习记录"],
        "required_elements": ["课程信息", "学习记录", "进度状态", "学习时长", "章节信息"],
        "preconditions": ["用户已登录", "课程已发布"],
        "exception_scenarios": ["课程不存在", "学习记录保存失败", "无权限学习", "课程已下架"],
        "typical_tasks": ["设计课程详情页面", "实现课程查询接口", "设计学习记录表", "实现进度更新"],
        "security_constraints": "付费课程需校验用户购买或授权状态"
    },
    {
        "module_name": "考试测评",
        "category": "教育系统",
        "aliases": ["考试", "测验", "答题", "在线考试", "试卷", "测评"],
        "required_elements": ["试题", "答卷", "分数", "提交时间", "考试时长"],
        "preconditions": ["考试已发布", "用户具备考试资格"],
        "exception_scenarios": ["考试已结束", "重复提交", "试题加载失败", "超时提交"],
        "typical_tasks": ["设计答题页面", "实现试题接口", "设计答卷表", "实现自动评分"],
        "security_constraints": "考试提交需防止重复提交和越权查看答案"
    },
    {
        "module_name": "预约排班",
        "category": "预约系统",
        "aliases": ["预约", "排班", "号源", "时间段预约", "挂号预约"],
        "required_elements": ["预约对象", "预约时间", "预约状态", "剩余名额", "取消规则"],
        "preconditions": ["用户已登录", "预约资源可用"],
        "exception_scenarios": ["号源不足", "时间冲突", "重复预约", "取消超时"],
        "typical_tasks": ["设计预约页面", "实现预约接口", "设计预约表", "实现时间冲突校验"],
        "security_constraints": "预约资源扣减需保证并发一致性"
    },
    {
        "module_name": "病历管理",
        "category": "医疗系统",
        "aliases": ["电子病历", "病历", "就诊记录", "诊疗记录"],
        "required_elements": ["患者信息", "诊断结果", "处方信息", "就诊时间", "医生记录"],
        "preconditions": ["患者信息存在", "医生具备查看权限"],
        "exception_scenarios": ["病历不存在", "无权访问病历", "病历保存失败"],
        "typical_tasks": ["设计病历页面", "实现病历查询接口", "设计病历表", "实现病历编辑记录"],
        "security_constraints": "医疗隐私数据必须严格权限控制并脱敏展示"
    },
    {
        "module_name": "政务申报",
        "category": "政务系统",
        "aliases": ["申报", "办事申请", "材料提交", "政务办理"],
        "required_elements": ["申请人", "申报材料", "办理状态", "受理结果", "办理时限"],
        "preconditions": ["申请人已实名", "材料格式符合要求"],
        "exception_scenarios": ["材料缺失", "材料格式错误", "重复申报", "审核不通过"],
        "typical_tasks": ["设计申报页面", "实现材料上传接口", "设计申报记录表", "实现状态流转"],
        "security_constraints": "政务材料涉及个人信息，需进行访问控制和审计"
    },

    # 七、运维集成与安全审计
    {
        "module_name": "日志审计",
        "category": "安全审计",
        "aliases": ["操作日志", "审计日志", "登录日志", "行为记录", "日志管理"],
        "required_elements": ["操作人", "操作时间", "操作对象", "操作结果", "请求来源"],
        "preconditions": ["系统发生关键操作"],
        "exception_scenarios": ["日志写入失败", "日志查询超时", "日志字段缺失"],
        "typical_tasks": ["设计日志表", "实现日志记录中间件", "设计日志查询页面", "实现日志筛选"],
        "security_constraints": "审计日志不允许普通用户删除或篡改"
    },
    {
        "module_name": "异常告警",
        "category": "系统运维",
        "aliases": ["告警", "异常监控", "错误提醒", "系统报警", "监控告警"],
        "required_elements": ["告警类型", "告警级别", "触发条件", "通知对象", "处理状态"],
        "preconditions": ["系统产生异常事件"],
        "exception_scenarios": ["告警重复发送", "通知失败", "告警规则配置错误"],
        "typical_tasks": ["设计告警规则表", "实现告警触发逻辑", "实现消息通知", "设计告警列表页面"],
        "security_constraints": "告警信息中不应暴露敏感配置和密钥"
    },
    {
        "module_name": "第三方接口",
        "category": "系统集成",
        "aliases": ["外部接口", "第三方服务", "接口对接", "API对接", "外部系统对接"],
        "required_elements": ["接口地址", "请求参数", "响应格式", "错误码", "调用凭证"],
        "preconditions": ["第三方服务可用", "接口凭证有效"],
        "exception_scenarios": ["接口超时", "签名错误", "响应格式异常", "服务不可用"],
        "typical_tasks": ["封装第三方接口客户端", "实现接口调用逻辑", "记录调用日志", "处理失败重试"],
        "security_constraints": "接口密钥不得写死在代码中"
    },
    {
        "module_name": "数据备份",
        "category": "系统运维",
        "aliases": ["备份", "恢复", "数据库备份", "数据恢复", "灾备"],
        "required_elements": ["备份范围", "备份时间", "备份文件", "恢复策略", "备份日志"],
        "preconditions": ["系统具备备份权限", "存储空间充足"],
        "exception_scenarios": ["备份失败", "备份文件损坏", "恢复失败", "存储空间不足"],
        "typical_tasks": ["设计备份任务", "实现备份接口", "记录备份日志", "实现恢复校验"],
        "security_constraints": "备份文件需限制访问权限"
    }
]


def dumps_list(value):
    return json.dumps(value or [], ensure_ascii=False)


def seed_common_knowledge():
    """
    初始化或更新数据库知识库。
    若模块已存在，则更新其内容；若不存在，则插入新记录。
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        insert_count = 0
        update_count = 0

        for item in COMMON_KNOWLEDGE_MODULES:
            module_name = item["module_name"]
            row = db.query(KnowledgeModule).filter(
                KnowledgeModule.module_name == module_name
            ).first()

            if row is None:
                row = KnowledgeModule(module_name=module_name)
                db.add(row)
                insert_count += 1
            else:
                update_count += 1

            row.category = item.get("category", "通用软件模块")
            row.aliases = dumps_list(item.get("aliases"))
            row.required_elements = dumps_list(item.get("required_elements"))
            row.preconditions = dumps_list(item.get("preconditions"))
            row.exception_scenarios = dumps_list(item.get("exception_scenarios"))
            row.typical_tasks = dumps_list(item.get("typical_tasks"))
            row.security_constraints = item.get("security_constraints", "")
            row.description = item.get("description", "")
            row.is_builtin = True

        db.commit()
        print(f"通用知识库初始化完成：新增 {insert_count} 条，更新 {update_count} 条，总计 {len(COMMON_KNOWLEDGE_MODULES)} 条。")
    finally:
        db.close()


if __name__ == "__main__":
    seed_common_knowledge()
