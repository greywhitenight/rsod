# Day 2: 前端模板对接 + 单图检测全流程打通

> 学习目标：掌握图片上传API开发、YOLO推理服务集成、检测结果返回格式定义、前端检测界面开发及历史记录展示

---

## 📋 今日任务清单

- [ ] 图片上传API开发
- [ ] YOLO推理服务集成
- [ ] 检测结果返回格式定义
- [ ] 前端检测界面开发
- [ ] 历史记录列表展示

---

## 一、后端检测服务开发

### 1.1 检测服务核心代码

创建检测服务类，封装 YOLO 目标检测模型的所有操作：

```python
# backend/app/services/detection_service.py

# =============================================================================
# 目标检测服务模块
# =============================================================================
# 功能说明：
#   - 封装 YOLO 目标检测模型的所有操作
#   - 提供单图检测、批量检测等接口
#   - 支持绘制检测框并保存结果图片
#   - 检测结果持久化存储到数据库

import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ultralytics import YOLO
import cv2

from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.models.database import DetectionRecord, DetectionResult as DBDetectionResult
from app.database import get_db
from app.utils.file_utils import get_file_url

import logging
logger = logging.getLogger(__name__)


class DetectionService:
    """
    目标检测服务类
    
    该类封装了 YOLO 目标检测的所有操作，包括：
    - 模型加载和初始化
    - 单图检测
    - 检测结果处理和可视化
    - 检测结果持久化存储
    """

    def __init__(self):
        """
        初始化检测服务
        - 加载 YOLO 模型权重
        - 初始化类别名称映射（RSOD 数据集 4 类）
        """
        self.model = None
        self.class_names = {}
        
        # 加载模型
        self._load_model()
        # 初始化类别映射
        self._init_class_names()

    def _load_model(self):
        """加载 YOLO 模型"""
        if os.path.exists(settings.yolo_model_path):
            self.model = YOLO(settings.yolo_model_path)
            logger.info(f"模型加载成功: {settings.yolo_model_path}")
        else:
            raise FileNotFoundError(f"模型文件未找到: {settings.yolo_model_path}")

    def _init_class_names(self):
        """
        初始化 RSOD 数据集类别映射
        - 0: aircraft (飞机)
        - 1: oiltank (油罐)
        - 2: overpass (立交桥)
        - 3: playground (操场)
        """
        self.class_names = {
            0: "aircraft",
            1: "oiltank",
            2: "overpass",
            3: "playground",
        }

    def get_class_chinese_name(self, class_name: str) -> str:
        """获取类别的中文名称"""
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
                           model_name: str = "rsod-yolo11n") -> DetectionResult:
        """
        单图目标检测核心方法
        
        参数：
            image_path: 图片文件路径
            user_id: 用户 ID（可选）
            model_name: 模型名称（可选）
        
        返回：
            DetectionResult: 检测结果对象
        """
        # 记录检测开始时间
        start_time = time.time()
        
        # 生成唯一检测 ID
        detection_id = str(uuid.uuid4())

        # 调用 YOLO 模型进行预测
        # conf: 置信度阈值，只保留高于此值的检测结果
        # iou: 非极大值抑制 IOU 阈值
        results = self.model.predict(
            source=image_path,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            save=False
        )

        # 解析检测结果
        boxes = []  # 检测框列表
        db_results = []  # 数据库结果列表

        for result in results:
            for box in result.boxes:
                # 提取检测框坐标（xyxy 格式）
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # 提取置信度和类别信息
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names.get(class_id, f"class_{class_id}")
                chinese_name = self.get_class_chinese_name(class_name)

                # 添加到检测框列表
                boxes.append(DetectionBox(
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

                # 添加到数据库结果列表
                db_results.append(DBDetectionResult(
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

        # 生成结果文件名并保存结果图片
        result_filename = f"result_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(settings.result_dir, result_filename)
        
        # 绘制检测框到图片
        annotated_image = results[0].plot()
        annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(result_path, annotated_image_bgr)

        # 计算检测耗时
        detection_time = time.time() - start_time

        # 保存检测记录到数据库
        image_filename = os.path.basename(image_path)
        self._save_to_database(
            user_id=user_id,
            detection_id=detection_id,
            model_name=model_name,
            total_objects=len(boxes),
            detection_time=detection_time,
            original_image_key=f"uploads/{image_filename}",
            result_image_key=f"results/{result_filename}",
            results=db_results
        )

        # 返回检测结果
        return DetectionResult(
            detection_id=detection_id,
            image_url=get_file_url(image_filename, "static/uploads"),
            result_image_url=get_file_url(result_filename, "static/results"),
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=round(detection_time, 3),
            model_name=model_name,
            created_at=datetime.now()
        )

    def _save_to_database(self, **kwargs):
        """将检测记录保存到 PostgreSQL 数据库"""
        try:
            db = next(get_db())
            
            # 创建检测记录
            record = DetectionRecord(
                id=kwargs['detection_id'],
                user_id=kwargs['user_id'],
                type="single",
                status="completed",
                model_name=kwargs['model_name'],
                model_version="1.0.0",
                total_objects=kwargs['total_objects'],
                detection_time=kwargs['detection_time'],
                original_image_key=kwargs['original_image_key'],
                result_image_key=kwargs['result_image_key']
            )
            
            db.add(record)
            
            # 添加检测结果
            for result in kwargs['results']:
                result.record_id = kwargs['detection_id']
                db.add(result)
            
            db.commit()
            logger.info(f"检测记录已保存到数据库: {kwargs['detection_id']}")
            
        except Exception as e:
            logger.error(f"保存检测记录失败: {str(e)}")
            db.rollback()

    def get_detection_history(self, user_id: str = None, limit: int = 10) -> List[DetectionRecord]:
        """获取检测历史记录"""
        try:
            db = next(get_db())
            query = db.query(DetectionRecord).order_by(DetectionRecord.created_at.desc())
            
            if user_id:
                query = query.filter(DetectionRecord.user_id == user_id)
            
            return query.limit(limit).all()
        
        except Exception as e:
            logger.error(f"获取检测历史失败: {str(e)}")
            return []


# 创建全局检测服务实例
detection_service = DetectionService()
```

### 1.2 检测API路由开发

```python
# backend/app/api/detection.py

"""
检测 API 路由模块
- POST /api/detection/single    - 单图检测
- GET  /api/detection/history   - 获取检测历史记录
- GET  /api/detection/{id}      - 获取单个检测记录
- DELETE /api/detection/{id}    - 删除检测记录
- GET  /api/detection/targets/list - 获取可检测目标列表
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories, get_file_url
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse, HistoryResponse, 
    TargetListResponse, TargetItem, HistoryItem
)

router = APIRouter(prefix="/detection", tags=["detection"])

# 确保目录存在
ensure_directories()


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),      # 上传的图片文件（必填）
    model_name: str = Form("rsod-yolo11n"),  # 使用的模型名称
    user_id: str = Form(None)          # 用户 ID（可选）
):
    """
    单图目标检测接口
    
    参数：
        file: 上传的图片文件，支持 jpg、png 等格式
        model_name: 使用的模型名称（默认 rsod-yolo11n）
        user_id: 用户 ID（可选）
    
    返回：
        SingleDetectionResponse: 包含检测结果的响应
    """
    try:
        # 保存上传的文件
        filename = await save_upload_file(file, settings.upload_dir)
        image_path = os.path.join(settings.upload_dir, filename)
        
        # 调用检测服务
        result = detection_service.detect_single_image(image_path, user_id, model_name)
        
        return SingleDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, message="模型文件未找到", detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, message="检测失败", detail=str(e))


@router.get("/history", response_model=HistoryResponse)
async def get_detection_history(
    page: int = 1,        # 页码（从 1 开始）
    page_size: int = 10,   # 每页记录数
    user_id: str = None    # 用户 ID（可选）
):
    """获取检测历史记录接口"""
    try:
        records = detection_service.get_detection_history(user_id=user_id, limit=page_size * page)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        history_items = []
        for record in records[start:end]:
            original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
            result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""
            
            history_items.append(HistoryItem(
                id=str(record.id),
                image_url=get_file_url(original_filename, "static/uploads") if original_filename else "",
                result_image_url=get_file_url(result_filename, "static/results") if result_filename else "",
                total_objects=record.total_objects or 0,
                created_at=record.created_at,
                model_name=record.model_name or "rsod-yolo11n"
            ))
        
        return HistoryResponse(
            success=True,
            message="获取成功",
            data=history_items,
            total=len(records)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, message="获取历史记录失败", detail=str(e))


@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    """获取可检测目标类别列表接口"""
    targets = [
        TargetItem(id=0, name="aircraft", chinese_name="飞机", description="固定翼飞机、直升机等"),
        TargetItem(id=1, name="oiltank", chinese_name="油罐", description="储油罐、化工罐等"),
        TargetItem(id=2, name="overpass", chinese_name="立交桥", description="各类立交桥"),
        TargetItem(id=3, name="playground", chinese_name="操场", description="运动场、操场等"),
    ]
    
    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )
```

---

## 二、前端检测界面开发

### 2.1 检测页面组件

```vue
<!-- frontend/src/views/DetectionPage.vue -->

<template>
  <div class="detection-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span>工作台</span>
        <span class="separator">›</span>
        <span class="active">智能检测</span>
      </div>
      <h1 class="page-title">上传遥感影像，立即识别多类目标</h1>
      <p class="page-subtitle">
        支持飞机 / 油罐 / 操场 / 立交桥等多目标检测
      </p>
    </div>

    <!-- 模型选择器 -->
    <div class="model-selector">
      <el-select v-model="selectedModel" style="width: 180px">
        <el-option label="rsod-yolo11n" value="rsod-yolo11n" />
      </el-select>
    </div>

    <!-- 功能选项卡 -->
    <div class="function-tabs">
      <div
        v-for="tab in functionTabs"
        :key="tab.key"
        class="function-tab"
        :class="{ active: activeTab === tab.key }"
        :data-key="tab.key"
        @click="handleTabClick(tab.key)"
      >
        <input
          type="file"
          :accept="tab.accept"
          :multiple="tab.multiple"
          class="file-input"
          @change="handleFileChange($event, tab.key)"
          @click.stop
        />
        <el-icon :size="18" class="tab-icon"><component :is="tab.icon" /></el-icon>
        <div class="tab-content">
          <span class="tab-text">{{ tab.name }}</span>
          <span class="tab-desc">{{ tab.desc }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧检测结果区域 -->
      <div class="left-panel">
        <div class="panel-header">
          <span class="panel-title">检测预览</span>
          <el-tag 
            :type="hasImage && detectionResult ? 'success' : 'info'" 
            effect="light" 
            class="result-tag"
          >
            <el-icon class="el-icon--left" v-if="hasImage && detectionResult"><Check /></el-icon>
            <el-icon class="el-icon--left" v-else><Upload /></el-icon>
            {{ hasImage && detectionResult ? '检测完成' : '等待上传' }}
          </el-tag>
        </div>

        <!-- 图片对比区域 -->
        <div class="image-compare">
          <div class="image-card">
            <template v-if="hasImage && originalImage">
              <img :src="originalImage" alt="原始图片" class="compare-image" />
            </template>
            <template v-else>
              <div class="image-placeholder">
                <el-icon class="placeholder-icon"><Upload /></el-icon>
                <p class="placeholder-text">请上传图片</p>
                <p class="placeholder-desc">支持 jpg、png 格式</p>
              </div>
            </template>
            <div class="image-label">原始图片</div>
          </div>
          <div class="image-card">
            <template v-if="hasImage && resultImage">
              <img :src="resultImage" alt="检测结果" class="compare-image" />
              <div class="detection-mark" v-if="detectionResult"></div>
            </template>
            <template v-else>
              <div class="image-placeholder">
                <el-icon class="placeholder-icon"><View /></el-icon>
                <p class="placeholder-text">检测结果将在此展示</p>
                <p class="placeholder-desc">上传图片后开始检测</p>
              </div>
            </template>
            <div class="image-label">检测结果</div>
          </div>
        </div>
      </div>

      <!-- 右侧信息面板 -->
      <div class="right-panel">
        <!-- 模型信息 -->
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">检测模型</span>
            <span class="info-value">{{ selectedModel }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">模型版本</span>
            <span class="info-value">v1.0.0</span>
          </div>
        </div>

        <!-- 识别清单 -->
        <div class="result-card">
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span class="card-title">识别清单</span>
          </div>
          <div v-if="!hasImage" class="empty-state">
            <el-icon class="empty-icon"><Upload /></el-icon>
            <p class="empty-text">请上传图片开始检测</p>
            <p class="empty-desc">上传遥感影像以识别目标</p>
          </div>
          <div v-else-if="!detectionResult || detectionResult.total_objects === 0" class="empty-state">
            <el-icon class="empty-icon"><CircleCheck /></el-icon>
            <p class="empty-text">未检测到目标</p>
            <p class="empty-desc">影像无异常目标</p>
          </div>
          <div v-else class="detection-list">
            <div
              v-for="(box, index) in detectionResult.boxes"
              :key="index"
              class="detection-item"
            >
              <span class="item-name">{{ box.chinese_name }}</span>
              <span class="item-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- AI诊断建议 -->
        <div class="result-card">
          <div class="card-header">
            <el-icon><ChatDotRound /></el-icon>
            <span class="card-title">AI 诊断建议</span>
          </div>
          <div class="diagnosis-content">
            <p v-if="!hasImage">上传图片后将自动生成诊断建议</p>
            <p v-else-if="!detectionResult">未检测到指定目标</p>
            <p v-else>
              检测到 {{ detectionResult.total_objects }} 个目标，耗时 {{ detectionResult.detection_time }}s。
              模型: {{ detectionResult.model_name }}
            </p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button size="default" class="btn-secondary" @click="handleRedetect">
            <el-icon><Refresh /></el-icon>
            重新检测
          </el-button>
          <el-button type="primary" size="default" class="btn-primary">
            查看完整报告
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import {
  Picture, Plus, Folder, Monitor, Check, Grid,
  List, CircleCheck, ChatDotRound, Refresh, Minus,
  Upload, View
} from "@element-plus/icons-vue";
import { detectSingleImage } from "../api/detection";

// 响应式状态
const selectedModel = ref("rsod-yolo11n");  // 选中的模型
const activeTab = ref("single");              // 当前激活的选项卡
const originalImage = ref(null);              // 原始图片
const resultImage = ref(null);                // 检测结果图片
const detectionResult = ref(null);            // 检测结果数据
const hasImage = ref(false);                  // 是否有图片

// 功能选项卡配置
const functionTabs = [
  { key: "single", name: "单图检测", desc: "快速识别一张图片", icon: Picture, accept: "image/*", multiple: false },
  { key: "batch", name: "批量检测", desc: "一次处理多张图片", icon: Plus, accept: "image/*", multiple: true },
  { key: "folder", name: "文件夹", desc: "上传整个文件夹", icon: Folder, accept: "image/*", multiple: true },
  { key: "video", name: "视频检测", desc: "上传视频自动分析", icon: Monitor, accept: "video/*", multiple: false },
];

// 处理选项卡点击
const handleTabClick = (key) => {
  activeTab.value = key;
  const input = document.querySelector(`.function-tab[data-key="${key}"] .file-input`);
  if (input) input.click();
};

// 处理文件选择
const handleFileChange = async (event, tabKey) => {
  const files = event.target.files;
  if (files && files.length > 0 && tabKey === "single") {
    await performSingleDetection(files[0]);
  }
  event.target.value = '';
};

// 执行单图检测
const performSingleDetection = async (file) => {
  const loading = ElLoading.service({
    lock: true,
    text: "正在检测中...",
    background: "rgba(0, 0, 0, 0.7)",
  });
  
  try {
    hasImage.value = true;
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
    
    // 显示原始图片
    originalImage.value = URL.createObjectURL(file);
    
    // 调用检测 API
    const response = await detectSingleImage(formData);
    if (response.success && response.data) {
      detectionResult.value = response.data;
      resultImage.value = response.data.result_image_url;
      ElMessage.success("检测成功！");
    } else {
      ElMessage.error(response.message || "检测失败");
    }
  } catch (error) {
    console.error("检测错误:", error);
    ElMessage.error("检测失败，请稍后重试");
  } finally {
    loading.close();
  }
};

// 重新检测
const handleRedetect = () => {
  const input = document.querySelector(`.function-tab[data-key="single"] .file-input`);
  if (input) input.click();
};
</script>

<style scoped>
.detection-page {
  width: 100%;
  position: relative;
}

.page-header { margin-bottom: 32px; }

.breadcrumb {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.model-selector {
  position: absolute;
  top: 0;
  right: 0;
}

/* 功能选项卡 */
.function-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.function-tab {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.function-tab:hover { background-color: var(--primary-light); }
.function-tab.active {
  background-color: var(--primary-light);
  border-color: var(--primary-color);
}

.tab-icon {
  font-size: 18px;
  color: var(--primary-color);
  margin-right: 12px;
}

.tab-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.tab-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 主内容区域 */
.main-content {
  display: flex;
  gap: 24px;
}

.left-panel {
  flex: 1;
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.result-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
}

/* 图片对比区域 */
.image-compare {
  display: flex;
  gap: 16px;
  height: 320px;
}

.image-card {
  flex: 1;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9fafb;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
  text-align: center;
}

.placeholder-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.placeholder-desc {
  font-size: 12px;
  color: #9ca3af;
}

.compare-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 13px;
}

/* 右侧面板 */
.right-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card, .result-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child { border-bottom: none; }

.info-label { font-size: 13px; color: var(--text-secondary); }
.info-value { font-size: 13px; font-weight: 500; color: var(--text-primary); }

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.card-header .el-icon {
  font-size: 16px;
  color: var(--primary-color);
  margin-right: 8px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
}

.empty-icon {
  font-size: 48px;
  color: var(--success-color);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.detection-list {
  max-height: 200px;
  overflow-y: auto;
}

.detection-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  margin-bottom: 8px;
}

.item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.item-confidence {
  font-size: 12px;
  color: var(--primary-color);
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-secondary, .btn-primary {
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
}

.btn-secondary { flex: 1; }
.btn-primary { flex: 2; }
</style>
```

### 2.2 API 请求封装

```javascript
// frontend/src/api/detection.js

/**
 * 检测相关 API 封装
 */

import request from '../utils/request';

/**
 * 单图检测
 * @param {FormData} formData - 包含 file 和 model_name
 * @returns {Promise} - 检测结果
 */
export const detectSingleImage = async (formData) => {
  return request({
    url: '/api/detection/single',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/**
 * 获取检测历史记录
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页大小
 * @param {string} params.userId - 用户 ID（可选）
 * @returns {Promise} - 历史记录列表
 */
export const getDetectionHistory = async (params = {}) => {
  return request({
    url: '/api/detection/history',
    method: 'GET',
    params,
  });
};

/**
 * 获取单个检测记录
 * @param {string} id - 检测记录 ID
 * @returns {Promise} - 检测记录详情
 */
export const getDetectionById = async (id) => {
  return request({
    url: `/api/detection/${id}`,
    method: 'GET',
  });
};

/**
 * 获取可检测目标列表
 * @returns {Promise} - 目标类别列表
 */
export const getTargetList = async () => {
  return request({
    url: '/api/detection/targets/list',
    method: 'GET',
  });
};
```

---

## 三、历史记录页面开发

### 3.1 历史记录页面组件

```vue
<!-- frontend/src/views/HistoryPage.vue -->

<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span>工作台</span>
        <span class="separator">›</span>
        <span class="active">历史记录</span>
      </div>
      <h1 class="page-title">检测历史记录</h1>
      <p class="page-subtitle">查看您的所有检测记录</p>
    </div>

    <!-- 统计信息 -->
    <div class="stats-row">
      <div class="stat-card">
        <el-icon class="stat-icon"><History /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ totalCount }}</span>
          <span class="stat-label">总检测次数</span>
        </div>
      </div>
      <div class="stat-card">
        <el-icon class="stat-icon"><Target /></el-icon>
        <div class="stat-content">
          <span class="stat-value">{{ totalTargets }}</span>
          <span class="stat-label">检测目标总数</span>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索检测记录..."
        class="search-input"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-icon class="el-input__icon" @click="handleSearch"><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list">
      <div v-if="records.length === 0" class="empty-state">
        <el-icon class="empty-icon"><FolderOpen /></el-icon>
        <p class="empty-text">暂无检测记录</p>
        <p class="empty-desc">上传图片进行检测后，记录将显示在这里</p>
        <el-button type="primary" @click="goToDetection">去检测</el-button>
      </div>

      <div v-else class="records-grid">
        <div
          v-for="record in records"
          :key="record.id"
          class="record-card"
          @click="viewRecord(record.id)"
        >
          <div class="card-image">
            <img :src="record.result_image_url" alt="检测结果" />
            <div class="target-count">
              <el-icon><Target /></el-icon>
              <span>{{ record.total_objects }}</span>
            </div>
          </div>
          <div class="card-info">
            <div class="card-header">
              <span class="model-name">{{ record.model_name }}</span>
              <span class="record-time">{{ formatTime(record.created_at) }}</span>
            </div>
            <div class="card-stats">
              <span class="stat-item">
                <el-icon><Eye /></el-icon>
                检测到 {{ record.total_objects }} 个目标
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="records.length > 0" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="totalCount"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import {
  History, Target, Search, FolderOpen, Eye
} from "@element-plus/icons-vue";
import { getDetectionHistory } from "../api/detection";

const router = useRouter();

// 响应式状态
const records = ref([]);
const currentPage = ref(1);
const pageSize = ref(6);
const totalCount = ref(0);
const searchKeyword = ref("");

// 计算属性：统计检测到的目标总数
const totalTargets = computed(() => {
  return records.value.reduce((sum, record) => sum + (record.total_objects || 0), 0);
});

// 格式化时间
const formatTime = (dateStr) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  
  // 计算时间差
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  
  return date.toLocaleDateString("zh-CN");
};

// 获取历史记录
const fetchHistory = async () => {
  try {
    const response = await getDetectionHistory({
      page: currentPage.value,
      pageSize: pageSize.value,
    });
    
    if (response.success) {
      records.value = response.data;
      totalCount.value = response.total;
    }
  } catch (error) {
    console.error("获取历史记录失败:", error);
  }
};

// 搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchHistory();
};

// 分页
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchHistory();
};

// 查看记录详情
const viewRecord = (id) => {
  // 跳转到检测页面并显示详情
  router.push({ path: "/detection", query: { recordId: id } });
};

// 跳转到检测页面
const goToDetection = () => {
  router.push("/detection");
};

// 页面挂载时获取历史记录
onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.history-page { width: 100%; }

.page-header { margin-bottom: 24px; }

.breadcrumb {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle { font-size: 14px; color: var(--text-secondary); }

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: #fff;
  border-radius: 12px;
}

.stat-icon {
  font-size: 32px;
  color: var(--primary-color);
  margin-right: 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 搜索栏 */
.search-bar {
  margin-bottom: 24px;
}

.search-input {
  width: 400px;
}

/* 历史记录列表 */
.history-list {
  min-height: 300px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.empty-icon {
  font-size: 64px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

/* 记录卡片网格 */
.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.record-card {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.record-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-image {
  position: relative;
  height: 180px;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.target-count {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  color: #fff;
  font-size: 12px;
}

.target-count .el-icon {
  margin-right: 4px;
}

.card-info {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.record-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-item .el-icon {
  margin-right: 4px;
  font-size: 14px;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
```

---

## 四、启动服务测试

### 4.1 启动后端服务

```bash
# 进入后端目录
cd /Users/lily/Desktop/rsod-web-platform/backend

# 激活虚拟环境
source .venv/bin/activate

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 
或
python main.py
```

### 4.2 启动前端服务

```bash
# 进入前端目录
cd /Users/lily/Desktop/rsod-web-platform/frontend

# 启动前端服务
npm run dev
```

### 4.3 测试检测接口

使用 curl 测试单图检测接口：

```bash
# 测试单图检测
curl -X POST http://localhost:8000/api/detection/single \
  -F "file=@/path/to/your/image.jpg" \
  -F "model_name=rsod-yolo11n"

# 测试获取历史记录
curl http://localhost:8000/api/detection/history

# 测试获取目标列表
curl http://localhost:8000/api/detection/targets/list
```

---

## 五、今日任务检查清单

- [ ] 图片上传API开发 ✅
- [ ] YOLO推理服务集成 ✅
- [ ] 检测结果返回格式定义 ✅
- [ ] 前端检测界面开发 ✅
- [ ] 历史记录列表展示 ✅

---

## 📚 学习要点总结

1. **检测服务设计**：封装 YOLO 模型为独立服务类，提供统一接口
2. **API 设计规范**：遵循 RESTful 风格，使用 Pydantic 模型定义请求/响应格式
3. **数据持久化**：检测记录自动保存到 PostgreSQL 数据库
4. **前端状态管理**：使用 Vue 3 Composition API 管理组件状态
5. **响应式布局**：使用 Flexbox 和 Grid 实现灵活的页面布局
6. **用户体验优化**：空状态友好提示、加载动画、错误处理
