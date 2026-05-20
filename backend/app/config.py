# =============================================================================
# 配置文件模块
# =============================================================================
# 功能说明：
#   - 集中管理系统所有配置项
#   - 支持从环境变量读取配置
#   - 提供各服务的连接参数
#
# 使用方式：
#   from app.config import settings
#   settings.database.host  # 获取数据库主机
#   settings.minio.port    # 获取 MinIO 端口
#
# 环境变量说明：
#   - .env 文件中的配置会覆盖默认值
#   - 部署时可通过 Docker 环境变量或系统环境变量配置
# =============================================================================

# 导入 Pydantic BaseModel，用于数据验证和设置管理
from pydantic import BaseModel

# 导入类型提示 List，用于定义列表类型
from typing import List

# 导入 os 模块，用于读取操作系统环境变量
import os

# 导入 Path 模块，用于获取文件路径
from pathlib import Path

# 导入 dotenv 模块的 load_dotenv 函数，用于加载 .env 文件
from dotenv import load_dotenv

# 获取 backend 目录路径（config.py 在 backend/app/ 下）
# 向上两级到达 backend 目录
BACKEND_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件到环境变量
# 使用 backend 目录下的 .env 文件
load_dotenv(BACKEND_DIR / ".env")


# =============================================================================
# 数据库配置类
# =============================================================================
class DatabaseConfig(BaseModel):
    """
    PostgreSQL 数据库配置

    配置项：
        host: 数据库服务器地址，默认 localhost
        port: 数据库服务端口，默认 5432（PostgreSQL 标准端口）
        username: 数据库用户名，默认 rsod_user
        password: 数据库密码，默认 rsod_password
        database: 数据库名称，默认 rsod_platform
    """

    # 数据库主机地址，从环境变量 DB_HOST 读取，默认为 localhost
    host: str = os.getenv("DB_HOST", "localhost")

    # 数据库端口，从环境变量 DB_PORT 读取，转换为整数，默认为 5432
    port: int = int(os.getenv("DB_PORT", "5432"))

    # 数据库用户名，从环境变量 DB_USERNAME 读取，默认为 rsod_user
    username: str = os.getenv("DB_USERNAME", "rsod_user")

    # 数据库密码，从环境变量 DB_PASSWORD 读取，默认为 rsod_password
    # 注意：生产环境应使用强密码并通过环境变量传入
    password: str = os.getenv("DB_PASSWORD", "rsod_password")

    # 数据库名称，从环境变量 DB_DATABASE 读取，默认为 rsod_platform
    database: str = os.getenv("DB_DATABASE", "rsod_platform")


# =============================================================================
# MinIO 对象存储配置类
# =============================================================================
class MinIOConfig(BaseModel):
    """
    MinIO 对象存储配置

    MinIO 是一个高性能的分布式对象存储系统，兼容 Amazon S3 API
    用于存储图片、视频、模型文件等非结构化数据

    配置项：
        host: MinIO 服务器地址，默认 localhost
        port: MinIO API 端口，默认 9000
        access_key: 访问密钥（相当于用户名），默认 admin
        secret_key: 秘密密钥（相当于密码），默认 minio_password
        secure: 是否使用 HTTPS 连接，默认 false（开发环境用 HTTP）
        original_bucket: 原始图片存储桶名称
        results_bucket: 检测结果图片存储桶名称
        models_bucket: AI 模型文件存储桶名称
    """

    # MinIO 服务器主机地址
    host: str = os.getenv("MINIO_HOST", "localhost")

    # MinIO API 端口（不是 Console 端口）
    port: int = int(os.getenv("MINIO_PORT", "9000"))

    # 访问密钥（Access Key），用于身份验证
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "admin")

    # 秘密密钥（Secret Key），用于身份验证
    # 注意：生产环境应使用强密码并通过环境变量传入
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio_password")

    # 是否使用安全连接（HTTPS）
    # 从环境变量读取并转换为布尔值
    # 支持的值：true, 1, yes（不区分大小写）
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")

    # 原始图片存储桶名称，用于保存上传的原始图片
    original_bucket: str = "rsod-original"

    # 检测结果图片存储桶名称，用于保存检测后的图片
    results_bucket: str = "rsod-results"

    # 模型文件存储桶名称，用于保存 AI 模型文件（设置为私有访问）
    models_bucket: str = "rsod-models"


# =============================================================================
# Redis 缓存配置类
# =============================================================================
class RedisConfig(BaseModel):
    """
    Redis 缓存配置

    Redis 是一个开源的内存数据结构存储系统，可用作数据库、缓存和消息队列
    用于缓存热点数据、会话管理、实时分析等场景

    配置项：
        host: Redis 服务器地址，默认 localhost
        port: Redis 服务端口，默认 6379
        password: Redis 访问密码，默认 redis_password
    """

    # Redis 服务器主机地址
    host: str = os.getenv("REDIS_HOST", "localhost")

    # Redis 服务端口
    port: int = int(os.getenv("REDIS_PORT", "6379"))

    # Redis 访问密码，用于身份验证
    # 注意：生产环境应使用强密码并通过环境变量传入
    password: str = os.getenv("REDIS_PASSWORD", "redis_password")


# =============================================================================
# 应用全局配置类
# =============================================================================
class Settings(BaseModel):
    """
    应用全局配置

    整合所有配置项，包括应用信息、CORS、YOLO 模型参数等

    配置项：
        app_name: 应用名称
        app_version: 应用版本号
        debug: 调试模式开关
        host: 服务监听地址
        port: 服务监听端口
        static_dir: 静态文件目录
        upload_dir: 上传文件存储目录
        result_dir: 检测结果文件目录
        database: 数据库配置（DatabaseConfig 实例）
        minio: MinIO 配置（MinIOConfig 实例）
        redis: Redis 配置（RedisConfig 实例）
        cors_origins: CORS 允许的来源列表
        yolo_model_path: YOLO 模型文件路径
        confidence_threshold: 目标检测置信度阈值
        iou_threshold: 非极大值抑制 IOU 阈值
    """

    # -------------------------------------------------------------------------
    # 应用基本信息
    # -------------------------------------------------------------------------

    # 应用名称，用于 API 文档标题
    app_name: str = os.getenv("APP_NAME", "RSOD Detection Platform")

    # 应用版本号
    app_version: str = os.getenv("APP_VERSION", "1.0.0")

    # 调试模式开关
    # True: 启用详细日志输出、服务重启自动加载代码变更
    # False: 生产模式，优化性能
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # 服务监听地址
    # 0.0.0.0: 监听所有网络接口（允许外部访问）
    # 127.0.0.1: 仅监听本地回环地址（仅本地访问）
    host: str = os.getenv("HOST", "0.0.0.0")

    # 服务监听端口
    port: int = int(os.getenv("PORT", "8000"))

    # -------------------------------------------------------------------------
    # 静态文件和目录配置
    # -------------------------------------------------------------------------

    # 静态文件目录，用于 serving 上传的图片等静态资源
    static_dir: str = "static"

    # 上传文件存储目录，保存用户上传的原始图片
    upload_dir: str = "static/uploads"

    # 检测结果文件目录，保存检测后的图片
    result_dir: str = "static/results"

    # -------------------------------------------------------------------------
    # 服务配置实例
    # -------------------------------------------------------------------------

    # 数据库配置实例
    database: DatabaseConfig = DatabaseConfig()

    # MinIO 对象存储配置实例
    minio: MinIOConfig = MinIOConfig()

    # Redis 缓存配置实例
    redis: RedisConfig = RedisConfig()

    # -------------------------------------------------------------------------
    # CORS 跨域配置
    # -------------------------------------------------------------------------

    # CORS（跨域资源共享）允许的来源列表
    # 多个来源用逗号分隔
    # 开发环境通常包括前端开发服务器地址
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # -------------------------------------------------------------------------
    # YOLO 目标检测模型配置
    # -------------------------------------------------------------------------

    # YOLO 模型文件路径，相对于项目根目录
    # 支持的模型：yolo11n.pt, yolo11s.pt, yolo11m.pt 等
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")

    # 目标检测置信度阈值
    # 只有检测框置信度 >= 此值的结果才会被保留
    # 范围：0.0 - 1.0，默认 0.5
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

    # 非极大值抑制（Non-Maximum Suppression）IOU 阈值
    # 用于去除重叠的检测框，只保留最优的检测结果
    # 范围：0.0 - 1.0，默认 0.45
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD", "0.45"))


# =============================================================================
# 全局配置实例
# =============================================================================
# 创建全局唯一的配置实例
# 在应用的任何地方都可以通过 import settings 访问配置
# 注意：应在应用启动时创建此实例，以确保所有配置正确加载
settings = Settings()
