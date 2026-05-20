# =============================================================================
# 目标检测服务模块
# =============================================================================
# 功能说明：
#   - 封装 YOLO 目标检测模型的所有操作
#   - 提供单图检测、批量检测等接口
#   - 支持绘制检测框并保存结果图片
#   - 检测结果持久化存储到数据库
#
# YOLO 模型说明：
#   YOLO（You Only Look Once）是一种实时目标检测算法
#   本模块使用 Ultralytics 提供的 YOLO11 实现
#
# 检测流程：
#   1. 加载图片
#   2. 调用 YOLO 模型进行预测
#   3. 解析检测结果（框坐标、置信度、类别）
#   4. 绘制检测框到图片
#   5. 保存结果到数据库
#   6. 返回检测结果
#
# 使用示例：
#   from app.services.detection_service import detection_service
#
#   # 单图检测
#   result = detection_service.detect_single_image("/path/to/image.jpg", user_id="xxx")
#   print(f"检测到 {result.total_objects} 个目标")
# =============================================================================

# 导入 os 模块，用于文件路径操作
import os

# 导入 time 模块，用于计时
import time

# 导入 uuid 模块，用于生成唯一 ID
import uuid

# 导入 datetime 模块，用于时间戳
from datetime import datetime

# 导入 Path 模块，用于路径操作
from pathlib import Path

# 导入类型提示
from typing import List, Dict, Any, Optional

# 导入 Ultralytics YOLO 模型
from ultralytics import YOLO

# 导入 PIL 用于图片处理
from PIL import Image

# 导入 OpenCV 用于图片处理和绘制
import cv2

# 导入应用配置
from app.config import settings

# 导入数据模型
from app.models.schemas import DetectionBox, DetectionResult
from app.models.database import DetectionRecord, DetectionResult as DBDetectionResult

# 导入数据库会话
try:
    from app.database import get_db
except ImportError:
    from app.models.database import get_db

# 导入文件工具函数
from app.utils.file_utils import get_file_url

# 导入 MinIO 服务
from app.services.minio_service import minio_service

# 导入日志模块
import logging

# 配置日志
logger = logging.getLogger(__name__)


class DetectionService:
    """
    目标检测服务类

    该类封装了 YOLO 目标检测的所有操作，包括：
    - 模型加载和初始化（智能版本管理）
    - 单图检测
    - 批量检测（预留）
    - 检测结果处理和可视化
    - 检测结果持久化存储
    """

    def __init__(self):
        """
        初始化检测服务

        功能：
        - 初始化模型实例
        - 检查本地模型版本，智能加载最新版本
        - 初始化类别名称映射
        """
        # 模型实例初始化为 None
        self.model = None

        # 当前加载的模型信息
        self.current_model_info = {
            "version": None,
            "object_name": None,
            "loaded_at": None,
            "metadata": None
        }

        # 本地模型信息存储路径
        self.local_model_info_path = Path(settings.yolo_model_path).parent / "model_info.json"

        # 类别名称映射字典（RSOD 数据集 4 类）
        self.class_names = {}

        # 加载 YOLO 模型（智能版本检查）
        self._load_model_smart()

        # 初始化类别名称映射
        self._init_class_names()

    def _save_local_model_info(self, model_info: dict):
        """
        保存本地模型信息到文件
        
        参数：
            model_info: 模型信息字典
        """
        try:
            info_path = Path(self.local_model_info_path)
            info_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(info_path, "w", encoding="utf-8") as f:
                import json
                json.dump(model_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"保存本地模型信息失败: {str(e)}")

    def _load_local_model_info(self) -> Optional[dict]:
        """
        从文件加载本地模型信息
        
        返回：
            Optional[dict]: 模型信息字典
        """
        try:
            info_path = Path(self.local_model_info_path)
            if not info_path.exists():
                return None
                
            with open(info_path, "r", encoding="utf-8") as f:
                import json
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"加载本地模型信息失败: {str(e)}")
            return None

    def _load_model_smart(self):
        """
        智能加载模型（版本检查与自动更新）
        
        功能：
        1. 检查本地模型是否存在
        2. 查询 MinIO 中的最新模型版本
        3. 如果本地没有或版本过旧，下载最新模型
        4. 加载模型并保存版本信息
        """
        # 检查是否有本地模型信息
        local_info = self._load_local_model_info()
        
        # 获取 MinIO 中的最新模型
        latest_model = minio_service.get_latest_model()
        
        need_download = False
        model_object_name = None
        
        # 情况 1：本地模型不存在
        if not os.path.exists(settings.yolo_model_path):
            logger.info("本地模型不存在，需要从 MinIO 下载")
            need_download = True
            
        # 情况 2：本地模型存在但没有信息
        elif not local_info:
            logger.info("本地模型存在但没有版本信息，检查 MinIO 最新版本")
            need_download = True
            
        # 情况 3：有本地信息，对比版本
        else:
            if latest_model:
                # 检查是否是同一个模型版本
                if local_info.get("object_name") != latest_model:
                    logger.info(f"发现新版本模型: {latest_model} (当前: {local_info.get('object_name', 'unknown')})")
                    need_download = True
                else:
                    logger.info(f"本地模型已是最新版本: {latest_model}")
        
        # 如果需要下载，从 MinIO 获取最新模型
        if need_download and latest_model:
            logger.info(f"从 MinIO 下载最新模型: {latest_model}")
            success = minio_service.download_model_file(latest_model, settings.yolo_model_path)
            if not success:
                # 如果下载失败但本地已有模型，继续使用本地模型
                if os.path.exists(settings.yolo_model_path):
                    logger.warning(f"模型下载失败，使用本地已有模型: {settings.yolo_model_path}")
                    model_object_name = local_info.get("object_name") if local_info else None
                else:
                    raise FileNotFoundError(f"模型下载失败且本地不存在: {latest_model}")
            else:
                model_object_name = latest_model
                logger.info(f"模型下载成功: {settings.yolo_model_path}")
        
        elif not latest_model:
            # 没有 MinIO 模型，检查本地是否存在
            if not os.path.exists(settings.yolo_model_path):
                raise FileNotFoundError(f"模型文件未找到: {settings.yolo_model_path}")
            model_object_name = local_info.get("object_name") if local_info else None
        
        else:
            # 本地已是最新
            model_object_name = local_info.get("object_name") if local_info else None
        
        # 加载 YOLO 模型
        self.model = YOLO(settings.yolo_model_path)
        
        # 获取并保存模型信息
        model_metadata = None
        if model_object_name:
            model_metadata = minio_service.get_model_metadata(model_object_name)
        
        # 更新当前模型信息
        self.current_model_info = {
            "version": model_metadata.get("version", "unknown") if model_metadata else "unknown",
            "object_name": model_object_name,
            "loaded_at": datetime.now().isoformat(),
            "metadata": model_metadata
        }
        
        # 保存到本地
        self._save_local_model_info(self.current_model_info)
        
        logger.info(f"模型加载成功: {settings.yolo_model_path} (版本: {self.current_model_info['version']})")
    
    def reload_model(self, model_object_name: Optional[str] = None) -> bool:
        """
        重新加载模型（可指定特定版本）
        
        参数：
            model_object_name: 可选的模型对象名称（MinIO 中的名称）
            
        返回：
            bool: 是否成功
        """
        try:
            if model_object_name:
                logger.info(f"加载指定模型: {model_object_name}")
                success = minio_service.download_model_file(model_object_name, settings.yolo_model_path)
                if not success:
                    logger.error(f"模型下载失败: {model_object_name}")
                    return False
            else:
                logger.info("重新加载最新模型")
            
            # 重新初始化
            self.model = None
            self._load_model_smart()
            return True
            
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            return False

    def _init_class_names(self):
        """
        初始化类别名称映射

        功能：
        - 定义 RSOD 数据集的 4 类目标名称
        - 类别 ID 从 0 开始

        说明：
        - RSOD 数据集包含 4 种遥感目标
        - 支持飞机、油罐、立交桥、操场的检测
        """
        # RSOD 数据集 4 类目标名称映射
        # 类别 ID：目标名称
        self.class_names = {
            0: "aircraft",    # 飞机
            1: "oiltank",     # 油罐
            2: "overpass",    # 立交桥
            3: "playground",  # 操场
        }

    def get_class_chinese_name(self, class_name: str) -> str:
        """
        获取类别的中文名称

        参数：
            class_name: 类别英文名称

        返回：
            str: 类别中文名称
        """
        chinese_names = {
            "aircraft": "飞机",
            "oiltank": "油罐",
            "overpass": "立交桥",
            "playground": "操场"
        }
        return chinese_names.get(class_name, class_name)

    def detect_single_image(self, 
                           image_path: str, 
                           user_id: Optional[str] = None,
                           model_name: str = "rsod-yolo11n",
                           minio_svc = None) -> DetectionResult:
        """
        单图目标检测

        参数：
            image_path: 图片文件路径
            user_id: 用户 ID（可选）
            model_name: 模型名称（可选）

        返回：
            DetectionResult: 检测结果对象

        检测流程：
            1. 记录开始时间
            2. 生成唯一检测 ID
            3. 调用 YOLO 模型进行预测
            4. 解析检测框信息
            5. 在图片上绘制检测框
            6. 上传结果图片到 MinIO
            7. 计算检测耗时
            8. 保存检测记录到数据库
            9. 返回检测结果

        说明：
            - 使用配置文件中的置信度和 IOU 阈值
            - 检测结果包含所有检测到的目标
            - 结果图片上传到 MinIO 对象存储
            - 检测记录持久化存储到 PostgreSQL 数据库
        """
        # 记录检测开始时间
        start_time = time.time()

        # 生成唯一的检测 ID
        detection_id = str(uuid.uuid4())

        # 调用 YOLO 模型进行预测
        results = self.model.predict(
            source=image_path,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            save=False
        )

        # 解析检测结果
        boxes = []  # 检测框列表
        db_results = []  # 数据库结果列表

        # 遍历所有检测结果
        for result in results:
            # 遍历所有检测到的目标框
            for box in result.boxes:
                # 提取检测框坐标（xyxy 格式：左上角、右下角）
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # 提取置信度
                confidence = float(box.conf[0])

                # 提取类别 ID
                class_id = int(box.cls[0])

                # 获取类别名称
                class_name = self.class_names.get(class_id, f"class_{class_id}")

                # 获取中文名称
                chinese_name = self.get_class_chinese_name(class_name)

                # 创建检测框对象（用于返回）
                boxes.append(DetectionBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

                # 创建数据库结果对象（用于持久化）
                db_results.append(DBDetectionResult(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

        # 生成结果文件名
        result_filename = f"result_{uuid.uuid4().hex}.jpg"

        # 绘制检测框到图片
        # results[0].plot() 返回带检测框的图片（NumPy 数组）
        annotated_image = results[0].plot()

        # 将图片从 RGB 格式转换为 BGR 格式（OpenCV 需要）
        annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

        # 将图片编码为 JPEG 格式，获取字节数据
        _, image_bytes = cv2.imencode('.jpg', annotated_image_bgr)
        image_bytes = image_bytes.tobytes()

        # 使用传入的 minio_svc 或全局的 minio_service
        minio = minio_svc if minio_svc is not None else minio_service

        # 上传结果图片到 MinIO
        result_object_name = minio.upload_result_image(image_bytes, "jpg")

        # 计算检测耗时
        detection_time = time.time() - start_time

        # 获取原始图片文件名
        image_filename = os.path.basename(image_path)

        # 将原始图片上传到 MinIO
        with open(image_path, 'rb') as f:
            original_image_bytes = f.read()
        original_object_name = minio.upload_image_bytes(original_image_bytes, image_filename)

        # 构建 MinIO 对象 key
        original_image_key = f"uploads/{original_object_name}"
        result_image_key = f"results/{result_object_name}"

        # 保存检测记录到数据库
        db_record = self._save_to_database(
            user_id=user_id,
            detection_id=detection_id,
            model_name=model_name,
            total_objects=len(boxes),
            detection_time=detection_time,
            original_image_key=original_image_key,
            result_image_key=result_image_key,
            results=db_results
        )

        # 构建 FastAPI 代理接口 URL
        # 格式：http://localhost:8000/api/detection/files/{bucket}/{filename}
        original_image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_object_name}"
        result_image_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_object_name}"

        # 构建检测结果对象
        return DetectionResult(
            detection_id=detection_id,                    # 唯一检测 ID
            image_url=original_image_url,                 # 原始图片 URL（FastAPI代理）
            result_image_url=result_image_url,            # 结果图片 URL（FastAPI代理）
            boxes=boxes,                                 # 检测框列表
            total_objects=len(boxes),                    # 检测到的目标数量
            detection_time=round(detection_time, 3),     # 检测耗时（秒）
            model_name=model_name,                       # 使用的模型名称
            created_at=datetime.now()                   # 创建时间
        )

    def _save_to_database(self,
                         user_id: Optional[str],
                         detection_id: str,
                         model_name: str,
                         total_objects: int,
                         detection_time: float,
                         original_image_key: str,
                         result_image_key: str,
                         results: List[DBDetectionResult]) -> DetectionRecord:
        """
        将检测记录保存到数据库

        参数：
            user_id: 用户 ID
            detection_id: 检测 ID
            model_name: 模型名称
            total_objects: 检测到的目标数量
            detection_time: 检测耗时
            original_image_key: 原始图片 key
            result_image_key: 结果图片 key
            results: 检测结果列表

        返回：
            DetectionRecord: 数据库记录对象
        """
        try:
            # 获取数据库会话
            db = next(get_db())

            # 创建检测记录
            record = DetectionRecord(
                id=detection_id,
                user_id=user_id,
                type="single",
                status="completed",
                model_name=model_name,
                model_version="1.0.0",
                total_objects=total_objects,
                detection_time=detection_time,
                original_image_key=original_image_key,
                result_image_key=result_image_key
            )

            # 添加到会话
            db.add(record)

            # 添加检测结果
            for result in results:
                result.record_id = detection_id
                db.add(result)

            # 提交事务
            db.commit()

            # 刷新记录
            db.refresh(record)

            logger.info(f"检测记录已保存到数据库: {detection_id}")

            return record

        except Exception as e:
            logger.error(f"保存检测记录到数据库失败: {str(e)}")
            # 回滚事务
            try:
                db.rollback()
            except:
                pass
            return None

    def get_detection_history(self, user_id: str = None, limit: int = 10) -> List[DetectionRecord]:
        """
        获取检测历史记录

        参数：
            user_id: 用户 ID（可选）
            limit: 返回数量限制（默认 10）

        返回：
            List[DetectionRecord]: 检测记录列表
        """
        try:
            db = next(get_db())

            query = db.query(DetectionRecord).order_by(DetectionRecord.created_at.desc())

            if user_id:
                query = query.filter(DetectionRecord.user_id == user_id)

            records = query.limit(limit).all()

            logger.info(f"获取检测历史记录: {len(records)} 条")

            return records

        except Exception as e:
            logger.error(f"获取检测历史记录失败: {str(e)}")
            return []

    def get_detection_by_id(self, detection_id: str) -> Optional[DetectionRecord]:
        """
        根据检测 ID 获取检测记录

        参数：
            detection_id: 检测 ID

        返回：
            Optional[DetectionRecord]: 检测记录对象
        """
        try:
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()

            if record:
                logger.info(f"获取检测记录成功: {detection_id}")
            else:
                logger.warning(f"检测记录不存在: {detection_id}")

            return record

        except Exception as e:
            logger.error(f"获取检测记录失败: {str(e)}")
            return None

    def delete_detection(self, detection_id: str) -> bool:
        """
        删除检测记录

        参数：
            detection_id: 检测 ID

        返回：
            bool: 删除是否成功
        """
        try:
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()

            if record:
                # 删除关联的检测结果
                db.query(DBDetectionResult).filter(DBDetectionResult.record_id == detection_id).delete()

                # 删除检测记录
                db.delete(record)

                # 提交事务
                db.commit()

                logger.info(f"检测记录已删除: {detection_id}")
                return True

            logger.warning(f"检测记录不存在: {detection_id}")
            return False

        except Exception as e:
            logger.error(f"删除检测记录失败: {str(e)}")
            try:
                db.rollback()
            except:
                pass
            return False


# =============================================================================
# 全局检测服务实例
# =============================================================================
# 创建全局唯一的检测服务实例（单例模式）
# 在应用的任何地方都可以通过 import detection_service 访问
detection_service = DetectionService()
