# =============================================================================
# FastAPI 应用入口
# =============================================================================
# 功能：创建 FastAPI 应用，配置中间件，注册路由
# 依赖：fastapi, uvicorn
# =============================================================================

from fastapi import FastAPI                                      # FastAPI 框架
from fastapi.middleware.cors import CORSMiddleware              # CORS 中间件
from fastapi.staticfiles import StaticFiles                      # 静态文件服务
from app.config import settings                                  # 配置
from app.api.detection import router as detection_router         # 检测 API 路由
from app.api.model import router as model_router                 # 模型管理 API 路由
from app.utils.file_utils import ensure_directories              # 确保目录存在

# 启动时确保必要的目录存在（上传目录、结果目录等）
ensure_directories()

# =============================================================================
# 创建 FastAPI 应用实例
# =============================================================================
app = FastAPI(
    title=settings.app_name,                                    # API 文档标题
    version=settings.app_version,                                # API 版本
    description="遥感目标检测平台后端 API"                        # API 描述
)

# =============================================================================
# 配置 CORS 中间件
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,                        # 允许的跨域来源
    allow_credentials=True,                                     # 允许携带凭证
    allow_methods=["*"],                                        # 允许所有 HTTP 方法
    allow_headers=["*"],                                        # 允许所有请求头
)

# =============================================================================
# 挂载静态文件目录
# =============================================================================
# 访问 URL: http://host:port/static/文件名
# 实际路径: settings.static_dir/文件名
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# =============================================================================
# 注册 API 路由
# =============================================================================
# 所有检测相关的 API 都会以 /api/detection 为前缀
app.include_router(detection_router, prefix="/api")
# 所有模型管理相关的 API 都会以 /api/model 为前缀
app.include_router(model_router, prefix="/api")


# =============================================================================
# 根路径
# =============================================================================
@app.get("/")
async def root():
    """根路径返回应用信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


# =============================================================================
# 健康检查接口
# =============================================================================
@app.get("/health")
async def health_check():
    """
    健康检查接口

    功能：检查所有依赖服务的状态
    - PostgreSQL：数据库连接
    - MinIO：对象存储连接
    - Redis：缓存连接

    返回：
        dict: 包含各服务状态的字典
    """
    postgres_ok = False
    minio_ok = False
    redis_ok = False

    # 检查 PostgreSQL
    try:
        from app.models.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass

    # 检查 Redis
    try:
        from app.services.redis_service import redis_service
        redis_ok = redis_service.ping()
    except Exception:
        pass

    # 检查 MinIO
    try:
        from app.services.minio_service import minio_service
        minio_service.client.list_buckets()
        minio_ok = True
    except Exception:
        pass

    # 计算整体状态
    all_ok = all([postgres_ok, minio_ok, redis_ok])
    status = "healthy" if all_ok else "degraded"

    return {
        "status": status,
        "services": {
            "postgres": "up" if postgres_ok else "down",
            "minio": "up" if minio_ok else "down",
            "redis": "up" if redis_ok else "down"
        }
    }


# =============================================================================
# 应用启动入口
# =============================================================================
if __name__ == "__main__":
    import uvicorn                                               # ASGI 服务器

    uvicorn.run(
        "main:app",                                             # 应用模块路径
        host=settings.host,                                      # 监听地址
        port=settings.port,                                      # 监听端口
        reload=settings.debug,                                   # 开发模式启用热重载
        log_level="debug" if settings.debug else "info",         # 日志级别
        access_log=True                                          # 启用访问日志
    )