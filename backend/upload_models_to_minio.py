#!/usr/bin/env python3
"""
上传模型到 MinIO

功能：
    将本地的模型文件上传到 MinIO 对象存储
    支持批量上传和单个上传

使用方法：
    1. 上传所有模型：
        python upload_models_to_minio.py
    
    2. 上传指定模型：
        python upload_models_to_minio.py <模型文件路径>

作者：AI 训练计划
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.minio_service import minio_service
from app.config import BACKEND_DIR


def upload_model(local_path, model_name=None):
    """
    上传单个模型
    
    参数：
        local_path: 本地模型文件路径
        model_name: 模型名称（可选，自动从文件名推导）
        
    返回：
        str: 上传后的对象名称
    """
    if not os.path.exists(local_path):
        print(f"❌ 错误：文件不存在 - {local_path}")
        return None
    
    if model_name is None:
        model_name = os.path.basename(local_path).split('.')[0]
    
    print(f"📤 上传模型：{model_name}")
    print(f"   文件路径：{local_path}")
    
    try:
        object_name = minio_service.upload_model_file(local_path, model_name)
        print(f"✅ 上传成功！")
        print(f"   对象名称：{object_name}")
        print(f"   访问 URL：{minio_service.get_public_url(settings.minio.models_bucket, object_name)}")
        return object_name
    except Exception as e:
        print(f"❌ 上传失败：{str(e)}")
        return None


def main():
    """
    主函数
    """
    print("=" * 60)
    print("📦 模型上传工具")
    print("=" * 60)
    
    # 模型文件列表
    model_files = [
        ("yolo11n.pt", "yolo11n"),
        ("rsod_yolo11n/weights/best.pt", "rsod-yolo11n-best"),
        ("rsod_yolo11n/weights/last.pt", "rsod-yolo11n-last"),
    ]
    
    uploaded_models = []
    
    # 上传所有模型
    for model_path, model_name in model_files:
        full_path = os.path.join(BACKEND_DIR, "models", model_path)
        
        if os.path.exists(full_path):
            print()
            object_name = upload_model(full_path, model_name)
            if object_name:
                uploaded_models.append(object_name)
        else:
            print(f"⚠️ 跳过，文件不存在：{model_path}")
    
    print()
    print("=" * 60)
    print("📊 上传完成！")
    print(f"成功上传 {len(uploaded_models)} 个模型")
    print()
    
    # 列出所有模型
    print("📦 MinIO 模型列表：")
    models_list = minio_service.list_models()
    for m in models_list:
        print(f"   - {m}")
    
    print("=" * 60)


if __name__ == "__main__":
    # 导入配置
    from app.config import settings
    
    if len(sys.argv) > 1:
        # 上传单个模型
        model_path = sys.argv[1]
        upload_model(model_path)
    else:
        # 批量上传
        main()

