#!/usr/bin/env python3
"""
YOLO 模型训练工具 - 生产环境版本

功能：
    - 训练自定义 YOLO 模型（基于 RSOD 数据集）
    - 支持模型评估、指标记录、训练日志
    - 自动保存最佳模型和训练配置
    - 训练完成后自动上传到 MinIO
    - 模型语义化版本管理
    - 模型元数据保存

使用方式：
    python train_model.py --epochs 100 --batch 16 --device cpu --version 1.0.0
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("未安装 ultralytics 库，请运行: pip install ultralytics")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class YOLOTrainer:
    """
    YOLO 模型训练器
    
    负责训练、评估和管理 YOLO 目标检测模型
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化训练器
        
        参数：
            base_dir: 项目基础目录
        """
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(base_dir)
        
        # 路径配置
        self.data_dir = self.base_dir / "data" / "rsod"
        self.models_dir = self.base_dir / "models"
        self.logs_dir = self.base_dir / "logs"
        
        # 数据集配置
        self.dataset_yaml = self.data_dir / "yolo_dataset" / "rsod.yaml"
        
        # 训练配置
        self.default_config = {
            "epochs": 100,
            "batch": 16,
            "imgsz": 640,
            "device": "cpu",
            "patience": 20,
            "lr0": 0.01,
            "lrf": 0.01,
            "momentum": 0.937,
            "weight_decay": 0.0005
        }
        
        # 初始化 MinIO 服务
        self.minio_service = None
        self.minio_available = False
        self._init_minio_service()
        
        # 确保目录存在
        self._ensure_directories()
    
    def _init_minio_service(self):
        """初始化 MinIO 服务"""
        try:
            sys.path.insert(0, str(self.base_dir))
            from app.services.minio_service import minio_service
            self.minio_service = minio_service
            self.minio_available = True
            logger.info("MinIO 服务初始化成功")
        except Exception as e:
            logger.warning(f"MinIO 服务初始化失败: {str(e)}")
            self.minio_available = False
    
    def _ensure_directories(self):
        """确保必要目录存在"""
        directories = [
            self.models_dir,
            self.logs_dir
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_dataset(self) -> bool:
        """
        验证数据集是否存在
        
        返回：
            bool: 验证是否通过
        """
        if not self.dataset_yaml.exists():
            logger.error(f"数据集配置文件不存在: {self.dataset_yaml}")
            logger.error("请先运行: python convert_rsod.py")
            return False
        
        logger.info(f"数据集配置: {self.dataset_yaml}")
        return True
    
    def _get_next_version(self, model_name: str = "rsod-yolo11n") -> str:
        """
        获取下一个版本号（语义化版本）
        
        参数：
            model_name: 模型名称
            
        返回：
            str: 版本号，如 "1.0.0"
        """
        if not self.minio_available:
            logger.warning("MinIO 不可用，使用默认版本号 1.0.0")
            return "1.0.0"
        
        try:
            # 获取 MinIO 中的所有模型
            models = self.minio_service.list_models()
            
            # 解析已存在的版本号
            versions = []
            for model_file in models:
                if model_name in model_file:
                    # 从文件名中提取版本号 rsod-yolo11n-best_v1.0.0_20240101090000.pt
                    try:
                        parts = model_file.split('_v')
                        if len(parts) > 1:
                            version_part = parts[1].split('_')[0]
                            # 验证是有效的版本号
                            if len(version_part.split('.')) == 3:
                                versions.append(version_part)
                    except:
                        continue
            
            if not versions:
                return "1.0.0"
            
            # 找出最大版本号
            def parse_version(v):
                parts = v.split('.')
                return tuple(map(int, parts))
            
            latest_version = max(versions, key=parse_version)
            
            # 自动递增修订版本号
            major, minor, patch = parse_version(latest_version)
            return f"{major}.{minor}.{patch + 1}"
            
        except Exception as e:
            logger.warning(f"获取版本号失败: {str(e)}，使用默认版本号 1.0.0")
            return "1.0.0"
    
    def _save_metadata(self, metadata: dict, output_path: Path):
        """
        保存模型元数据
        
        参数：
            metadata: 元数据字典
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"模型元数据已保存: {output_path}")
    
    def train(self, config: dict = None, version: str = None) -> Optional[dict]:
        """
        训练 YOLO 模型
        
        参数：
            config: 训练配置字典
            version: 模型版本号（可选）
            
        返回：
            dict: 包含训练结果和元数据的字典
        """
        # 使用默认配置或用户配置
        train_config = {**self.default_config, **(config or {})}
        
        # 如果未指定版本，自动获取下一个版本
        if version is None:
            version = self._get_next_version()
            logger.info(f"使用自动生成的版本号: {version}")
        else:
            logger.info(f"使用指定的版本号: {version}")
        
        logger.info("=" * 60)
        logger.info("开始训练 YOLO 模型")
        logger.info("=" * 60)
        
        # 验证数据集
        if not self._validate_dataset():
            return None
        
        # 打印训练配置
        logger.info("\n训练配置:")
        for key, value in train_config.items():
            logger.info(f"  {key}: {value}")
        
        try:
            # 加载预训练模型
            logger.info("\n加载预训练模型...")
            model = YOLO("yolo11n.pt")
            
            # 获取当前时间戳，用于保存训练日志
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 训练参数
            results = model.train(
                data=str(self.dataset_yaml),
                epochs=train_config["epochs"],
                imgsz=train_config["imgsz"],
                batch=train_config["batch"],
                device=train_config["device"],
                name=f"rsod_yolo11n_{timestamp}",
                project=str(self.models_dir),
                exist_ok=True,
                plots=True,
                patience=train_config["patience"],
                lr0=train_config["lr0"],
                lrf=train_config["lrf"],
                momentum=train_config["momentum"],
                weight_decay=train_config["weight_decay"],
                save=True,
                val=True,
                cache=False
            )
            
            # 保存训练配置
            self._save_train_config(train_config, timestamp)
            
            logger.info("\n" + "=" * 60)
            logger.info("训练完成！")
            logger.info("=" * 60)
            
            # 获取最佳模型路径
            best_model_path = self.models_dir / f"rsod_yolo11n_{timestamp}" / "weights" / "best.pt"
            logger.info(f"最佳模型路径: {best_model_path}")
            
            # 更新符号链接（便于后续使用）
            self._update_model_link(best_model_path)
            
            # 评估模型并获取指标
            metrics = self.evaluate(str(best_model_path))
            
            # 构建元数据
            metadata = {
                "name": "rsod-yolo11n",
                "version": version,
                "created_at": datetime.now().isoformat(),
                "description": "RSOD 数据集训练的 YOLO11 目标检测模型",
                "metrics": {
                    "mAP50": metrics["mAP50"] if metrics else 0.0,
                    "mAP50-95": metrics["mAP50-95"] if metrics else 0.0,
                    "precision": metrics["precision"] if metrics else 0.0,
                    "recall": metrics["recall"] if metrics else 0.0,
                    "f1": metrics["f1"] if metrics else 0.0
                },
                "config": train_config,
                "dataset": str(self.dataset_yaml)
            }
            
            # 保存元数据到本地
            metadata_path = best_model_path.parent.parent / "metadata.json"
            self._save_metadata(metadata, metadata_path)
            
            # 上传模型和元数据到 MinIO
            self._upload_model_to_minio(best_model_path, version, metadata)
            
            return {
                "model_path": best_model_path,
                "metadata": metadata,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"训练失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_train_config(self, config: dict, timestamp: str):
        """
        保存训练配置
        
        参数：
            config: 训练配置
            timestamp: 时间戳
        """
        config_path = self.models_dir / f"rsod_yolo11n_{timestamp}" / "train_config.json"
        
        config_data = {
            "timestamp": timestamp,
            "config": config,
            "dataset": str(self.dataset_yaml),
            "created_at": datetime.now().isoformat()
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"训练配置已保存: {config_path}")
    
    def _update_model_link(self, model_path: Path):
        """
        更新模型符号链接
        
        参数：
            model_path: 模型路径
        """
        # 创建/更新最新模型链接
        latest_link = self.models_dir / "rsod_yolo11n"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        
        # 创建目录链接
        latest_link.symlink_to(model_path.parent.parent)
        logger.info(f"更新模型链接: {latest_link} -> {model_path.parent.parent}")
    
    def _upload_model_to_minio(self, model_path: Path, version: str, metadata: dict):
        """
        上传训练好的模型到 MinIO
        
        参数：
            model_path: 本地模型文件路径
            version: 版本号
            metadata: 模型元数据
        """
        if not self.minio_available:
            logger.warning("MinIO 服务不可用，跳过模型上传")
            return
        
        if not model_path.exists():
            logger.warning(f"模型文件不存在，跳过上传: {model_path}")
            return
        
        try:
            logger.info(f"\n正在上传模型到 MinIO...")
            
            # 生成带语义化版本和时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            base_model_name = f"rsod-yolo11n-best_v{version}_{timestamp}"
            object_name = f"{base_model_name}.pt"
            
            # 上传最佳模型
            logger.info(f"  模型名称: {object_name}")
            logger.info(f"  文件路径: {model_path}")
            
            object_name = self.minio_service.upload_model_file(str(model_path), base_model_name)
            
            # 获取公开访问 URL
            public_url = self.minio_service.get_public_url(
                "rsod-models",
                object_name
            )
            
            logger.info(f"✅ 模型上传成功！")
            logger.info(f"   对象名称: {object_name}")
            logger.info(f"   访问 URL: {public_url}")
            
            # 上传 last.pt 模型（如果存在）
            last_model_path = model_path.parent / "last.pt"
            if last_model_path.exists():
                last_base_name = f"rsod-yolo11n-last_v{version}_{timestamp}"
                last_object_name = self.minio_service.upload_model_file(
                    str(last_model_path), 
                    last_base_name
                )
                last_public_url = self.minio_service.get_public_url(
                    "rsod-models",
                    last_object_name
                )
                logger.info(f"   同时上传了 last.pt: {last_object_name}")
                logger.info(f"   访问 URL: {last_public_url}")
            
            # 上传元数据 JSON
            metadata_filename = f"{base_model_name}_metadata.json"
            metadata_content = json.dumps(metadata, indent=2, ensure_ascii=False)
            
            # 使用 BytesIO 保存元数据
            import io
            metadata_bytes = io.BytesIO(metadata_content.encode('utf-8'))
            
            # 上传元数据
            metadata_object_name = metadata_filename
            self.minio_service.client.put_object(
                bucket_name="rsod-models",
                object_name=metadata_object_name,
                data=metadata_bytes,
                length=len(metadata_content),
                content_type="application/json"
            )
            
            metadata_public_url = self.minio_service.get_public_url(
                "rsod-models",
                metadata_object_name
            )
            
            logger.info(f"   同时上传了元数据: {metadata_object_name}")
            logger.info(f"   访问 URL: {metadata_public_url}")
            
        except Exception as e:
            logger.error(f"❌ 模型上传失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def evaluate(self, model_path: str = None) -> Optional[dict]:
        """
        评估训练好的模型
        
        参数：
            model_path: 模型路径，默认为最新训练的模型
            
        返回：
            dict: 评估指标
        """
        if model_path is None:
            # 使用默认路径
            model_path = self.models_dir / "rsod_yolo11n" / "weights" / "best.pt"
        else:
            model_path = Path(model_path)
        
        if not model_path.exists():
            logger.error(f"模型文件不存在: {model_path}")
            return None
        
        logger.info(f"\n开始评估模型: {model_path}")
        
        try:
            model = YOLO(str(model_path))
            metrics = model.val(data=str(self.dataset_yaml))
            
            # 提取关键指标
            results = {
                "mAP50": float(metrics.box.map50),
                "mAP50-95": float(metrics.box.map),
                "precision": float(metrics.box.mp),
                "recall": float(metrics.box.mr),
                "f1": float(metrics.box.mf1),
                "speed": {
                    "preprocess": metrics.speed.get("preprocess", 0),
                    "inference": metrics.speed.get("inference", 0),
                    "postprocess": metrics.speed.get("postprocess", 0)
                }
            }
            
            logger.info("\n评估结果:")
            logger.info(f"  mAP50: {results['mAP50']:.4f}")
            logger.info(f"  mAP50-95: {results['mAP50-95']:.4f}")
            logger.info(f"  Precision: {results['precision']:.4f}")
            logger.info(f"  Recall: {results['recall']:.4f}")
            logger.info(f"  F1: {results['f1']:.4f}")
            
            # 保存评估结果
            eval_path = model_path.parent.parent / "evaluation_results.json"
            with open(eval_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"\n评估结果已保存: {eval_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"评估失败: {str(e)}")
            return None
    
    def predict(self, image_path: str, model_path: str = None, conf: float = 0.3):
        """
        使用模型进行预测
        
        参数：
            image_path: 图片路径
            model_path: 模型路径
            conf: 置信度阈值
            
        返回：
            results: 预测结果
        """
        if model_path is None:
            model_path = self.models_dir / "rsod_yolo11n" / "weights" / "best.pt"
        
        if not Path(model_path).exists():
            logger.error(f"模型文件不存在: {model_path}")
            return None
        
        if not Path(image_path).exists():
            logger.error(f"图片文件不存在: {image_path}")
            return None
        
        model = YOLO(str(model_path))
        results = model.predict(
            source=image_path,
            conf=conf,
            save=True,
            save_txt=True
        )
        
        return results


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="YOLO 模型训练工具")
    
    # 训练参数
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="训练轮数 (默认: 100)"
    )
    
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="批次大小 (默认: 16)"
    )
    
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="输入图片尺寸 (默认: 640)"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="训练设备 (cpu/cuda/0, 默认: cpu)"
    )
    
    parser.add_argument(
        "--patience",
        type=int,
        default=20,
        help="早停耐心值 (默认: 20)"
    )
    
    # 模型版本
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="模型版本号 (默认: 自动递增)"
    )
    
    # 评估参数
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="仅评估模型"
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="模型路径"
    )
    
    # 预测参数
    parser.add_argument(
        "--predict",
        type=str,
        default=None,
        help="预测图片路径"
    )
    
    parser.add_argument(
        "--conf",
        type=float,
        default=0.3,
        help="置信度阈值 (默认: 0.3)"
    )
    
    # 其他参数
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 创建训练器
    trainer = YOLOTrainer()
    
    # 根据参数执行相应操作
    if args.predict:
        # 执行预测
        logger.info(f"执行预测: {args.predict}")
        trainer.predict(args.predict, model_path=args.model_path, conf=args.conf)
    
    elif args.evaluate:
        # 执行评估
        trainer.evaluate(model_path=args.model_path)
    
    else:
        # 执行训练
        config = {
            "epochs": args.epochs,
            "batch": args.batch,
            "imgsz": args.imgsz,
            "device": args.device,
            "patience": args.patience
        }
        
        trainer.train(config, version=args.version)


if __name__ == "__main__":
    main()

