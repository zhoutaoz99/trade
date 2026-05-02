# Frontend

币安 USDⓈ-M 合约模拟交易系统前端，基于 React 19 + TypeScript + Vite + Tailwind CSS。

## 环境要求

- Node.js 20+
- npm

## 一、环境变量

`.env` 中配置后端 API 地址：

```
VITE_API_BASE_URL=http://localhost:8000
```

开发环境下，Vite 会将所有 `/api` 请求代理到 `http://localhost:8000`，因此 `VITE_API_BASE_URL` 可留空使用相对路径。

## 二、启动

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器（端口 5173，热更新）
npm run dev
```

访问 `http://localhost:5173` 即可使用（确保后端已启动）。

## 可用脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 类型检查 + 生产构建 |
| `npm run preview` | 预览生产构建 |
| `npm run lint` | ESLint 代码检查 |

## 技术栈

| 依赖 | 用途 |
|------|------|
| React 19 + TypeScript | UI 框架 |
| Vite | 构建工具与开发服务器 |
| Tailwind CSS 4 | 原子化 CSS |
| React Router 7 | 客户端路由 |
| TanStack React Query 5 | 服务端状态管理与数据获取 |
| Axios | HTTP 客户端 |
| Sonner | Toast 通知 |
| Lucide React | 图标库 |
