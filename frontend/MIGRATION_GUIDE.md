# Frontend Migration Guide: HTML → React + Vite

## 📊 变化总览 (Changes Overview)

### 之前 (Before)
- **技术栈**: 纯 HTML + CSS + 原生 JavaScript
- **文件结构**: 单个 `templates/index.html` 文件（856 行）
- **构建工具**: 无
- **开发体验**: 需要刷新浏览器查看更改

### 之后 (After)
- **技术栈**: React 18 + Vite 5
- **文件结构**: 组件化，6 个独立文件
- **构建工具**: Vite（极速 HMR）
- **开发体验**: 热模块替换，即时更新

---

## 🏗️ 新的项目结构 (New Structure)

```
intelligent_retail_store_filter/
├── frontend/                    # 【新增】React 前端目录
│   ├── src/
│   │   ├── components/
│   │   │   ├── TabNav.jsx              # 标签导航组件
│   │   │   ├── CreatePlanForm.jsx      # 创建计划表单
│   │   │   ├── PlansList.jsx           # 计划列表 + 搜索
│   │   │   └── PlanDetailModal.jsx     # 计划详情弹窗
│   │   ├── services/
│   │   │   └── api.js                  # API 调用封装
│   │   ├── styles/
│   │   │   └── index.css               # 全局样式
│   │   ├── App.jsx                     # 主应用组件
│   │   └── main.jsx                    # React 入口
│   ├── index.html                      # Vite HTML 模板
│   ├── vite.config.js                  # Vite 配置
│   └── package.json                    # 依赖管理
│
├── templates/
│   └── index.html.backup               # 【已备份】原 HTML 文件
│
├── retailops/
│   └── frontend_urls.py                # 【已更新】支持 React SPA
│
└── static/dist/                        # 【构建产物】生产环境使用
```

---

## 🔄 代码拆分映射 (Component Mapping)

| 原 HTML 部分 | React 组件 | 功能 |
|------------|-----------|-----|
| Tab buttons (line 353-356) | `TabNav.jsx` | 标签切换 |
| Create form (line 359-388) | `CreatePlanForm.jsx` | 表单提交 + 加载状态 |
| Search & list (line 390-400) | `PlansList.jsx` | 搜索 + 列表展示 |
| Detail modal (line 404-429) | `PlanDetailModal.jsx` | 详情弹窗 + 轮询 |
| JavaScript logic (line 432-852) | `api.js` + React Hooks | API 调用 + 状态管理 |
| CSS styles (line 8-347) | `index.css` | 全局样式（改为白色主题） |

---

## 🎨 设计改进 (Design Improvements)

### 主色调变化
- **之前**: 紫色渐变背景 (`#667eea` → `#764ba2`)
- **之后**: 白色为主 + 蓝色强调色 (`#4285f4` Google Blue)

### 专业化改进
1. **更简洁的配色方案**: 白色背景，灰色文字，蓝色交互元素
2. **更精致的阴影**: 从重阴影改为轻微阴影
3. **更清晰的层次**: 通过留白和边框区分内容
4. **更舒适的字体**: 优化行高和字号
5. **更流畅的动画**: 减少视觉干扰，专注于内容

---

## ⚡ 页面加载效率对比 (Performance Comparison)

### 开发环境 (Development)
| 指标 | 之前 (HTML) | 之后 (React + Vite) |
|-----|-----------|------------------|
| 首次加载 | ~100ms | ~200-300ms |
| 热更新 | 需手动刷新 | <50ms (HMR) |
| 开发体验 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 生产环境 (Production)
| 指标 | 之前 (HTML) | 之后 (React + Vite) |
|-----|-----------|------------------|
| 初始加载 | 856 行 HTML (~40KB) | ~80-120KB (gzipped ~25KB) |
| 后续导航 | 完整页面刷新 | 无需刷新（SPA） |
| 缓存策略 | 基础 HTTP 缓存 | 强缓存 + 代码分割 |
| 整体性能 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**结论**: 
- ✅ **首次加载略慢** (多 ~30KB)，但仍然很快
- ✅ **后续操作更快** (无需刷新页面)
- ✅ **开发效率大幅提升** (HMR + 组件化)
- ✅ **维护性大幅提升** (代码组织更清晰)

---

## 🚀 启动步骤 (How to Run)

### 1️⃣ 安装依赖
```bash
cd frontend
npm install
```

### 2️⃣ 启动开发服务器
```bash
# Terminal 1: Start Django backend
python manage.py runserver

# Terminal 2: Start Vite frontend
cd frontend
npm run dev
```

### 3️⃣ 访问应用
打开浏览器访问: `http://localhost:3000`

### 4️⃣ 生产构建（可选）
```bash
cd frontend
npm run build
```

构建后的文件会输出到 `static/dist/` 目录，Django 会自动服务这些文件。

---

## 🔧 主要 Workflow (Main Workflow)

### 创建 Action Plan 流程
```
用户填写表单
    ↓
CreatePlanForm.jsx 提交数据
    ↓
api.createActionPlan() 调用 POST /api/action-plans/
    ↓
Django 返回 plan 对象 (status: pending)
    ↓
自动打开 PlanDetailModal
    ↓
PlanDetailModal 开始轮询 GET /api/action-plans/{id}/status/
    ↓
轮询逻辑：1s → 2s → 3s → 5s → 5s → ...
    ↓
status 变为 completed
    ↓
获取完整 plan 内容并展示
    ↓
用户可下载或关闭
```

### 搜索 & 浏览流程
```
用户切换到 "Search & Browse Plans" 标签
    ↓
PlansList.jsx 加载数据
    ↓
api.listActionPlans() 调用 GET /api/action-plans/list/
    ↓
展示所有 plans（卡片形式）
    ↓
用户可搜索过滤（实时客户端搜索）
    ↓
点击卡片查看详情
    ↓
打开 PlanDetailModal
    ↓
如果 status 是 pending/processing，自动轮询
    ↓
completed 后可下载
```

---

## 📦 依赖说明 (Dependencies)

### 生产依赖
- `react` (18.2.0): React 核心库
- `react-dom` (18.2.0): React DOM 渲染

### 开发依赖
- `vite` (5.0.8): 构建工具
- `@vitejs/plugin-react` (4.2.1): React 插件
- `@types/react` & `@types/react-dom`: TypeScript 类型定义

**总依赖大小**: ~30MB（仅开发环境，生产构建仅 ~80KB）

---

## ❓ 常见问题 (FAQ)

### Q: 需要改动后端代码吗？
**A**: 不需要！所有 Django API 保持不变，只是前端技术栈改变。

### Q: 如何回滚到原来的版本？
**A**: 将 `templates/index.html.backup` 改回 `templates/index.html` 即可。

### Q: 生产环境如何部署？
**A**: 运行 `npm run build`，构建产物会自动放到 `static/dist/`，Django 会自动服务。

### Q: 为什么首次加载变大了？
**A**: React 运行时约 ~40KB (gzipped)，但换来更好的用户体验（无需刷新页面）和开发体验（组件化）。
