# =============================================================================
# 检测 API 路由模块
# =============================================================================
# 功能说明：
#   - 定义检测相关的 API 接口
#   - 处理图片上传、检测请求、结果返回
#   - 提供历史记录和目标类别查询接口
#   - 检测结果持久化存储到 PostgreSQL 数据库
#
# API 接口列表：
#   POST /api/detection/single    - 单图检测
#   GET  /api/detection/history   - 获取检测历史记录（从数据库）
#   GET  /api/detection/{id}      - 获取单个检测记录
#   DELETE /api/detection/{id}    - 删除检测记录
#   GET  /api/detection/targets/list - 获取可检测目标列表
#
# 使用示例：
#   # 前端调用
#   const formData = new FormData();
#   formData.append('file', imageFile);
#   formData.append('model_name', 'rsod-yolo11n');
#   const response = await fetch('/api/detection/single', {
#       method: 'POST',
#       body: formData
#   });
# =============================================================================

# 导入 os 模块，用于文件路径操作
import os

# 导入 FastAPI 相关组件
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Response
from fastapi.responses import StreamingResponse

# 导入检测服务
from app.services.detection_service import detection_service

# 导入 MinIO 服务
from app.services.minio_service import minio_service

# 导入文件工具函数
from app.utils.file_utils import save_upload_file, ensure_directories, get_file_url

# 导入应用配置
from app.config import settings

# 导入数据模型
from app.models.schemas import (
    SingleDetectionResponse,   # 单图检测响应模型
    HistoryResponse,          # 历史记录响应模型
    TargetListResponse,       # 目标列表响应模型
    TargetItem,               # 目标项数据模型
    HistoryItem               # 历史记录项数据模型
)

# 导入数据库模型
from app.models.database import DetectionRecord

# 创建 API 路由实例
# prefix: 所有路由的前缀，如 /api/detection
# tags: 用于 OpenAPI 文档分组
router = APIRouter(prefix="/detection", tags=["detection"])

# 在模块加载时确保必要的目录存在
ensure_directories()


# =============================================================================
# 单图检测接口
# =============================================================================

@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),      # 上传的图片文件（必填）
    model_name: str = Form("rsod-yolo11n"), # 使用的模型名称（可选）
    user_id: str = Form(None)          # 用户 ID（可选）
):
    """
    单图目标检测接口

    功能：
    - 接收用户上传的图片
    - 保存图片到服务器
    - 调用检测服务进行目标检测
    - 保存检测记录到数据库
    - 返回检测结果

    参数：
        file: 上传的图片文件，支持 jpg、png 等格式
        model_name: 使用的模型名称（可选，默认 rsod-yolo11n）
        user_id: 用户 ID（可选）

    返回：
        SingleDetectionResponse: 包含检测结果的响应

    响应示例：
        {
            "success": true,
            "message": "检测成功",
            "data": {
                "detection_id": "uuid-string",
                "image_url": "http://localhost:8000/static/uploads/xxx.jpg",
                "result_image_url": "http://localhost:8000/static/results/xxx.jpg",
                "boxes": [...],
                "total_objects": 5,
                "detection_time": 0.523,
                "model_name": "rsod-yolo11n",
                "created_at": "2024-12-01T14:30:00"
            }
        }
    """
    try:
        # 确保临时上传目录存在
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # 保存上传的文件到服务器
        # save_upload_file 是异步函数，使用 await 调用
        filename = await save_upload_file(file, settings.upload_dir)

        # 构建图片的完整路径
        image_path = os.path.join(settings.upload_dir, filename)

        # 调用检测服务进行单图检测（支持用户 ID）
        result = detection_service.detect_single_image(image_path, user_id, model_name, minio_service)

        # 检测完成后，删除临时上传的文件（节省空间）
        try:
            os.remove(image_path)
        except:
            pass  # 删除失败不影响流程

        # 返回成功的响应
        return SingleDetectionResponse(
            success=True,                    # 请求成功
            message="检测成功",             # 提示信息
            data=result                      # 检测结果数据
        )

    except FileNotFoundError as e:
        # 模型文件未找到
        raise HTTPException(
            status_code=500,
            detail="模型文件未找到"
        )
    except Exception as e:
        # 如果检测过程中发生错误，抛出 500 错误
        raise HTTPException(
            status_code=500,                 # HTTP 状态码：服务器内部错误
            detail=f"检测失败: {str(e)}"    # 详细错误信息
        )


# =============================================================================
# 检测历史记录接口
# =============================================================================

@router.get("/history", response_model=HistoryResponse)
async def get_detection_history(
    page: int = 1,        # 页码（从 1 开始）
    page_size: int = 10,   # 每页记录数
    user_id: str = None    # 用户 ID（可选）
):
    """
    获取检测历史记录接口

    功能：
    - 从 PostgreSQL 数据库查询检测历史记录
    - 支持分页查询
    - 支持按用户 ID 筛选

    参数：
        page: 页码，默认 1
        page_size: 每页记录数，默认 10
        user_id: 用户 ID（可选）

    返回：
        HistoryResponse: 包含历史记录列表的响应

    响应示例：
        {
            "success": true,
            "message": "获取成功",
            "data": [
                {
                    "id": "uuid-string",
                    "image_url": "http://localhost:8000/static/uploads/xxx.jpg",
                    "result_image_url": "http://localhost:8000/static/results/xxx.jpg",
                    "total_objects": 3,
                    "created_at": "2024-12-01T14:30:00",
                    "model_name": "rsod-yolo11n"
                },
                ...
            ],
            "total": 15
        }
    """
    try:
        # 调用检测服务获取历史记录
        records = detection_service.get_detection_history(user_id=user_id, limit=page_size * page)

        # 计算分页
        start = (page - 1) * page_size
        end = start + page_size

        # 转换为 HistoryItem 列表
        history_items = []
        for record in records[start:end]:
            # 获取文件名（从 image_key 中提取）
            # 格式：uploads/xxx.jpg 或 results/xxx.jpg
            original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
            result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""
            
            # 构建 FastAPI 代理接口 URL
            # 格式：http://localhost:8000/api/detection/files/{bucket}/{filename}
            if original_filename:
                image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_filename}"
            else:
                image_url = ""
            
            if result_filename:
                result_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_filename}"
            else:
                result_url = ""

            history_items.append(HistoryItem(
                id=str(record.id),
                image_url=image_url,
                result_image_url=result_url,
                total_objects=record.total_objects or 0,
                created_at=record.created_at,
                model_name=record.model_name or "rsod-yolo11n",
                filename=original_filename or "detection.jpg",
                status=record.status or "completed",
                type=record.type or "single",
                time=record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "",
                count=1,
                detected_targets=[]  # 暂时留空
            ))

        # 返回历史记录响应
        return HistoryResponse(
            success=True,                          # 请求成功
            message="获取成功",                     # 提示信息
            data=history_items,                    # 当前页的数据
            total=len(records)                     # 总记录数
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="获取历史记录失败",
            detail=str(e)
        )


# =============================================================================
# 获取单个检测记录接口
# =============================================================================

@router.get("/{detection_id}", response_model=SingleDetectionResponse)
async def get_detection_by_id(
    detection_id: str = Path(..., description="检测记录 ID")
):
    """
    获取单个检测记录接口

    功能：
    - 根据检测 ID 从数据库查询详细检测记录

    参数：
        detection_id: 检测记录 ID

    返回：
        SingleDetectionResponse: 包含检测结果的响应
    """
    try:
        # 调用检测服务获取检测记录
        record = detection_service.get_detection_by_id(detection_id)

        if not record:
            raise HTTPException(
                status_code=404,
                message="检测记录不存在"
            )

        # 获取文件名
        original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
        result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""
        
        # 构建 FastAPI 代理接口 URL
        if original_filename:
            image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_filename}"
        else:
            image_url = ""
        
        if result_filename:
            result_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_filename}"
        else:
            result_url = ""

        # 构建响应数据
        from app.models.schemas import DetectionResult, DetectionBox

        # 查询检测结果详情
        boxes = []
        if hasattr(record, 'results') and record.results:
            for result in record.results:
                boxes.append(DetectionBox(
                    x1=result.x1,
                    y1=result.y1,
                    x2=result.x2,
                    y2=result.y2,
                    confidence=result.confidence,
                    class_id=result.class_id,
                    class_name=result.class_name,
                    chinese_name=result.chinese_name
                ))

        detection_result = DetectionResult(
            detection_id=str(record.id),
            image_url=image_url,
            result_image_url=result_url,
            boxes=boxes,
            total_objects=record.total_objects or 0,
            detection_time=record.detection_time or 0,
            model_name=record.model_name or "rsod-yolo11n",
            created_at=record.created_at
        )

        return SingleDetectionResponse(
            success=True,
            message="获取成功",
            data=detection_result
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="获取检测记录失败",
            detail=str(e)
        )


# =============================================================================
# 删除检测记录接口
# =============================================================================

@router.delete("/{detection_id}")
async def delete_detection(
    detection_id: str = Path(..., description="检测记录 ID")
):
    """
    删除检测记录接口

    功能：
    - 根据检测 ID 删除数据库中的检测记录及关联数据

    参数：
        detection_id: 检测记录 ID

    返回：
        dict: 删除结果
    """
    try:
        # 调用检测服务删除检测记录
        success = detection_service.delete_detection(detection_id)

        if not success:
            raise HTTPException(
                status_code=404,
                message="检测记录不存在"
            )

        return {
            "success": True,
            "message": "删除成功"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            message="删除检测记录失败",
            detail=str(e)
        )


# =============================================================================
# 目标类别列表接口
# =============================================================================

@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    """
    获取可检测目标类别列表接口

    功能：
    - 返回系统支持检测的所有目标类别
    - RSOD 数据集包含 4 种遥感目标

    返回：
        TargetListResponse: 包含目标类别列表的响应

    响应示例：
        {
            "success": true,
            "message": "获取成功",
            "data": [
                {
                    "id": 0,
                    "name": "aircraft",
                    "chinese_name": "飞机",
                    "description": "固定翼飞机、直升机等"
                },
                ...
            ]
        }
    """
    # 定义 RSOD 数据集支持检测的目标类别列表
    targets = [
        TargetItem(id=0, name="aircraft", chinese_name="飞机", description="固定翼飞机、直升机等"),
        TargetItem(id=1, name="oiltank", chinese_name="油罐", description="储油罐、化工罐等"),
        TargetItem(id=2, name="overpass", chinese_name="立交桥", description="各类立交桥"),
        TargetItem(id=3, name="playground", chinese_name="操场", description="运动场、操场等"),
    ]

    # 返回目标列表响应
    return TargetListResponse(
        success=True,              # 请求成功
        message="获取成功",         # 提示信息
        data=targets              # 目标类别列表
    )


# =============================================================================
# MinIO 文件代理接口
# =============================================================================

@router.get("/files/{bucket}/{filename}", response_class=Response)
def get_file(bucket: str, filename: str):
    """
    MinIO 文件代理接口

    功能：
    - 从 MinIO 获取文件并返回给前端
    - 解决前端无法直接访问 MinIO 的问题

    参数：
        bucket: MinIO Bucket 名称
        filename: 文件名

    返回：
        文件流
    """
    try:
        from app.services.minio_service import minio_service
        
        # 从 MinIO 获取文件
        response = minio_service.client.get_object(bucket, filename)
        
        # 确定内容类型
        content_type = "image/jpeg"
        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            content_type = "image/jpeg"
        
        # 读取所有数据
        data = response.read()
        
        # 关闭响应对象
        response.close()
        response.release_conn()
        
        # 返回文件流
        return Response(
            content=data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(data))
            }
        )
        
    except Exception as e:
        import traceback
        print(f"[文件代理错误] Bucket: {bucket}, Filename: {filename}")
        print(f"[文件代理错误] 异常类型: {type(e).__name__}")
        print(f"[文件代理错误] 异常信息: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=404,
            message="文件未找到",
            detail=f"{type(e).__name__}: {str(e)}"
        )
