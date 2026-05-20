# RSOD 检测平台后端

遥感目标检测平台的后端服务，基于 FastAPI 和 YOLO 模型实现。

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由层
│   │   └── detection.py  # 检测相关接口
│   ├── models/           # 数据模型
│   │   └── schemas.py    # Pydantic 模型定义
│   ├── services/         # 业务逻辑层
│   │   └── detection_service.py  # 检测服务
│   ├── utils/            # 工具函数
│   │   └── file_utils.py # 文件处理工具
│   ├── config.py         # 配置管理
│   └── __init__.py
├── static/               # 静态文件目录
│   ├── uploads/          # 上传图片
│   └── results/          # 检测结果
├── main.py               # 应用入口
├── requirements.txt      # 依赖包
└── run.sh                # 启动脚本
```

## 安装和运行

### 方式一：使用启动脚本

```bash
chmod +x run.sh
./run.sh
```

### 方式二：手动启动

1. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动服务
```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要接口

### 单图检测

```
POST /detection/single
Content-Type: multipart/form-data

参数:
- file: 图片文件
- model_name: 模型名称 (默认: pest-v1)

响应:
{
  "success": true,
  "message": "检测成功",
  "data": {
    "detection_id": "...",
    "image_url": "...",
    "result_image_url": "...",
    "boxes": [...],
    "total_objects": 5,
    "detection_time": 0.5,
    "model_name": "pest-v1",
    "created_at": "..."
  }
}
```

### 获取目标列表

```
GET /detection/targets/list
```

### 获取检测历史

```
GET /detection/history?page=1&page_size=10
```

### 获取检测详情

```
GET /detection/detail/{id}
```

## 配置说明

配置在 `app/config.py` 中，可以通过环境变量 `.env` 文件覆盖。

主要配置项：
- `YOLO_MODEL_PATH`: YOLO 模型文件路径
- `CONFIDENCE_THRESHOLD`: 置信度阈值
- `IOU_THRESHOLD`: IOU 阈值
- `CORS_ORIGINS`: 允许的跨域来源
