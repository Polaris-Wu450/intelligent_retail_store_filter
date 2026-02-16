# 🚀 Quick Start Guide - Retail Action Plan Generator MVP

这是一个最小可行产品（MVP），包含前端、后端（Django）、PostgreSQL数据库和Claude AI集成。

## 📋 系统要求

- Docker
- Docker Compose

## 🛠️ 快速启动步骤

### 1. 启动所有服务

```bash
docker-compose up --build
```

这将启动：
- PostgreSQL 数据库（端口 5432）
- Django 后端服务器（端口 8000）

### 2. 初始化数据库

在新的终端窗口中运行：

```bash
docker-compose exec web bash init_db.sh
```

或者分步执行：

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 3. 访问应用

打开浏览器访问：
```
http://localhost:8000
```

## 📝 使用说明

### 创建新的行动计划

1. 在 "Create New Plan" 标签页中填写表单：
   - **Store Name**: 商店名称（例如：Downtown Store #42）
   - **Store Location**: 商店地址（例如：123 Main St, San Francisco, CA）
   - **Issue Description**: 问题描述（描述商店遇到的问题或挑战）

2. 点击 "Generate Action Plan" 按钮

3. 等待系统生成行动计划（这是同步操作，会等待几秒钟）

4. 查看生成的行动计划结果

### 搜索和浏览行动计划

1. 切换到 "Search & Browse Plans" 标签页

2. 使用搜索框按以下内容搜索：
   - 商店名称
   - 商店位置
   - 问题描述

3. 点击 "View Details" 查看完整的行动计划

4. 对于已完成的计划，点击 "Download" 下载为文本文件

## 🔌 API 端点

### 创建行动计划
```bash
POST http://localhost:8000/api/action-plans/
Content-Type: application/json

{
  "store_name": "Downtown Store #42",
  "store_location": "123 Main St, San Francisco, CA",
  "issue_description": "Low customer satisfaction scores"
}
```

### 获取单个行动计划
```bash
GET http://localhost:8000/api/action-plans/{plan_id}/
```

### 获取所有行动计划列表
```bash
GET http://localhost:8000/api/action-plans/list/
```

## 📊 数据库结构

**ActionPlan 表结构：**
- `id`: 主键
- `store_name`: 商店名称
- `store_location`: 商店位置
- `issue_description`: 问题描述
- `status`: 状态（pending, processing, completed, failed）
- `plan_content`: 生成的行动计划内容
- `error_message`: 错误信息（如果失败）
- `created_at`: 创建时间
- `updated_at`: 更新时间

## ✨ 新功能

### 🔍 搜索功能
- 实时搜索所有行动计划
- 按商店名称、位置或问题描述过滤
- 显示所有计划的列表，包含状态标识

### 📥 下载功能
- 将已完成的行动计划下载为文本文件
- 包含完整的商店信息、问题描述和生成的行动计划
- 文件名自动包含计划ID和商店名称

## 🔧 常用 Docker 命令

### 查看运行中的容器
```bash
docker-compose ps
```

### 查看日志
```bash
docker-compose logs -f web
```

### 停止所有服务
```bash
docker-compose down
```

### 重新构建并启动
```bash
docker-compose up --build
```

### 进入 Django 容器的 shell
```bash
docker-compose exec web bash
```

### 进入 PostgreSQL 数据库
```bash
docker-compose exec db psql -U retailops -d retailops
```

## 🐛 故障排查

### 问题：端口已被占用
如果 8000 或 5432 端口已被占用，可以修改 `docker-compose.yml` 中的端口映射。

### 问题：数据库连接失败
确保数据库容器已完全启动。可以运行：
```bash
docker-compose logs db
```

### 问题：LLM API 调用失败
检查环境变量 `RETAILOPS_API_KEY` 是否正确设置在 `docker-compose.yml` 中。

### 重置整个环境
```bash
docker-compose down -v
docker-compose up --build
# 然后重新运行初始化脚本
```

## 📁 项目结构

```
intelligent_retail_store_filter/
├── config/                 # Django 项目配置
│   ├── __init__.py
│   ├── settings.py         # 主设置文件
│   ├── urls.py             # 主 URL 配置
│   └── wsgi.py
├── retailops/              # 主应用
│   ├── __init__.py
│   ├── models.py           # ActionPlan 模型
│   ├── views.py            # API 视图（包含 LLM 调用）
│   ├── urls.py             # API 路由
│   └── frontend_urls.py    # 前端路由
├── templates/
│   └── index.html          # 前端界面（搜索+下载）
├── static/                 # 静态文件目录
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # Docker 镜像配置
├── requirements.txt        # Python 依赖
├── manage.py               # Django 管理脚本
├── init_db.sh              # 数据库初始化脚本
└── QUICKSTART.md           # 本文件
```

## 🎯 特性说明

### 当前实现（MVP）
- ✅ 同步生成行动计划（用户等待生成完成）
- ✅ 美观的前端界面（标签页设计）
- ✅ PostgreSQL 数据库存储
- ✅ Claude AI 集成生成行动计划
- ✅ 状态追踪（pending → processing → completed/failed）
- ✅ 搜索功能（实时过滤）
- ✅ 下载功能（导出为文本文件）
- ✅ Docker 容器化部署

### 未来可添加的特性
- ⏳ 异步处理（使用 Celery + Redis）
- ⏳ WebSocket 实时更新
- ⏳ 用户认证和授权
- ⏳ 更复杂的错误处理和验证
- ⏳ 单元测试和集成测试
- ⏳ 日志系统
- ⏳ API 限流
- ⏳ 缓存层
- ⏳ 导出为 PDF 格式
- ⏳ 高级搜索过滤（按日期、状态等）

## 💡 开发建议

这是一个最小化的 MVP，专门设计用于学习和体验：
1. 没有复杂的分层架构
2. 没有额外的抽象层
3. 同步处理，便于理解流程
4. 最少的依赖和配置
5. 简单的客户端搜索和下载

当你需要扩展功能时，可以逐步添加：
- 异步任务队列
- WebSocket 支持
- 更好的错误处理
- 测试覆盖
- 服务器端分页和搜索
- 等等...

这样可以帮助你更好地理解每个组件的作用和为什么需要它们。

## 🎉 开始使用

现在你可以开始使用这个系统了！尝试：

1. 创建几个行动计划
2. 使用搜索功能查找特定的计划
3. 下载已完成的行动计划
4. 体验同步处理的等待时间（思考为什么需要异步）
5. 体验前端搜索的限制（思考为什么需要服务器端搜索）

如有问题，请检查 Docker 日志：
```bash
docker-compose logs -f
```
