# TravelWise - 智能旅行清单管家

> 一个具备长期记忆、主动服务、聊天即操作的智能旅行清单系统

## 🏗️ 技术架构

- **后端**: Python 3.11+ / LangChain / LangGraph
- **前端**: React 18 / TypeScript / TailwindCSS
- **AI**: Claude API / 通义千问 API (可切换)
- **存储**: JSON文件存储 (MVP阶段) / PostgreSQL (生产)

## 📁 项目结构

```
lxqd/
├── backend/
│   ├── agents/           # 智能体核心
│   │   ├── core.py       # Agent 定义
│   │   ├── tools.py      # 工具集
│   │   ├── prompts.py    # 提示词模板
│   │   └── memory.py     # 记忆管理
│   ├── services/         # 业务服务
│   │   ├── checklist.py  # 清单生成
│   │   └── scene.py      # 场景识别
│   ├── models/           # 数据模型
│   │   └── schemas.py
│   ├── api/              # API路由
│   │   └── routes.py
│   ├── config.py         # 配置
│   └── main.py           # 入口
├── frontend/             # React前端
│   └── src/
├── data/                 # 数据存储
│   └── templates/        # 清单模板
└── README.md
```

## 🚀 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 📋 核心功能

1. **🧠 长期记忆** - 记住用户习惯、偏好、历史旅行
2. **⚡ 主动服务** - 主动提醒、预警、优化建议
3. **💬 聊天即操作** - 自然语言交互完成所有操作
4. **🎯 场景化生成** - 根据目的地+季节+人群智能生成

## 🔑 MVP范围

- ✅ 基础对话界面
- ✅ 场景化清单生成
- ✅ 清单管理（增删改查）
- ✅ 用户画像（基本信息）
- ✅ 记忆系统（习惯学习）
