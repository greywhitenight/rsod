# =============================================================================
# 数据模型/Schema 模块
# =============================================================================
# 功能说明：
#   - 定义 API 请求和响应的数据结构
#   - 使用 Pydantic 进行数据验证
#   - 提供清晰的 API 接口定义
#
# Pydantic 简介：
#   Pydantic 是一个数据验证库，使用 Python 类型注解进行数据验证
#   主要特点：
#   - 自动数据验证
#   - 类型转换
#   - JSON Schema 生成
#   - IDE 自动补全支持
#
# 使用示例：
#   from app.models.schemas import DetectionResult, SingleDetectionResponse
#
#   # 定义响应
#   response = SingleDetectionResponse(
#       success=True,
#       message="检测成功",
#       data=detection_result
#   )
# =============================================================================

# 导入 Pydantic 的 BaseModel 基类
from pydantic import BaseModel

# 导入类型提示
from typing import List, Optional

# 导入 datetime 模块
from datetime import datetime


# =============================================================================
# 检测相关的数据模型
# =============================================================================

class DetectionBox(BaseModel):
    """
    检测框数据模型

    表示一个目标检测框的信息，包括位置、置信度和类别

    属性：
        x1: 检测框左上角 X 坐标
        y1: 检测框左上角 Y 坐标
        x2: 检测框右下角 X 坐标
        y2: 检测框右下角 Y 坐标
        confidence: 置信度（0-1 之间）
        class_id: 目标类别 ID
        class_name: 目标类别名称（英文）
        chinese_name: 目标类别名称（中文）
    """
    # 检测框左上角 X 坐标
    x1: float

    # 检测框左上角 Y 坐标
    y1: float

    # 检测框右下角 X 坐标
    x2: float

    # 检测框右下角 Y 坐标
    y2: float

    # 置信度，表示检测框包含目标的置信程度（0.0 - 1.0）
    confidence: float

    # 目标类别 ID（RSOD 数据集 0-3）
    class_id: int

    # 目标类别名称（英文，如 "aircraft", "oiltank", "overpass", "playground"）
    class_name: str

    # 目标类别名称（中文）
    chinese_name: Optional[str] = None


class DetectionResult(BaseModel):
    """
    检测结果数据模型

    表示一次完整的检测任务的结果

    属性：
        detection_id: 唯一检测 ID（UUID）
        image_url: 原始图片的访问 URL
        result_image_url: 检测结果图片的访问 URL（带检测框）
        boxes: 检测到的目标框列表
        total_objects: 检测到的目标总数
        detection_time: 检测耗时（秒）
        model_name: 使用的模型名称
        created_at: 检测时间
    """
    # 唯一检测 ID，用于追踪和查询
    detection_id: str

    # 原始图片的访问 URL
    image_url: str

    # 检测结果图片的访问 URL（带检测框标记）
    result_image_url: str

    # 检测到的所有目标框列表
    boxes: List[DetectionBox]

    # 检测到的目标总数
    total_objects: int

    # 检测耗时（秒）
    detection_time: float

    # 使用的检测模型名称
    model_name: str

    # 检测完成时间
    created_at: datetime


class SingleDetectionResponse(BaseModel):
    """
    单图检测 API 响应模型

    用于统一单图检测接口的响应格式

    属性：
        success: 请求是否成功
        message: 提示信息
        data: 检测结果数据（成功时有值）
    """
    # 请求是否成功
    success: bool

    # 提示信息或错误描述
    message: str

    # 检测结果数据（可选，失败时为 None）
    data: Optional[DetectionResult] = None


# =============================================================================
# 历史记录相关的数据模型
# =============================================================================

class HistoryItem(BaseModel):
    """
    历史记录项数据模型

    表示一条检测历史记录

    属性：
        id: 历史记录 ID
        image_url: 图片 URL
        result_image_url: 结果图片 URL
        total_objects: 检测到的目标数量
        created_at: 检测时间
        model_name: 使用的模型名称
        filename: 文件名
        status: 状态
        type: 类型
        time: 时间字符串
        count: 数量
        detected_targets: 检测到的目标列表
    """
    # 历史记录 ID
    id: str

    # 图片 URL
    image_url: str

    # 结果图片 URL
    result_image_url: str

    # 检测到的目标数量
    total_objects: int

    # 检测时间
    created_at: datetime

    # 使用的模型名称
    model_name: str
    
    # 文件名
    filename: str = ""
    
    # 状态
    status: str = "completed"
    
    # 类型
    type: str = "single"
    
    # 时间字符串
    time: str = ""
    
    # 数量
    count: int = 1
    
    # 检测到的目标列表
    detected_targets: list = []


class HistoryResponse(BaseModel):
    """
    历史记录列表 API 响应模型

    用于返回检测历史记录列表

    属性：
        success: 请求是否成功
        message: 提示信息
        data: 历史记录列表
        total: 总记录数
    """
    # 请求是否成功
    success: bool

    # 提示信息
    message: str

    # 历史记录列表
    data: List[HistoryItem]

    # 总记录数（用于分页）
    total: int


# =============================================================================
# 目标类别相关的数据模型
# =============================================================================

class TargetItem(BaseModel):
    """
    目标类别项数据模型

    表示一个可检测的目标类别

    属性：
        id: 类别 ID
        name: 类别名称（英文）
        chinese_name: 类别名称（中文）
        description: 类别描述（可选）
    """
    # 类别 ID
    id: int

    # 类别名称（英文）
    name: str

    # 类别名称（中文）
    chinese_name: str

    # 类别描述（可选）
    description: Optional[str] = None


class TargetListResponse(BaseModel):
    """
    目标类别列表 API 响应模型

    用于返回所有可检测的目标类别

    属性：
        success: 请求是否成功
        message: 提示信息
        data: 目标类别列表
    """
    # 请求是否成功
    success: bool

    # 提示信息
    message: str

    # 目标类别列表
    data: List[TargetItem]


# =============================================================================
# 模型管理相关的数据模型
# =============================================================================

class ModelMetadata(BaseModel):
    """
    模型元数据模型
    
    表示模型的元数据信息，包括版本、指标、配置等
    
    属性：
        name: 模型名称
        version: 模型版本（语义化版本，如 "1.0.0"）
        created_at: 创建时间
        description: 模型描述
        metrics: 模型指标（字典，包含 mAP50, mAP50_95, precision, recall 等）
        config: 训练配置（字典）
    """
    name: str
    version: str
    created_at: datetime
    description: Optional[str] = None
    metrics: Optional[dict] = None
    config: Optional[dict] = None


class ModelItem(BaseModel):
    """
    模型项数据模型
    
    表示一个可用的模型版本的信息
    
    属性：
        object_name: MinIO 中的对象名称
        metadata: 模型元数据
        public_url: 模型公开访问 URL
    """
    object_name: str
    metadata: Optional[ModelMetadata] = None
    public_url: str


class ModelListResponse(BaseModel):
    """
    模型列表 API 响应模型
    
    用于返回所有可用的模型版本列表
    
    属性：
        success: 请求是否成功
        message: 提示信息
        data: 模型列表
        latest: 最新模型信息（可选）
    """
    success: bool
    message: str
    data: List[ModelItem]
    latest: Optional[ModelItem] = None


class CurrentModelResponse(BaseModel):
    """
    当前加载模型信息 API 响应模型
    
    用于返回当前加载的模型的详细信息
    
    属性：
        success: 请求是否成功
        message: 提示信息
        data: 当前模型信息
    """
    success: bool
    message: str
    data: ModelItem


class ReloadModelRequest(BaseModel):
    """
    重新加载模型请求模型
    
    参数：
        object_name: 可选的模型对象名称（MinIO 中的名称）
    """
    object_name: Optional[str] = None


class ReloadModelResponse(BaseModel):
    """
    重新加载模型响应模型
    
    属性：
        success: 是否成功
        message: 提示信息
        data: 重新加载后的模型信息
    """
    success: bool
    message: str
    data: Optional[ModelItem] = None
