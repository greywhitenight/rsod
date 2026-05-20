# 遥感目标智能检测平台

> 基于YOLO11的遥感图像目标检测系统，支持飞机、油罐、立交桥、操场等多类目标识别

***

## 📋 目录

- [项目简介](#项目简介)
- [核心亮点](#核心亮点)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [开发进度](#开发进度)
- [项目结构](#项目结构)
- [使用说明](#使用说明)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

***

## 项目简介

**遥感目标智能检测平台**是一个基于深度学习的遥感图像目标检测系统，旨在实现对遥感影像中多种目标的快速、准确识别。

### 项目背景

随着遥感技术的发展，海量遥感影像数据需要高效的目标检测方法进行分析。本项目利用YOLO11深度学习模型，针对RSOD数据集进行迁移学习，实现对飞机、油罐、立交桥、操场等典型遥感目标的智能检测。

### 数据集说明

- **数据集来源**: RSOD（Remote Sensing Object Detection）数据集
- **图片数量**: 976张遥感图像
- **标注文件**: 936个XML标注文件
- **目标类别**: 4类（飞机、油罐、立交桥、操场）

***

## 核心亮点

| 亮点           | 说明                     |
| ------------ | ---------------------- |
| 🚀 **高性能推理** | 基于YOLO11，支持半精度推理，检测速度快 |
| 🎯 **多目标检测** | 支持飞机、油罐、立交桥、操场等多类目标    |
| 📊 **可视化展示** | 检测结果可视化，支持框选标注、置信度展示   |
| 🔄 **批量处理**  | 支持多张图片批量检测，异步任务队列      |
| 📱 **友好界面**  | 现代化前端界面，操作便捷           |
| 🐳 **容器化部署** | Docker一键部署，环境配置简单      |

***

## 功能特性

### 🖼️ 单图检测

- 支持上传单张遥感图像进行检测
- 实时返回检测结果和置信度
- 检测框可视化标注

### 📦 批量检测

- 支持上传多张图片批量检测
- 异步任务队列处理
- 批量结果导出

### 🎬 视频检测

- 支持视频文件上传
- 逐帧目标检测
- 检测结果视频输出

### 📜 历史记录

- 检测历史记录管理
- 支持查询和筛选
- 检测结果持久化存储

### 📈 结果分析

- 检测结果结构化输出
- PDF报告生成
- 统计分析图表

***

## 技术栈

### 前端技术

| 技术           | 版本  | 说明      |
| ------------ | --- | ------- |
| Vue.js       | 3.x | 前端框架    |
| Element Plus | 2.x | UI组件库   |
| Axios        | 1.x | HTTP客户端 |
| ECharts      | 5.x | 数据可视化   |

### 后端技术

| 技术         | 版本     | 说明     |
| ---------- | ------ | ------ |
| Python     | 3.10+  | 编程语言   |
| FastAPI    | 0.100+ | Web框架  |
| PostgreSQL | 15+    | 关系型数据库 |
| Redis      | 7+     | 缓存服务   |
| MinIO      | 2023+  | 对象存储   |
| SQLAlchemy | 2.x    | ORM框架  |

### AI核心技术

| 技术                 | 版本   | 说明     |
| ------------------ | ---- | ------ |
| PyTorch            | 2.0+ | 深度学习框架 |
| Ultralytics YOLO11 | 8.x  | 目标检测模型 |
| scikit-learn       | 1.3+ | 数据处理   |

### 工具链

| 工具             | 说明        |
| -------------- | --------- |
| Docker         | 容器化部署     |
| Docker Compose | 多容器编排     |
| Git+GitHub     | 版本控制+代码托管 |
| Pre-commit     | 代码质量检查    |

***

## 快速开始

### 环境要求

- Python 3.10+
- Docker 20.10+
- Docker Compose 2.0+

### 1. 克隆项目

```bash
git clone https://github.com/your-username/rsod-web-platform.git
cd rsod-web-platform
```

### 2. 启动服务

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d
```

### 3. 安装后端依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. 启动后端服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问服务

- 前端地址: <http://localhost:8080>
- 后端API: <http://localhost:8000/docs>

***

## 开发进度

### ✅ 已完成

| 模块    | 状态 | 说明                |
| ----- | -- | ----------------- |
| 环境搭建  | ✅  | Docker部署、依赖配置     |
| 单图检测  | ✅  | 图片上传、YOLO推理、结果展示  |
| 历史记录  | ✅  | 检测记录存储与查询         |
| 数据预处理 | ✅  | RSOD数据集XML转YOLO格式 |
| 模型训练  | ✅  | YOLO11迁移学习训练脚本    |

### 🔄 进行中

| 模块   | 状态 | 说明           |
| ---- | -- | ------------ |
| 批量检测 | 🔄 | 批量上传API、异步队列 |
| 视频检测 | 🔄 | 视频帧处理、实时推理   |

### 📋 待开发

| 模块    | 状态 | 说明          |
| ----- | -- | ----------- |
| PDF报告 | 📋 | 检测报告生成      |
| 性能优化  | 📋 | 半精度推理、流水线优化 |
| 大图像切分 | 📋 | 遥感大图处理      |

***

## 项目结构

```
rsod-web-platform/                          # 项目根目录
│
├── backend/                                # 后端代码目录
│   ├── app/                              # 应用核心模块
│   │   ├── api/                          # API路由层
│   │   │   ├── __init__.py              # 路由包初始化
│   │   │   └── detection.py             # 目标检测API接口
│   │   ├── models/                       # 数据模型层
│   │   │   ├── __init__.py
│   │   │   ├── database.py              # 数据库连接配置
│   │   │   └── schemas.py               # Pydantic数据模型
│   │   ├── services/                     # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── detection_service.py     # YOLO检测服务
│   │   │   ├── minio_service.py         # MinIO对象存储服务
│   │   │   └── redis_service.py         # Redis缓存服务
│   │   ├── utils/                        # 工具函数层
│   │   │   ├── __init__.py
│   │   │   └── file_utils.py            # 文件操作工具
│   │   ├── __init__.py
│   │   └── config.py                    # 配置管理
│   ├── models/                            # 模型文件目录
│   │   ├── yolo11n.pt                   # YOLO11n预训练模型
│   │   └── rsod_yolo11n/               # 自定义训练模型
│   │       └── weights/
│   │           ├── best.pt              # 最佳权重
│   │           └── last.pt              # 最后权重
│   ├── data/                              # 数据存储目录
│   │   └── rsod/                        # RSOD数据集
│   │       ├── images/                  # 原始遥感图像
│   │       │   ├── aircraft_*.jpg       # 飞机类图像(446张)
│   │       │   ├── oiltank_*.jpg        # 油罐类图像(165张)
│   │       │   ├── overpass_*.jpg       # 立交桥类图像(176张)
│   │       │   └── playground_*.jpg     # 操场类图像(149张)
│   │       ├── annotations/             # XML标注文件(PASCAL VOC格式)
│   │       │   ├── aircraft_*.xml
│   │       │   ├── oiltank_*.xml
│   │       │   ├── overpass_*.xml
│   │       │   └── playground_*.xml
│   │       └── yolo_dataset/            # YOLO格式数据集
│   │           ├── images/              # 图像文件
│   │           │   ├── train/          # 训练集(~749张)
│   │           │   └── val/            # 验证集(~187张)
│   │           ├── labels/              # 标注文件(YOLO txt格式)
│   │           │   ├── train/          # 训练集标签
│   │           │   └── val/            # 验证集标签
│   │           └── rsod.yaml           # 数据集配置文件
│   ├── uploads/                           # 上传文件临时目录
│   │   └── [临时上传的图片文件]
│   ├── results/                           # 检测结果存储目录
│   │   └── [检测结果图像和JSON]
│   ├── train_model.py                    # 模型训练脚本
│   ├── convert_rsod.py                   # 数据集格式转换脚本
│   ├── requirements.txt                   # Python依赖列表
│   ├── main.py                           # FastAPI应用入口
│   └── .venv/                            # Python虚拟环境
│
├── frontend/                              # 前端代码目录
│   ├── public/                           # 静态公共资源
│   │   ├── favicon.ico                  # 网站图标
│   │   └── index.html                   # HTML模板
│   ├── src/                             # 前端源代码
│   │   ├── api/                        # API接口层
│   │   │   ├── detection.ts            # 检测相关API
│   │   │   ├── history.ts             # 历史记录API
│   │   │   └── upload.ts              # 文件上传API
│   │   ├── assets/                     # 前端资源
│   │   │   ├── images/                # 图片资源
│   │   │   └── styles/                # 样式文件
│   │   │       └── main.css           # 全局样式
│   │   ├── components/                 # Vue组件
│   │   │   ├── common/                # 通用组件
│   │   │   │   ├── ImageUploader.vue  # 图片上传组件
│   │   │   │   ├── ResultViewer.vue   # 结果查看组件
│   │   │   │   └── Loading.vue        # 加载状态组件
│   │   │   └── detection/              # 检测相关组件
│   │   │       ├── DetectionPanel.vue # 检测面板
│   │   │       ├── ImageList.vue      # 图片列表
│   │   │       └── BatchUpload.vue    # 批量上传
│   │   ├── router/                     # 路由配置
│   │   │   └── index.ts               # 路由定义
│   │   ├── store/                      # 状态管理
│   │   │   ├── detection.ts           # 检测状态
│   │   │   └── user.ts                # 用户状态
│   │   ├── views/                      # 页面视图
│   │   │   ├── Home.vue               # 首页
│   │   │   ├── Detection.vue          # 检测页面
│   │   │   ├── History.vue            # 历史记录页面
│   │   │   └── Analysis.vue           # 结果分析页面
│   │   ├── App.vue                     # 根组件
│   │   └── main.ts                     # 前端入口文件
│   ├── package.json                     # 前端依赖配置
│   ├── vite.config.ts                  # Vite配置
│   └── tsconfig.json                   # TypeScript配置
│
├── storage/                              # 持久化存储目录
│   ├── minio/                          # MinIO对象存储数据
│   │   ├── data/                      # MinIO数据存储
│   │   │   └── rsod-bucket/          # 存储桶
│   │   │       ├── images/           # 用户上传图片
│   │   │       └── results/          # 检测结果图片
│   │   └── config/                   # MinIO配置
│   ├── postgres/                       # PostgreSQL数据库
│   │   ├── data/                      # 数据库文件
│   │   └── init/                     # 初始化脚本
│   │       └── init_db.sql           # 数据库初始化SQL
│   └── redis/                          # Redis缓存数据
│       └── data/                      # Redis持久化文件
│
├── docs/                                 # 项目文档
│   └── 实训计划-优化版.md             # 实训计划文档
│
├── docker/                              # Docker相关配置
│   └── Dockerfile.backend              # 后端Docker镜像
│
├── .env                                  # 环境变量配置
├── .env.example                         # 环境变量示例
├── docker-compose.yml                   # Docker Compose配置
├── Dockerfile                           # Docker镜像配置
├── .gitignore                          # Git忽略配置
├── README.md                            # 项目说明文档
└── LICENSE                              # 项目许可证
```

### 目录说明

#### 后端目录结构

| 目录 | 说明 |
|------|------|
| `backend/app/api/` | API路由定义，处理HTTP请求 |
| `backend/app/models/` | 数据模型和数据库结构 |
| `backend/app/services/` | 核心业务逻辑服务 |
| `backend/app/utils/` | 通用工具函数 |
| `backend/models/` | YOLO模型权重文件 |
| `backend/data/rsod/` | RSOD遥感数据集 |
| `backend/uploads/` | 临时上传文件 |
| `backend/results/` | 检测结果输出 |

#### 前端目录结构

| 目录 | 说明 |
|------|------|
| `frontend/src/api/` | 封装API调用接口 |
| `frontend/src/components/` | Vue组件（可复用UI组件） |
| `frontend/src/views/` | 页面级组件（路由页面） |
| `frontend/src/router/` | Vue Router路由配置 |
| `frontend/src/store/` | Pinia状态管理 |

#### 数据存储目录结构

| 目录 | 说明 | 存储内容 |
|------|------|---------|
| `storage/minio/` | 对象存储 | 用户上传图片、检测结果 |
| `storage/postgres/` | 关系数据库 | 结构化数据（用户信息、检测记录） |
| `storage/redis/` | 缓存数据库 | 会话缓存、热点数据 |

#### MinIO存储桶结构

```
rsod-bucket/                    # 主存储桶
├── images/                    # 原始上传图片
│   ├── {user_id}/
│   │   ├── {timestamp}_{filename}
│   │   └── ...
├── results/                   # 检测结果图片
│   ├── {user_id}/
│   │   ├── {timestamp}_result.jpg
│   │   └── ...
└── models/                    # 模型文件备份
    └── yolo11n.pt
```

#### PostgreSQL数据库表结构

```sql
-- 检测记录表
CREATE TABLE detection_records (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    image_path TEXT,
    result_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

***

## 使用说明

### 模型训练

```bash
cd backend
source .venv/bin/activate
python train_model.py
```

### 数据转换

```bash
cd backend
source .venv/bin/activate
python convert_rsod.py
```

### API接口

**单图检测接口**

```
POST /api/detection/single
Content-Type: multipart/form-data

参数:
- file: 图片文件
- model_name: 模型名称(可选)

返回:
{
  "success": true,
  "message": "检测成功",
  "result": {
    "boxes": [...],
    "confidences": [...],
    "class_names": [...]
  }
}
```

***

## 贡献指南

欢迎贡献代码！请遵循以下流程：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx feature'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

***

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

***

**项目状态**: 🚀 开发中\
**最后更新**: 2026-05-17\
**联系邮箱**: <your-email@example.com>
