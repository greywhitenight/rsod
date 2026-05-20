# =============================================================================
# MinIO 对象存储服务模块
# =============================================================================
# 功能说明：
#   - 封装 MinIO 对象存储的所有操作
#   - 提供图片上传、下载、删除等接口
#   - 支持公开和私有 Bucket 的访问控制
#
# MinIO 简介：
#   MinIO 是一个高性能的分布式对象存储系统，兼容 Amazon S3 API
#   适合存储图片、视频、文档、模型文件等非结构化数据
#
# Bucket 说明：
#   - rsod-original: 存储用户上传的原始图片
#   - rsod-results: 存储检测后的结果图片
#   - rsod-models: 存储 AI 模型文件（私有）
#
# 使用示例：
#   from app.services.minio_service import minio_service
#
#   # 上传图片
#   object_name = minio_service.upload_image(file, "rsod-original")
#
#   # 获取访问 URL
#   url = minio_service.get_public_url("rsod-original", object_name)
# =============================================================================

# 导入 MinIO Python SDK 的 Minio 客户端类
from minio import Minio

# 导入 MinIO 错误异常类，用于处理 MinIO 操作中的错误
from minio.error import S3Error

# 导入 FastAPI 的 UploadFile 类型，用于处理文件上传
from fastapi import UploadFile

# 导入 io 模块，用于处理字节流（BytesIO）
import io

# 导入 uuid 模块，用于生成唯一的对象名称
import uuid

# 导入 os 模块，用于文件路径操作
import os

# 导入类型提示 Optional，表示可选类型
from typing import Optional

# 导入应用配置
from app.config import settings


class MinIOService:
    """
    MinIO 对象存储服务类

    该类封装了所有 MinIO 对象存储的操作，包括：
    - Bucket 管理（创建、检查存在性）
    - 对象上传（图片、文件）
    - 对象访问（公开 URL、私有 URL）
    - 对象删除和列表
    """

    def __init__(self):
        """
        初始化 MinIO 客户端

        功能：
        - 创建 MinIO 客户端连接
        - 自动创建配置的 Bucket（如果不存在）
        """
        # 构建 MinIO 服务器地址，格式：主机:端口
        endpoint = f"{settings.minio.host}:{settings.minio.port}"

        # 创建 MinIO 客户端实例
        self.client = Minio(
            endpoint=endpoint,                              # MinIO 服务器地址
            access_key=settings.minio.access_key,         # 访问密钥
            secret_key=settings.minio.secret_key,         # 秘密密钥
            secure=settings.minio.secure                   # 是否使用 HTTPS
        )

        # 启动时确保所有需要的 Bucket 存在
        self._ensure_buckets()

    def _ensure_buckets(self):
        """
        确保所有配置的 Bucket 存在

        功能：
        - 检查 Bucket 是否存在
        - 如果不存在，自动创建
        - 用于服务启动时的初始化
        """
        # 定义需要创建的 Bucket 列表
        buckets = [
            settings.minio.original_bucket,          # 原始图片存储桶
            settings.minio.results_bucket,            # 结果图片存储桶
            settings.minio.models_bucket              # 模型文件存储桶
        ]

        # 遍历每个 Bucket，检查并创建
        for bucket in buckets:
            # 检查 Bucket 是否已存在
            if not self.client.bucket_exists(bucket):
                try:
                    # 创建 Bucket
                    self.client.make_bucket(bucket)
                    print(f"Bucket '{bucket}' 创建成功")
                except S3Error as e:
                    # 如果创建失败，打印错误（可能只是已存在的并发错误）
                    print(f"创建 Bucket '{bucket}' 时出错: {e}")

            # 配置存储桶为公开读取
            self._set_bucket_public_read(bucket)
            print(f"存储桶 {bucket} 已配置为公开读取")

    def _set_bucket_public_read(self, bucket_name: str):
        """
        设置存储桶为公开读取

        功能：
        - 使用 Bucket Policy 设置存储桶为公开读取
        - 所有对象都可以通过 URL 直接访问

        参数：
            bucket_name: 存储桶名称
        """
        # 定义公开读取的 Bucket Policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": f"PublicRead{bucket_name}",
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

        try:
            import json
            policy_str = json.dumps(bucket_policy)
            self.client.set_bucket_policy(bucket_name, policy_str)
            print(f"存储桶 {bucket_name} 已设置为公开读取")
        except Exception as e:
            print(f"设置存储桶 {bucket_name} 公开读取失败: {str(e)}")

    def upload_image(self, file: UploadFile, bucket_name: str) -> str:
        """
        上传图片到 MinIO

        参数：
            file: FastAPI 上传的文件对象（UploadFile 类型）
            bucket_name: 目标 Bucket 名称

        返回：
            str: 上传后的对象名称（UUID.扩展名）

        功能：
            1. 从文件名提取扩展名
            2. 生成唯一的对象名称（UUID）
            3. 读取文件内容并上传到 MinIO
            4. 返回对象名称供后续访问
        """
        # 从文件名中提取扩展名（如 jpg, png）
        # 如果文件名没有扩展名，默认为 jpg
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"

        # 生成唯一的对象名称：UUID + 扩展名
        # uuid.uuid4().hex 生成 32 位十六进制字符串
        object_name = f"{uuid.uuid4().hex}.{file_extension}"

        # 读取上传的文件内容
        file_content = file.file.read()

        # 将字节内容转换为 BytesIO 对象（MinIO SDK 需要）
        file_bytes = io.BytesIO(file_content)

        # 上传到 MinIO
        self.client.put_object(
            bucket_name=bucket_name,                    # Bucket 名称
            object_name=object_name,                    # 对象名称（Key）
            data=file_bytes,                          # 文件数据（BytesIO 对象）
            length=len(file_content),                 # 文件大小（字节数）
            content_type=file.content_type or "image/jpeg"  # MIME 类型
        )

        # 返回对象名称
        return object_name

    async def upload_image_async(self, file: UploadFile, bucket_name: str) -> str:
        """
        异步上传图片到 MinIO

        参数：
            file: FastAPI 上传的文件对象
            bucket_name: 目标 Bucket 名称

        返回：
            str: 上传后的对象名称

        功能：
            与 upload_image 类似，但是异步版本
            适用于 FastAPI 的异步路由
        """
        # 从文件名中提取扩展名
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"

        # 生成唯一的对象名称
        object_name = f"{uuid.uuid4().hex}.{file_extension}"

        # 异步读取上传的文件内容
        file_content = await file.read()

        # 转换为 BytesIO 对象
        file_bytes = io.BytesIO(file_content)

        # 上传到 MinIO
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_bytes,
            length=len(file_content),
            content_type=file.content_type or "image/jpeg"
        )

        return object_name

    def upload_result_image(self, image_bytes: bytes, extension: str = "jpg") -> str:
        """
        上传检测结果图片

        参数：
            image_bytes: 图片的字节数据
            extension: 图片扩展名，默认为 jpg

        返回：
            str: 上传后的对象名称

        功能：
            - 用于保存 YOLO 检测后的结果图片
            - 自动保存到结果图片 Bucket
            - 对象名称以 'result_' 为前缀，标识为结果图片
        """
        # 生成唯一的对象名称，以 result_ 为前缀
        object_name = f"result_{uuid.uuid4().hex}.{extension}"

        # 转换为 BytesIO 对象
        file_bytes = io.BytesIO(image_bytes)

        # 上传到结果图片 Bucket
        self.client.put_object(
            bucket_name=settings.minio.results_bucket,  # 结果图片存储桶
            object_name=object_name,                     # 对象名称
            data=file_bytes,                            # 文件数据
            length=len(image_bytes),                    # 文件大小
            content_type="image/jpeg"                   # MIME 类型
        )

        return object_name

    def upload_image_bytes(self, image_bytes: bytes, original_filename: str) -> str:
        """
        上传原始图片（字节数据）

        参数：
            image_bytes: 图片的字节数据
            original_filename: 原始文件名（用于提取扩展名）

        返回：
            str: 上传后的对象名称
        """
        # 从文件名提取扩展名
        file_extension = original_filename.split(".")[-1] if "." in original_filename else "jpg"
        
        # 生成唯一的对象名称
        object_name = f"{uuid.uuid4().hex}.{file_extension}"
        
        # 转换为 BytesIO 对象
        file_bytes = io.BytesIO(image_bytes)
        
        # 确定内容类型
        content_type = f"image/{file_extension}" if file_extension in ["jpg", "jpeg", "png", "gif"] else "image/jpeg"
        
        # 上传到原始图片 Bucket
        self.client.put_object(
            bucket_name=settings.minio.original_bucket,
            object_name=object_name,
            data=file_bytes,
            length=len(image_bytes),
            content_type=content_type
        )
        
        return object_name

    def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        生成预签名 URL（用于临时访问私有文件）

        参数：
            bucket_name: Bucket 名称
            object_name: 对象名称
            expires: URL 有效期（秒），默认 1 小时

        返回：
            Optional[str]: 预签名 URL，失败返回 None

        功能：
            - 为私有 Bucket 中的对象生成临时访问 URL
            - URL 包含签名信息，过期后无法访问
            - 适用于需要授权访问的私有文件
        """
        try:
            # 使用 MinIO SDK 生成预签名 GET URL
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,        # Bucket 名称
                object_name=object_name,       # 对象名称
                expires=expires                 # 过期时间（秒）
            )
            return url
        except S3Error:
            # 如果生成失败，返回 None
            return None

    def get_public_url(self, bucket_name: str, object_name: str) -> str:
        """
        生成公开访问 URL（适用于公开 Bucket）

        参数：
            bucket_name: Bucket 名称
            object_name: 对象名称

        返回：
            str: 公开访问 URL

        功能：
            - 直接生成公开可访问的 URL
            - 适用于设置为公开访问的 Bucket（如 rsod-original, rsod-results）
            - 格式：http://host:port/bucket/object
        """
        # 格式：http://主机:端口/Bucket/对象名
        return f"http://{settings.minio.host}:{settings.minio.port}/{bucket_name}/{object_name}"

    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        删除对象

        参数：
            bucket_name: Bucket 名称
            object_name: 对象名称

        返回：
            bool: 删除是否成功

        功能：
            - 从指定 Bucket 中删除对象
            - 删除后无法恢复，请谨慎使用
        """
        try:
            # 删除对象
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def list_objects(self, bucket_name: str, prefix: str = "") -> list:
        """
        列出 Bucket 中的对象

        参数：
            bucket_name: Bucket 名称
            prefix: 对象名称前缀过滤（可选）

        返回：
            list: 对象名称列表

        功能：
            - 列出指定 Bucket 中的所有对象
            - 可通过 prefix 参数过滤特定前缀的对象
        """
        try:
            # 获取对象列表
            objects = self.client.list_objects(bucket_name, prefix=prefix)

            # 提取并返回对象名称列表
            return [obj.object_name for obj in objects]
        except S3Error:
            # 如果列出失败，返回空列表
            return []

    def bucket_exists(self, bucket_name: str) -> bool:
        """
        检查 Bucket 是否存在

        参数：
            bucket_name: Bucket 名称

        返回：
            bool: 是否存在
        """
        return self.client.bucket_exists(bucket_name)


    def upload_model_file(self, local_file_path: str, model_name: str) -> str:
        """
        上传模型文件到 MinIO
        
        参数：
            local_file_path: 本地模型文件路径
            model_name: 模型名称（用于生成对象名）
            
        返回：
            str: 上传后的对象名称
        """
        # 提取文件扩展名
        file_extension = local_file_path.split(".")[-1] if "." in local_file_path else "pt"
        
        # 生成对象名称（格式：模型名_时间戳.扩展名）
        import time
        timestamp = int(time.time())
        object_name = f"{model_name}_{timestamp}.{file_extension}"
        
        # 读取本地文件
        with open(local_file_path, "rb") as f:
            file_content = f.read()
        
        # 转换为 BytesIO 对象
        file_bytes = io.BytesIO(file_content)
        
        # 上传到模型 Bucket
        self.client.put_object(
            bucket_name=settings.minio.models_bucket,
            object_name=object_name,
            data=file_bytes,
            length=len(file_content),
            content_type="application/octet-stream"
        )
        
        return object_name
    
    def download_model_file(self, object_name: str, local_save_path: str) -> bool:
        """
        从 MinIO 下载模型文件到本地
        
        参数：
            object_name: MinIO 中的对象名称
            local_save_path: 本地保存路径
            
        返回：
            bool: 是否下载成功
        """
        try:
            # 从 MinIO 获取文件
            response = self.client.get_object(settings.minio.models_bucket, object_name)
            
            # 读取文件内容
            file_content = response.read()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_save_path), exist_ok=True)
            
            # 保存到本地
            with open(local_save_path, "wb") as f:
                f.write(file_content)
            
            return True
        except Exception as e:
            print(f"下载模型失败: {str(e)}")
            return False
    
    def list_models(self) -> list:
        """
        列出模型 Bucket 中的所有模型
        
        返回：
            list: 模型对象名称列表
        """
        return self.list_objects(settings.minio.models_bucket)
    
    def delete_model(self, object_name: str) -> bool:
        """
        删除模型
        
        参数：
            object_name: 模型对象名称
            
        返回：
            bool: 是否删除成功
        """
        return self.delete_object(settings.minio.models_bucket, object_name)
    
    def get_latest_model(self, model_prefix: str = "rsod-yolo11n-best") -> Optional[str]:
        """
        获取最新版本的模型（兼容新旧两种格式）
        
        参数：
            model_prefix: 模型名称前缀（用于筛选）
            
        返回：
            Optional[str]: 最新模型的对象名称，无找到返回 None
        """
        try:
            models = self.list_models()
            
            # 筛选出符合前缀的模型（排除 metadata）
            model_files = [
                m for m in models 
                if m.startswith(model_prefix) 
                and not m.endswith("_metadata.json")
                and m.endswith(".pt")
            ]
            
            if not model_files:
                return None
            
            # 解析版本号并排序（兼容新旧格式）
            def parse_model_name(filename: str):
                try:
                    # 新格式：rsod-yolo11n-best_v1.0.0_20240101090000.pt
                    if '_v' in filename:
                        parts = filename.split('_v')
                        if len(parts) >= 2:
                            rest = parts[1].split('_')
                            if len(rest) >= 2:
                                version_str = rest[0]
                                timestamp_part = rest[1].split('.')[0]
                                try:
                                    major, minor, patch = map(int, version_str.split('.'))
                                    return (1, major, minor, patch, int(timestamp_part))
                                except:
                                    pass
                    
                    # 旧格式：rsod-yolo11n-best_1779125662.pt
                    if '_' in filename and not '_v' in filename:
                        parts = filename.rsplit('_', 1)
                        if len(parts) >= 2:
                            timestamp_part = parts[1].split('.')[0]
                            if timestamp_part.isdigit():
                                return (0, 0, 0, 0, int(timestamp_part))
                
                except:
                    pass
                
                # 如果解析失败，返回最低优先级
                return (-1, 0, 0, 0, 0)
            
            # 排序，选择最新的（新格式优先，同格式内按时间排序）
            model_files.sort(key=parse_model_name, reverse=True)
            return model_files[0]
            
        except Exception as e:
            print(f"获取最新模型失败: {str(e)}")
            return None
    
    def get_model_metadata(self, model_object_name: str) -> Optional[dict]:
        """
        获取模型的元数据
        
        参数：
            model_object_name: 模型对象名称（如 rsod-yolo11n-best_v1.0.0_20240101090000.pt）
            
        返回：
            Optional[dict]: 元数据字典，无找到返回 None
        """
        try:
            # 生成元数据文件名
            metadata_name = model_object_name.replace('.pt', '_metadata.json')
            
            # 从 MinIO 获取元数据
            response = self.client.get_object(settings.minio.models_bucket, metadata_name)
            metadata_content = response.read().decode('utf-8')
            
            import json
            return json.loads(metadata_content)
            
        except Exception as e:
            print(f"获取模型元数据失败: {str(e)}")
            return None
    
    def list_models_with_metadata(self, model_prefix: str = "rsod-yolo11n-best") -> list:
        """
        列出所有模型及其元数据
        
        参数：
            model_prefix: 模型名称前缀
            
        返回：
            list: 包含模型信息的字典列表
        """
        try:
            models = self.list_models()
            
            # 筛选出模型文件（排除 metadata）
            model_files = [
                m for m in models 
                if m.startswith(model_prefix) 
                and not m.endswith("_metadata.json")
                and m.endswith(".pt")
            ]
            
            result = []
            for model_file in model_files:
                metadata = self.get_model_metadata(model_file)
                result.append({
                    "object_name": model_file,
                    "metadata": metadata,
                    "public_url": self.get_public_url(settings.minio.models_bucket, model_file)
                })
            
            return result
            
        except Exception as e:
            print(f"列出模型失败: {str(e)}")
            return []


# =============================================================================
# 全局 MinIO 服务实例
# =============================================================================
# 创建全局唯一的 MinIO 服务实例（单例模式）
# 在应用的任何地方都可以通过 import minio_service 访问
minio_service = MinIOService()
