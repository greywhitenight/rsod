# =============================================================================
# 模型管理 API 路由模块
# =============================================================================
# 功能说明：
#   - 提供模型版本管理的 API 接口
#   - 查询可用模型列表、当前加载模型
#   - 支持重新加载最新模型或指定版本
#   - 管理 MinIO 中的模型文件
#
# API 接口列表：
#   GET    /api/model/list       - 获取所有可用模型列表
#   GET    /api/model/current    - 获取当前加载的模型信息
#   POST   /api/model/reload     - 重新加载模型（可选指定版本）
#
# 使用示例：
#   # 前端调用：获取当前模型信息
#   const response = await fetch('/api/model/current');
#   const data = await response.json();
# =============================================================================

# 导入 FastAPI 相关组件
from fastapi import APIRouter, HTTPException, Depends

# 导入模型管理服务
from app.services.detection_service import detection_service
from app.services.minio_service import minio_service

# 导入数据模型
from app.models.schemas import (
    ModelListResponse,
    ModelItem,
    CurrentModelResponse,
    ReloadModelRequest,
    ReloadModelResponse,
    ModelMetadata
)

# 导入应用配置
from app.config import settings

# 创建 API 路由实例
router = APIRouter(prefix="/model", tags=["model"])


# =============================================================================
# 获取可用模型列表接口
# =============================================================================

@router.get("/list", response_model=ModelListResponse)
async def get_model_list():
    """
    获取所有可用模型列表接口
    
    功能：
    - 查询 MinIO 中的所有模型文件
    - 解析每个模型的元数据
    - 找出并标记最新版本模型
    
    返回：
        ModelListResponse: 包含模型列表和最新模型信息的响应
    
    响应示例：
        {
            "success": true,
            "message": "获取成功",
            "data": [
                {
                    "object_name": "rsod-yolo11n-best_v1.0.0_20240101090000.pt",
                    "metadata": {...},
                    "public_url": "http://localhost:9000/rsod-models/..."
                }
            ],
            "latest": {...}
        }
    """
    try:
        # 获取所有模型并附带元数据
        models_with_meta = minio_service.list_models_with_metadata()
        
        # 转换为 ModelItem 列表
        model_items = []
        for model in models_with_meta:
            # 构建 ModelMetadata
            metadata = None
            if model.get("metadata"):
                meta_data = model["metadata"]
                metadata = ModelMetadata(
                    name=meta_data.get("name", "unknown"),
                    version=meta_data.get("version", "unknown"),
                    created_at=meta_data.get("created_at"),
                    description=meta_data.get("description"),
                    metrics=meta_data.get("metrics"),
                    config=meta_data.get("config")
                )
            
            model_items.append(ModelItem(
                object_name=model["object_name"],
                metadata=metadata,
                public_url=model["public_url"]
            ))
        
        # 获取最新模型
        latest_model = None
        if model_items:
            # 查找最新版本（使用 list_models_with_metadata 已经是最新优先吗？）
            # 我们再调用一次 get_latest_model 确保准确
            latest_object_name = minio_service.get_latest_model()
            if latest_object_name:
                for item in model_items:
                    if item.object_name == latest_object_name:
                        latest_model = item
                        break
        
        # 返回模型列表响应
        return ModelListResponse(
            success=True,
            message="获取成功",
            data=model_items,
            latest=latest_model
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="获取模型列表失败",
            detail=str(e)
        )


# =============================================================================
# 获取当前加载模型接口
# =============================================================================

@router.get("/current", response_model=CurrentModelResponse)
async def get_current_model():
    """
    获取当前加载的模型信息接口
    
    功能：
    - 返回当前应用正在使用的模型的详细信息
    - 包括版本、加载时间、元数据等
    
    返回：
        CurrentModelResponse: 包含当前模型信息的响应
    """
    try:
        # 获取当前模型信息
        current_info = detection_service.current_model_info
        
        # 构建 ModelMetadata
        metadata = None
        if current_info.get("metadata"):
            meta_data = current_info["metadata"]
            metadata = ModelMetadata(
                name=meta_data.get("name", "unknown"),
                version=meta_data.get("version", "unknown"),
                created_at=meta_data.get("created_at"),
                description=meta_data.get("description"),
                metrics=meta_data.get("metrics"),
                config=meta_data.get("config")
            )
        
        # 构建 ModelItem
        object_name = current_info.get("object_name", "unknown")
        public_url = ""
        if object_name and object_name != "unknown":
            public_url = minio_service.get_public_url(settings.minio.models_bucket, object_name)
        
        model_item = ModelItem(
            object_name=object_name,
            metadata=metadata,
            public_url=public_url
        )
        
        return CurrentModelResponse(
            success=True,
            message="获取成功",
            data=model_item
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="获取当前模型信息失败",
            detail=str(e)
        )


# =============================================================================
# 重新加载模型接口
# =============================================================================

@router.post("/reload", response_model=ReloadModelResponse)
async def reload_model(request: ReloadModelRequest = None):
    """
    重新加载模型接口
    
    功能：
    - 重新加载模型（默认加载最新版本）
    - 支持指定加载特定版本的模型
    
    参数：
        request: 请求对象，可选包含 object_name 字段
    
    返回：
        ReloadModelResponse: 包含重新加载后的模型信息
    """
    try:
        # 调用检测服务重新加载模型
        success = detection_service.reload_model(
            model_object_name=request.object_name if request else None
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                message="模型重新加载失败"
            )
        
        # 获取重新加载后的模型信息
        current_info = detection_service.current_model_info
        
        # 构建 ModelMetadata
        metadata = None
        if current_info.get("metadata"):
            meta_data = current_info["metadata"]
            metadata = ModelMetadata(
                name=meta_data.get("name", "unknown"),
                version=meta_data.get("version", "unknown"),
                created_at=meta_data.get("created_at"),
                description=meta_data.get("description"),
                metrics=meta_data.get("metrics"),
                config=meta_data.get("config")
            )
        
        # 构建 ModelItem
        object_name = current_info.get("object_name", "unknown")
        public_url = ""
        if object_name and object_name != "unknown":
            public_url = minio_service.get_public_url(settings.minio.models_bucket, object_name)
        
        model_item = ModelItem(
            object_name=object_name,
            metadata=metadata,
            public_url=public_url
        )
        
        return ReloadModelResponse(
            success=True,
            message="模型重新加载成功",
            data=model_item
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="模型重新加载失败",
            detail=str(e)
        )
