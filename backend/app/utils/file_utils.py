# =============================================================================
# 文件工具模块
# =============================================================================
# 功能说明：
#   - 提供文件操作的工具函数
#   - 处理文件上传、保存、路径生成等操作
#   - 管理静态文件目录结构
#
# 主要功能：
#   - ensure_directories(): 确保必要的目录存在
#   - generate_unique_filename(): 生成唯一的文件名
#   - save_upload_file(): 保存上传的文件
#   - get_file_url(): 生成文件的访问 URL
#
# 使用示例：
#   from app.utils.file_utils import save_upload_file, get_file_url
#
#   # 保存上传的文件
#   filename = await save_upload_file(file, "static/uploads")
#
#   # 生成文件访问 URL
#   url = get_file_url(filename, "static/uploads")
# =============================================================================

# 导入 os 模块，用于文件路径操作
import os

# 导入 uuid 模块，用于生成唯一标识符
import uuid

# 导入 Path 模块，用于路径操作
from pathlib import Path

# 导入 FastAPI 的 UploadFile 类型
from fastapi import UploadFile

# 导入应用配置
from app.config import settings


def ensure_directories():
    """
    确保必要的目录存在

    功能：
    - 检查上传文件目录是否存在
    - 检查结果文件目录是否存在
    - 如果不存在，自动创建

    说明：
    - 在应用启动时调用
    - 确保检测服务可以正常保存文件
    """
    # 创建上传文件目录
    # parents=True: 创建父目录（如果不存在）
    # exist_ok=True: 如果目录已存在，不报错
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    # 创建检测结果文件目录
    Path(settings.result_dir).mkdir(parents=True, exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名

    功能：
    - 保留原始文件的扩展名
    - 添加 UUID 前缀确保唯一性
    - 避免文件名冲突

    参数：
        original_filename: 原始文件名（如 "image.jpg"）

    返回：
        str: 唯一的文件名（如 "temp_a1b2c3d4e5f6.jpg"）

    示例：
        >>> generate_unique_filename("image.jpg")
        'temp_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d.jpg'
    """
    # 从原始文件名提取扩展名（包含点号）
    ext = Path(original_filename).suffix

    # 生成唯一的文件名
    # 格式：temp_{UUID十六进制}.{扩展名}
    # UUID 确保在分布式环境下也不会冲突
    unique_name = f"temp_{uuid.uuid4().hex}{ext}"

    return unique_name


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    """
    保存上传的文件

    功能：
    - 接收 FastAPI 上传的文件
    - 生成唯一的文件名
    - 将文件内容写入磁盘

    参数：
        file: FastAPI 上传的文件对象
        upload_dir: 上传目录路径

    返回：
        str: 保存后的文件名（不含路径）

    注意：
        - 这是异步函数，需要使用 await 调用
        - 文件会覆盖已存在的同名文件
    """
    # 生成唯一的文件名
    filename = generate_unique_filename(file.filename)

    # 构建完整的文件路径
    filepath = os.path.join(upload_dir, filename)

    # 以二进制写入模式打开文件
    with open(filepath, "wb") as buffer:
        # 异步读取文件内容
        content = await file.read()

        # 写入文件
        buffer.write(content)

    # 返回文件名（不含路径）
    return filename


def get_file_url(filename: str, directory: str) -> str:
    """
    生成文件的访问 URL

    功能：
    - 根据文件名和目录生成完整的访问 URL
    - 用于在 API 响应中返回文件访问路径

    参数：
        filename: 文件名
        directory: 文件所在目录（如 "static/uploads"）

    返回：
        str: 完整的文件访问 URL

    示例：
        >>> get_file_url("image.jpg", "static/uploads")
        'http://localhost:8000/static/uploads/image.jpg'
    """
    # 格式：http://localhost:8000/{directory}/{filename}
    return f"http://localhost:8000/{directory}/{filename}"
