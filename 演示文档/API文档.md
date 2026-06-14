# UserStoryLLM API 文档

## 基础信息

- **基础 URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

## API 端点列表

### 1. 健康检查

**端点**: `GET /health`

检查服务是否正常运行。

**请求示例**:
```bash
curl http://localhost:8000/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

---

### 2. 生成用户故事

**端点**: `POST /generate_user_stories`

从自然语言需求生成用户故事。

**请求体**:
```json
{
  "requirement": "我需要一个订单支付功能"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "生成成功",
  "data": {
    "requirement": "我需要一个订单支付功能",
    "stories": [
      {
        "id": 1,
        "story": "作为在线购物用户，我想通过多种支付方式完成支付，以便快速获得商品",
        "acceptance_criteria": [
          "支持支付宝、微信、银行卡支付",
          "支付成功后返回确认页面",
          "支付失败显示错误提示"
        ]
      },
      {
        "id": 2,
        "story": "作为系统管理员，我想查看所有支付记录和报表，以便了解销售情况",
        "acceptance_criteria": [
          "支持按日期、支付方式筛选",
          "显示日/周/月销售统计",
          "支持导出数据"
        ]
      },
      {
        "id": 3,
        "story": "作为财务人员，我想对账户资金进行对账，以便确保账户准确无误",
        "acceptance_criteria": [
          "对账单显示收入和支出",
          "支持标记已对账项目",
          "异常交易需要标记"
        ]
      }
    ],
    "generation_time_ms": 2450.50
  }
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| requirement | string | 是 | 自然语言需求描述，建议 10-500 字 |

---

### 3. 生成任务

**端点**: `POST /generate_tasks`

将用户故事拆解为具体的实现任务。

**请求体**:
```json
{
  "story": "作为在线购物用户，我想通过多种支付方式完成支付，以便快速获得商品"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "拆解成功",
  "data": {
    "story": "作为在线购物用户，我想通过多种支付方式完成支付，以便快速获得商品",
    "tasks": [
      {
        "id": 1,
        "task": "设计支付表结构，包含订单ID、支付方式、金额、状态等字段",
        "category": "backend",
        "priority": "high",
        "estimated_days": 1
      },
      {
        "id": 2,
        "task": "实现支付接口，调用第三方支付 API（支付宝/微信），处理回调",
        "category": "backend",
        "priority": "high",
        "estimated_days": 3
      },
      {
        "id": 3,
        "task": "实现订单-支付关联和状态管理，支持查询支付状态",
        "category": "backend",
        "priority": "high",
        "estimated_days": 2
      },
      {
        "id": 4,
        "task": "设计支付方式选择和金额确认页面",
        "category": "frontend",
        "priority": "high",
        "estimated_days": 1
      },
      {
        "id": 5,
        "task": "实现支付流程交互，处理成功/失败结果展示",
        "category": "frontend",
        "priority": "high",
        "estimated_days": 2
      },
      {
        "id": 6,
        "task": "集成第三方支付 SDK（如支付宝 H5、微信 H5）",
        "category": "frontend",
        "priority": "medium",
        "estimated_days": 2
      }
    ],
    "generation_time_ms": 1850.30
  }
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| story | string | 是 | 用户故事描述 |

---

### 4. 生成代码

**端点**: `POST /generate_code`

基于用户故事和任务生成代码框架。

**请求体**:
```json
{
  "requirement": "订单支付功能",
  "story": "作为在线购物用户，我想通过多种支付方式完成支付",
  "tasks": [
    {
      "task": "实现支付接口",
      "category": "backend"
    },
    {
      "task": "设计支付页面",
      "category": "frontend"
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "生成成功",
  "data": {
    "backend_code": "# 支付接口实现\nfrom fastapi import APIRouter\nfrom pydantic import BaseModel\n\nrouter = APIRouter(prefix=\"/payment\")\n\nclass PaymentRequest(BaseModel):\n    order_id: str\n    amount: float\n    payment_method: str  # alipay, wechat, bank\n\n@router.post(\"/pay\")\nasync def process_payment(request: PaymentRequest):\n    \"\"\"\n    处理支付请求\n    \"\"\"\n    # 验证订单\n    # 调用第三方支付 API\n    # 保存支付记录\n    # 返回支付结果\n    pass\n\n@router.get(\"/status/{payment_id}\")\nasync def get_payment_status(payment_id: str):\n    \"\"\"\n    查询支付状态\n    \"\"\"\n    pass",
    "frontend_code": "// 支付页面组件\n<template>\n  <div class=\"payment-page\">\n    <h2>选择支付方式</h2>\n    <div class=\"payment-methods\">\n      <button \n        v-for=\"method in paymentMethods\"\n        :key=\"method\"\n        @click=\"selectPaymentMethod(method)\"\n      >\n        {{ method }}\n      </button>\n    </div>\n    <button @click=\"handlePayment\" :disabled=\"!selectedMethod\">\n      确认支付\n    </button>\n  </div>\n</template>\n\n<script>\nexport default {\n  data() {\n    return {\n      paymentMethods: ['支付宝', '微信', '银行卡'],\n      selectedMethod: null\n    }\n  },\n  methods: {\n    selectPaymentMethod(method) {\n      this.selectedMethod = method\n    },\n    async handlePayment() {\n      // 调用支付接口\n      // 处理支付结果\n    }\n  }\n}\n</script>",
    "generation_time_ms": 3200.45
  }
}
```

---

### 5. 从代码提取需求

**端点**: `POST /extract_requirement_from_code`

分析现有代码并生成对应的需求描述。

**请求体**:
```json
{
  "code": "def login_user(username, password):\n    # 验证用户名和密码\n    user = db.query(User).filter(User.username == username).first()\n    if user and verify_password(password, user.password_hash):\n        return generate_token(user.id)\n    return None"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "提取成功",
  "data": {
    "extracted_requirement": "用户登录功能，包括用户验证、密码校验和令牌生成",
    "generated_stories": [
      "作为系统用户，我想输入用户名和密码登录，以便访问系统功能",
      "作为系统管理员，我想确保登录过程安全可靠，以便保护用户数据"
    ],
    "code_analysis": {
      "language": "python",
      "main_functions": ["login_user"],
      "dependencies": ["database", "authentication", "token_generation"]
    },
    "generation_time_ms": 1650.20
  }
}
```

---

### 6. 知识库 - 添加模块

**端点**: `POST /kb/add_module`

向知识库添加新的系统模块。

**请求体**:
```json
{
  "module_name": "评论评分",
  "category": "用户交互模块",
  "aliases": ["用户评价", "商品评分", "评论系统"],
  "required_elements": ["评论内容", "星级评分", "发表时间"],
  "preconditions": ["用户已购买商品", "用户已登录"],
  "exception_scenarios": ["重复评论", "评论被举报", "用户被禁言"],
  "typical_tasks": [
    "设计评论表结构",
    "实现评论发表接口",
    "实现评论展示和筛选"
  ],
  "security_constraints": "评论内容需要审核，禁止发布违规内容",
  "description": "用户对商品进行评价和评分"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "模块添加成功",
  "data": {
    "module_id": 25,
    "module_name": "评论评分",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 7. 知识库 - 查询统计

**端点**: `GET /kb/statistics`

获取知识库统计信息。

**响应示例**:
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "total_modules": 25,
    "categories": {
      "用户管理": 5,
      "商品管理": 4,
      "订单支付": 6,
      "用户交互": 5,
      "其他": 5
    },
    "most_used_modules": [
      "用户管理",
      "订单管理",
      "购物车"
    ]
  }
}
```

---

## 错误处理

所有错误响应都采用统一格式：

```json
{
  "success": false,
  "message": "具体错误信息",
  "data": null
}
```

**常见错误码**:

| 错误 | 状态码 | 说明 |
|-----|--------|------|
| 无效请求 | 400 | 请求参数不合法 |
| API 密钥无效 | 401 | 未提供有效的 API 密钥 |
| 服务不可用 | 503 | 后端服务暂时不可用 |

---

## 速率限制

- 标准限制：每分钟 60 请求
- VIP 限制：每分钟 300 请求

超限时返回 429 状态码。

---

## 性能优化

- 使用异步处理长时间的 AI 生成任务
- 缓存常见知识模块
- 支持批量操作以减少 API 调用

