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
        支持飞机 / 油罐 / 操场 / 建筑物 / 船舶 / 农业虫害等多目标检测
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
          ref="fileInputs"
        />
        <el-icon :size="18" class="tab-icon"
          ><component :is="tab.icon"
        /></el-icon>
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
            <el-icon class="el-icon--left" v-if="hasImage && detectionResult"
              ><Check
            /></el-icon>
            <el-icon class="el-icon--left" v-else><Upload /></el-icon>
            {{ hasImage && detectionResult ? "检测完成" : "等待上传" }}
          </el-tag>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button
            :class="{ active: compareMode === 'side' }"
            size="small"
            @click="compareMode = 'side'"
          >
            <el-icon><Minus /></el-icon>
            并排对比
          </el-button>
          <el-button
            :class="{ active: compareMode === 'grid' }"
            size="small"
            @click="compareMode = 'grid'"
          >
            <el-icon><Grid /></el-icon>
            栅格对比
          </el-button>
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
          <div
            v-else-if="!detectionResult || detectionResult.total_objects === 0"
            class="empty-state"
          >
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
              <span class="item-name">{{ box.class_name }}</span>
              <span class="item-confidence"
                >{{ (box.confidence * 100).toFixed(1) }}%</span
              >
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
              检测到 {{ detectionResult.total_objects }} 个目标，耗时
              {{ detectionResult.detection_time }}s。 模型:
              {{ detectionResult.model_name }}
            </p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            size="default"
            class="btn-secondary"
            @click="handleRedetect"
          >
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
  Picture,
  Plus,
  Folder,
  Monitor,
  Check,
  Grid,
  List,
  CircleCheck,
  ChatDotRound,
  Refresh,
  Minus,
  Upload,
  View,
} from "@element-plus/icons-vue";
import { detectSingleImage } from "../api/detection";

const selectedModel = ref("rsod-yolo11n");
const activeTab = ref("single");
const compareMode = ref("side");
const originalImage = ref(null);
const resultImage = ref(null);
const detectionResult = ref(null);
const isDetecting = ref(false);
const hasImage = ref(false);

const functionTabs = [
  {
    key: "single",
    name: "单图检测",
    desc: "快速识别一张图片",
    icon: Picture,
    accept: "image/*",
    multiple: false,
  },
  {
    key: "batch",
    name: "批量检测",
    desc: "一次处理多张图片",
    icon: Plus,
    accept: "image/*",
    multiple: true,
  },
  {
    key: "ciname",
    name: "摄像头",
    desc: "打开摄像头",
    icon: Folder,
    accept: "image/*",
    multiple: true,
  },
  {
    key: "video",
    name: "视频检测",
    desc: "上传视频自动分析",
    icon: Monitor,
    accept: "video/*",
    multiple: false,
  },
];

const fileInputs = ref([]);

const handleTabClick = (key) => {
  activeTab.value = key;
  const input = document.querySelector(
    `.function-tab[data-key="${key}"] .file-input`, //.function-tab data-key="single" .file-inputsingle
  );
  if (input) {
    input.click();
  }
};

const handleFileChange = async (event, tabKey) => {
  event.stopPropagation();
  event.preventDefault();
  const files = event.target.files;
  if (files && files.length > 0) {
    if (tabKey === "single") {
      await performSingleDetection(files[0]);
    }
  }
  setTimeout(() => {
    event.target.value = "";
  }, 0);
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({
    lock: true,
    text: "正在检测中...",
    background: "rgba(0, 0, 0, 0.7)",
  });

  try {
    isDetecting.value = true;
    hasImage.value = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);

    originalImage.value = URL.createObjectURL(file);

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
    isDetecting.value = false;
    loading.close();
  }
};

const handleRedetect = () => {
  const input = document.querySelector(
    `.function-tab[data-key="single"] .file-input`,
  );
  if (input) {
    input.click();
  }
};
</script>

<style scoped>
.detection-page {
  width: 100%;
  position: relative;
}

.page-header {
  margin-bottom: 32px;
  padding-top: 0;
}

.breadcrumb {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.separator {
  margin: 0 6px;
}

.active {
  color: var(--text-primary);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.model-selector {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
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
  background-color: #ffffff;
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

.function-tab:hover {
  background-color: var(--primary-light);
}

.function-tab.active {
  background-color: var(--primary-light);
  border-color: var(--primary-color);
}

.tab-icon {
  font-size: 18px;
  color: var(--primary-color);
  margin-right: 12px;
  flex-shrink: 0;
}

.tab-content {
  display: flex;
  flex-direction: column;
}

.tab-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.tab-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* 主内容区域 */
.main-content {
  display: flex;
  gap: 24px;
}

.left-panel {
  flex: 1;
  background-color: #ffffff;
  border-radius: 12px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.toolbar .el-button {
  border-radius: 6px;
  padding: 6px 14px;
}

.toolbar .el-button.active {
  background-color: var(--primary-light);
  color: var(--primary-color);
  border-color: var(--primary-color);
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
  width: 100%;
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
  color: #ffffff;
  font-size: 13px;
}

.detection-mark {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detection-mark::after {
  content: "✓";
  color: #ffffff;
  font-size: 18px;
  font-weight: bold;
}

/* 右侧面板 */
.right-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.result-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
}

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

.diagnosis-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
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

.detection-item:last-child {
  margin-bottom: 0;
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

.btn-secondary {
  flex: 1;
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
}

.btn-primary {
  flex: 2;
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
}
</style>
