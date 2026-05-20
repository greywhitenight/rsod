#!/usr/bin/env python3
"""
RSOD 数据集转换工具 - 生产环境版本

功能：
    - 将 RSOD 数据集（XML 标注格式）转换为 YOLO 格式
    - 支持数据集分割、数据校验、日志记录
    - 生成标准的 YOLO 数据集配置文件

使用方式：
    python convert_rsod.py [--split 0.8] [--seed 42] [--verbose]
"""

import os
import sys
import argparse
import logging
import xml.etree.ElementTree as ET
import shutil
import random
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 类别映射（RSOD 数据集 4 类）
CLASSES = ["aircraft", "oiltank", "overpass", "playground"]
CLASS_MAP = {cls: idx for idx, cls in enumerate(CLASSES)}


class RSODConverter:
    """
    RSOD 数据集转换类
    
    负责将 RSOD 数据集从 Pascal VOC 格式（XML）转换为 YOLO 格式
    """
    
    def __init__(self, base_dir: str = None, split_ratio: float = 0.8, seed: int = 42):
        """
        初始化转换器
        
        参数：
            base_dir: 项目基础目录，默认为脚本所在目录的父目录
            split_ratio: 训练集占比，默认 0.8
            seed: 随机种子，确保结果可复现
        """
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(base_dir)
            
        self.split_ratio = split_ratio
        self.seed = seed
        
        # 路径配置
        self.rsod_dir = self.base_dir / "data" / "rsod"
        self.yolo_dir = self.rsod_dir / "yolo_dataset"
        
        # YOLO 数据集目录结构
        self.train_images_dir = self.yolo_dir / "images" / "train"
        self.val_images_dir = self.yolo_dir / "images" / "val"
        self.train_labels_dir = self.yolo_dir / "labels" / "train"
        self.val_labels_dir = self.yolo_dir / "labels" / "val"
        
        # 原始数据目录
        self.annotations_dir = self.rsod_dir / "annotations"
        self.images_dir = self.rsod_dir / "images"
        
        # 统计信息
        self.stats = {
            "total_files": 0,
            "train_files": 0,
            "val_files": 0,
            "skipped_files": 0,
            "converted_files": 0
        }
    
    def _create_directories(self):
        """创建必要的目录结构"""
        directories = [
            self.train_images_dir,
            self.val_images_dir,
            self.train_labels_dir,
            self.val_labels_dir
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建目录: {dir_path}")
    
    def _validate_input_data(self) -> bool:
        """
        验证输入数据是否完整
        
        返回：
            bool: 验证是否通过
        """
        logger.info("开始验证输入数据...")
        
        # 检查标注目录
        if not self.annotations_dir.exists():
            logger.error(f"标注目录不存在: {self.annotations_dir}")
            return False
        
        # 检查图片目录
        if not self.images_dir.exists():
            logger.error(f"图片目录不存在: {self.images_dir}")
            return False
        
        # 获取所有 XML 文件
        xml_files = list(self.annotations_dir.glob("*.xml"))
        if len(xml_files) == 0:
            logger.error("未找到任何 XML 标注文件")
            return False
        
        self.stats["total_files"] = len(xml_files)
        logger.info(f"找到 {self.stats['total_files']} 个标注文件")
        
        return True
    
    def _convert_xml_to_yolo(self, xml_path: Path) -> str:
        """
        将单个 XML 文件转换为 YOLO 格式
        
        参数：
            xml_path: XML 文件路径
        
        返回：
            str: YOLO 格式的标注内容
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 获取图片尺寸
            size = root.find("size")
            if size is None:
                logger.warning(f"XML 文件缺少 size 标签: {xml_path}")
                return ""
            
            width = int(size.find("width").text)
            height = int(size.find("height").text)
            
            lines = []
            for obj in root.findall("object"):
                name = obj.find("name").text
                if name not in CLASS_MAP:
                    logger.warning(f"未知类别 '{name}'，已跳过")
                    continue
                
                class_id = CLASS_MAP[name]
                bbox = obj.find("bndbox")
                
                xmin = int(bbox.find("xmin").text)
                ymin = int(bbox.find("ymin").text)
                xmax = int(bbox.find("xmax").text)
                ymax = int(bbox.find("ymax").text)
                
                # 转换为 YOLO 格式（归一化）
                x_center = (xmin + xmax) / 2.0 / width
                y_center = (ymin + ymax) / 2.0 / height
                bbox_width = (xmax - xmin) / width
                bbox_height = (ymax - ymin) / height
                
                lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
            
            return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"转换 XML 文件失败 {xml_path}: {str(e)}")
            return ""
    
    def _create_yaml_config(self):
        """创建 YOLO 数据集配置文件"""
        yaml_content = f"""# RSOD 数据集配置文件
# 数据集路径（相对于运行目录）
path: {self.yolo_dir.resolve()}

# 训练/验证集路径
train: images/train
val: images/val

# 类别数量和名称
nc: {len(CLASSES)}
names: {CLASSES}

# 数据集描述
# RSOD (Remote Sensing Object Detection) 数据集
# 包含 4 类遥感目标：飞机(aircraft)、油罐(oiltank)、立交桥(overpass)、操场(playground)
"""
        
        yaml_path = self.yolo_dir / "rsod.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        
        logger.info(f"创建数据集配置文件: {yaml_path}")
    
    def _copy_files(self, xml_files: list, is_train: bool):
        """
        复制文件到目标目录
        
        参数：
            xml_files: XML 文件列表
            is_train: 是否为训练集
        """
        images_dir = self.train_images_dir if is_train else self.val_images_dir
        labels_dir = self.train_labels_dir if is_train else self.val_labels_dir
        
        for xml_file in xml_files:
            try:
                # 获取图片路径
                img_name = xml_file.stem + ".jpg"
                img_path = self.images_dir / img_name
                
                # 检查图片是否存在
                if not img_path.exists():
                    logger.warning(f"图片不存在，跳过: {img_path}")
                    self.stats["skipped_files"] += 1
                    continue
                
                # 转换标注
                yolo_content = self._convert_xml_to_yolo(xml_file)
                
                # 写入标注文件
                label_file = labels_dir / (xml_file.stem + ".txt")
                with open(label_file, "w") as f:
                    f.write(yolo_content)
                
                # 复制图片
                shutil.copy(img_path, images_dir / img_name)
                
                self.stats["converted_files"] += 1
                
                if is_train:
                    self.stats["train_files"] += 1
                else:
                    self.stats["val_files"] += 1
                    
            except Exception as e:
                logger.error(f"处理文件失败 {xml_file}: {str(e)}")
                self.stats["skipped_files"] += 1
    
    def convert(self):
        """
        执行完整的数据集转换流程
        
        返回：
            bool: 转换是否成功
        """
        logger.info("=" * 60)
        logger.info("开始 RSOD 数据集转换")
        logger.info("=" * 60)
        
        # 验证输入数据
        if not self._validate_input_data():
            return False
        
        # 创建目录结构
        self._create_directories()
        
        # 获取所有 XML 文件并打乱
        xml_files = list(self.annotations_dir.glob("*.xml"))
        random.seed(self.seed)
        random.shuffle(xml_files)
        
        # 分割数据集
        split_idx = int(len(xml_files) * self.split_ratio)
        train_files = xml_files[:split_idx]
        val_files = xml_files[split_idx:]
        
        logger.info(f"数据集分割: 训练集 {len(train_files)} 个, 验证集 {len(val_files)} 个")
        
        # 转换训练集
        logger.info("正在转换训练集...")
        self._copy_files(train_files, is_train=True)
        
        # 转换验证集
        logger.info("正在转换验证集...")
        self._copy_files(val_files, is_train=False)
        
        # 创建配置文件
        self._create_yaml_config()
        
        # 输出统计信息
        self._print_stats()
        
        logger.info("=" * 60)
        logger.info("数据集转换完成！")
        logger.info("=" * 60)
        
        return True
    
    def _print_stats(self):
        """打印转换统计信息"""
        logger.info("\n转换统计:")
        logger.info(f"  总文件数: {self.stats['total_files']}")
        logger.info(f"  训练集: {self.stats['train_files']}")
        logger.info(f"  验证集: {self.stats['val_files']}")
        logger.info(f"  转换成功: {self.stats['converted_files']}")
        logger.info(f"  跳过: {self.stats['skipped_files']}")
        logger.info(f"\n输出目录: {self.yolo_dir}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="RSOD 数据集转换工具")
    
    parser.add_argument(
        "--split",
        type=float,
        default=0.8,
        help="训练集占比 (默认: 0.8)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子 (默认: 42)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="项目基础目录"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 创建转换器并执行转换
    converter = RSODConverter(
        base_dir=args.base_dir,
        split_ratio=args.split,
        seed=args.seed
    )
    
    success = converter.convert()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
