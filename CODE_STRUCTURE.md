# 代码结构说明

## 整体架构

```
客户端请求
    ↓
views.py (create_feedback_entry)
    ↓
services.py (create_full_feedback_entry)
    ↓
┌─────────────────────────────────────┐
│  重复检测逻辑（按顺序执行）          │
│                                     │
│  1. Store 检测                      │
│     ├─ check_and_get_store()       │
│     └─ create_store_if_needed()    │
│                                     │
│  2. Customer 检测                   │
│     ├─ check_and_get_customer()    │
│     └─ create_customer_if_needed() │
│                                     │
│  3. Feedback 检测                   │
│     ├─ check_feedback_duplicate()  │
│     └─ create_feedback()           │
│                                     │
└─────────────────────────────────────┘
    ↓
返回结果或抛出异常
```

## 文件结构

```
retailops/
├── models.py           # 数据模型定义
│   ├── Store           # store_id (unique), name
│   ├── Customer        # customer_id (unique), first_name, last_name, phone
│   └── Feedback        # customer (FK), category_code, created_at
│
├── services.py         # 业务逻辑层
│   ├── 异常类
│   │   ├── StoreConflictError
│   │   ├── CustomerWarningError
│   │   ├── FeedbackDuplicateError
│   │   └── FeedbackWarningError
│   │
│   ├── Store 检测
│   │   ├── check_and_get_store()
│   │   └── create_store_if_needed()
│   │
│   ├── Customer 检测
│   │   ├── check_and_get_customer()
│   │   └── create_customer_if_needed()
│   │
│   ├── Feedback 检测
│   │   ├── check_feedback_duplicate()
│   │   └── create_feedback()
│   │
│   └── 完整工作流
│       └── create_full_feedback_entry()
│
├── views.py            # API 端点
│   └── create_feedback_entry()
│       ├── 参数解析
│       ├── 数据验证
│       ├── 调用 services
│       └── 异常处理 (4 个不同的 except 块)
│
└── urls.py             # URL 路由
    └── POST /feedback/
```

## 数据流

### 成功场景（201 Created）

```
请求 → views.py
    ↓
解析 JSON
    ↓
验证必填字段
    ↓
services.create_full_feedback_entry()
    ↓
1. create_store_if_needed()
   → check_and_get_store()
   → Store 存在且匹配？复用 ✅
   → Store 不存在？创建新的 ✅
    ↓
2. create_customer_if_needed()
   → check_and_get_customer()
   → Customer 存在且匹配？复用 ✅
   → Customer 不存在？创建新的 ✅
    ↓
3. create_feedback()
   → check_feedback_duplicate()
   → 没有重复？继续 ✅
   → 创建 Feedback ✅
    ↓
返回 201 + {store, customer, feedback}
```

### 错误场景 1：Store ID 冲突（409）

```
请求 → views.py
    ↓
services.create_full_feedback_entry()
    ↓
create_store_if_needed()
    ↓
check_and_get_store()
    ↓
Store ID 存在但名字不同 ❌
    ↓
raise StoreConflictError
    ↓
views.py except StoreConflictError
    ↓
返回 409 + 错误信息
```

### 错误场景 2：Customer 数据冲突（400）

```
请求 → views.py
    ↓
services.create_full_feedback_entry()
    ↓
create_store_if_needed() ✅
    ↓
create_customer_if_needed()
    ↓
check_and_get_customer()
    ↓
CID 存在但名字/phone 不匹配 ⚠️
或 名字+phone 存在但 CID 不同 ⚠️
    ↓
raise CustomerWarningError
    ↓
views.py except CustomerWarningError
    ↓
返回 400 + 警告信息
```

### 错误场景 3：同一天 Feedback 重复（409）

```
请求 → views.py
    ↓
services.create_full_feedback_entry()
    ↓
create_store_if_needed() ✅
    ↓
create_customer_if_needed() ✅
    ↓
create_feedback()
    ↓
check_feedback_duplicate()
    ↓
今天已有相同 customer + category ❌
    ↓
raise FeedbackDuplicateError
    ↓
views.py except FeedbackDuplicateError
    ↓
返回 409 + 错误信息
```

### 错误场景 4：不同天 Feedback 警告（400）

```
请求 → views.py
    ↓
services.create_full_feedback_entry()
    ↓
create_store_if_needed() ✅
    ↓
create_customer_if_needed() ✅
    ↓
create_feedback()
    ↓
check_feedback_duplicate()
    ↓
之前有相同 customer + category ⚠️
且 confirm=False
    ↓
raise FeedbackWarningError
    ↓
views.py except FeedbackWarningError
    ↓
返回 400 + 警告信息
```

## 检测逻辑详解

### Store 检测

```python
def check_and_get_store(store_id, name):
    existing = Store.objects.get(store_id=store_id)
    
    if existing.name == name:
        return existing  # 复用 ✅
    else:
        raise StoreConflictError  # 冲突 ❌
```

**决策表：**

| Store ID 是否存在 | 名字是否匹配 | 结果        | HTTP 状态 |
|------------------|-------------|------------|----------|
| 不存在            | -           | 创建新的     | 201      |
| 存在              | 匹配        | 复用现有     | 201      |
| 存在              | 不匹配      | 抛出异常     | 409      |

### Customer 检测

```python
def check_and_get_customer(customer_id, first_name, last_name, phone):
    # Check 1: CID 存在？
    existing_by_cid = Customer.objects.get(customer_id=customer_id)
    
    if 名字匹配 and phone 匹配:
        return existing_by_cid  # 复用 ✅
    else:
        raise CustomerWarningError  # 警告 ⚠️
    
    # Check 2: 名字+phone 存在但 CID 不同？
    existing_by_name_phone = Customer.objects.filter(
        first_name=first_name,
        last_name=last_name,
        phone=phone
    ).first()
    
    if existing_by_name_phone:
        raise CustomerWarningError  # 警告 ⚠️
```

**决策表：**

| 场景                                | 结果        | HTTP 状态 |
|------------------------------------|------------|----------|
| CID 不存在 + 名字+phone 不存在      | 创建新的     | 201      |
| CID 存在 + 名字和 phone 都匹配      | 复用现有     | 201      |
| CID 存在 + 名字或 phone 不匹配      | 抛出异常     | 400      |
| CID 不存在 + 名字+phone 存在        | 抛出异常     | 400      |

### Feedback 检测

```python
def check_feedback_duplicate(customer, category_code, confirm=False):
    # Check 1: 今天已提交相同 category？
    same_day = Feedback.objects.filter(
        customer=customer,
        category_code=category_code,
        created_at__date=today
    ).first()
    
    if same_day:
        raise FeedbackDuplicateError  # 阻止 ❌
    
    # Check 2: 之前提交过相同 category？
    other_day = Feedback.objects.filter(
        customer=customer,
        category_code=category_code
    ).exclude(created_at__date=today).first()
    
    if other_day and not confirm:
        raise FeedbackWarningError  # 警告 ⚠️
```

**决策表：**

| 之前是否提交 | 提交日期 | confirm 参数 | 结果        | HTTP 状态 |
|-------------|---------|-------------|------------|----------|
| 否           | -       | -           | 创建新的     | 201      |
| 是           | 今天    | -           | 抛出异常     | 409      |
| 是           | 其他天  | false       | 抛出异常     | 400      |
| 是           | 其他天  | true        | 创建新的     | 201      |

## 异常处理流程

```python
# views.py 中的异常处理

try:
    result = services.create_full_feedback_entry(...)
    return JsonResponse({...}, status=201)

except services.StoreConflictError as e:
    # Store ID 冲突
    return JsonResponse({
        'error': 'Store ID conflict',
        'message': str(e)
    }, status=409)

except services.CustomerWarningError as e:
    # Customer 数据冲突
    return JsonResponse({
        'error': 'Customer data conflict',
        'warning': str(e)
    }, status=400)

except services.FeedbackDuplicateError as e:
    # 同一天 Feedback 重复
    return JsonResponse({
        'error': 'Duplicate feedback',
        'message': str(e)
    }, status=409)

except services.FeedbackWarningError as e:
    # 不同天 Feedback 警告
    return JsonResponse({
        'error': 'Duplicate feedback warning',
        'warning': str(e)
    }, status=400)

except Exception as e:
    # 其他未预期的错误
    return JsonResponse({
        'error': 'Internal server error',
        'message': str(e)
    }, status=500)
```

## 代码复杂性总结

### 当前实现的问题

1. **多个独立的异常类**（4 个）
   - StoreConflictError
   - CustomerWarningError
   - FeedbackDuplicateError
   - FeedbackWarningError

2. **View 层代码臃肿**
   - 5 个不同的 except 块
   - 每个都要手动构造 JsonResponse
   - 重复的错误处理逻辑

3. **错误格式不统一**
   - 有些用 `error` + `message`
   - 有些用 `error` + `warning`
   - 没有统一的错误代码

4. **状态码分散**
   - 409 用在两个地方
   - 400 用在两个地方
   - 需要记住每种错误用哪个状态码

5. **难以扩展**
   - 添加新的检测类型需要：
     - 创建新的异常类
     - 在 view 中添加新的 except 块
     - 决定用什么状态码
     - 设计错误响应格式

### 理想的统一错误处理

如果使用统一的错误处理机制：

```python
# 基础错误类
class BusinessError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status

# 使用示例
raise BusinessError('STORE_CONFLICT', '...', 409)

# View 层只需一个处理
except BusinessError as e:
    return JsonResponse({
        'error_code': e.code,
        'message': e.message
    }, status=e.status)
```

这样会大大简化代码！
