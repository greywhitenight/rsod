<template>
  <div class="batch-detection">
    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{ 'is-dragover': isDragover, 'has-files': fileList.length > 0 }"
      @dragenter.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <input
        type="file"
        ref="fileInput"
        multiple
        accept="image/*"
        class="file-input"
        @change="handleFileSelect"
      />
      
      <div v-if="fileList.length === 0" class="upload-placeholder">
        <el-icon class="upload-icon"><Upload /></el-icon>
        <h3 class="upload-title">拖拽图片到此处或点击上传</h3>
        <p class="upload-desc">支持 jpg、png、jpeg 格式，最多可同时上传 20 张图片</p>
        <el-button type="primary" size="large" @click="triggerFileInput">
          <el-icon><Plus /></el-icon>
          选择图片
        </el-button>
      </div>

      <div v-else class="file-list">
        <div class="file-list-header">
          <span class="file-count">已选择 {{ fileList.length }} 张图片</span>
          <el-button link type="primary" @click="clearAll">
            <el-icon><Delete /></el-icon>
            清空全部
          </el-button>
        </div>
        
        <div class="file-grid">
          <div
            v-for="(file, index) in fileList"
            :key="index"
            class="file-item"
            :class="{ 'is-detecting': isDetecting, 'is-detected': file.status === 'completed' }"
          >
            <div class="file-preview">
              <img :src="file.preview" :alt="file.name" />
              <div v-if="file.status === 'detecting'" class="file-overlay">
                <el-icon class="loading-icon"><Loading /></el-icon>
              </div>
              <div v-else-if="file.status === 'completed'" class="file-overlay success">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div v-else-if="file.status === 'failed'" class="file-overlay error">
                <el-icon><CircleClose /></el-icon>
              </div>
            </div>
            <div class="file-info">
              <span class="file-name" :title="file.name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <div class="file-actions">
              <el-button
                v-if="file.result"
                link
                type="primary"
                size="small"
                @click="viewResult(file)"
              >
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button link type="danger" size="small" @click="removeFile(index)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="fileList.length > 0" class="batch-stats">
      <div class="stat-item">
        <span class="stat-label">总图片数</span>
        <span class="stat-value">{{ fileList.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">待检测</span>
        <span class="stat-value pending">{{ pendingCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已完成</span>
        <span class="stat-value success">{{ completedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">失败</span>
        <span class="stat-value error">{{ failedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">检测目标总数</span>
        <span class="stat-value primary">{{ totalObjects }}</span>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div v-if="fileList.length > 0" class="batch-actions">
      <el-button size="large" @click="$emit('back-to-single')">
        <el-icon><ArrowLeft /></el-icon>
        返回单图检测
      </el-button>
      <el-button
        type="primary"
        size="large"
        :loading="isDetecting"
        :disabled="pendingCount === 0"
        @click="startBatchDetection"
      >
        <el-icon><Picture /></el-icon>
        {{ isDetecting ? '检测中...' : `开始检测 (${pendingCount}张)` }}
      </el-button>
    </div>

    <!-- 批量检测结果 -->
    <div v-if="batchResults.length > 0" class="batch-results">
      <div class="results-header">
        <h3 class="results-title">批量检测结果</h3>
        <el-button type="success" size="small" @click="downloadAllResults">
          <el-icon><Download /></el-icon>
          下载全部结果
        </el-button>
      </div>
      
      <el-table :data="batchResults" border stripe>
        <el-table-column prop="filename" label="文件名" min-width="150">
          <template #default="{ row }">
            <div class="result-filename">
              <el-icon v-if="row.status === 'completed'" class="status-icon success"><CircleCheck /></el-icon>
              <el-icon v-else class="status-icon error"><CircleClose /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_objects" label="检测目标" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.total_objects > 0" type="success">{{ row.total_objects }} 个</el-tag>
            <el-tag v-else type="info">0 个</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_time" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.detection_time ? row.detection_time.toFixed(2) + 's' : '--' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              link
              type="primary"
              size="small"
              @click="viewResultDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 结果详情弹窗 -->
    <el-dialog
      v-model="showResultModal"
      title="检测详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedResult" class="result-detail">
        <div class="detail-images">
          <div class="image-section">
            <h4 class="section-title">原始图片</h4>
            <img :src="selectedResult.image_url" alt="原始图片" class="detail-image" />
          </div>
          <div class="image-section">
            <h4 class="section-title">检测结果</h4>
            <img :src="selectedResult.result_image_url" alt="检测结果" class="detail-image" />
          </div>
        </div>
        
        <div class="detail-info">
          <div class="info-row">
            <span class="info-label">文件名</span>
            <span class="info-value">{{ selectedResult.filename }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测目标数</span>
            <span class="info-value">{{ selectedResult.total_objects }} 个</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测耗时</span>
            <span class="info-value">{{ selectedResult.detection_time ? selectedResult.detection_time.toFixed(2) + ' 秒' : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测模型</span>
            <span class="info-value">{{ selectedResult.model_name }}</span>
          </div>
        </div>

        <div v-if="selectedResult.boxes && selectedResult.boxes.length > 0" class="detail-boxes">
          <h4 class="section-title">检测目标详情</h4>
          <el-table :data="selectedResult.boxes" border size="small">
            <el-table-column prop="class_name" label="目标类别" />
            <el-table-column prop="chinese_name" label="中文名称" />
            <el-table-column prop="confidence" label="置信度">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import {
  Upload,
  Plus,
  Delete,
  Loading,
  CircleCheck,
  CircleClose,
  View,
  ArrowLeft,
  Download,
  Picture,
} from "@element-plus/icons-vue";
import { detectBatchImages } from "../api/detection";

const props = defineProps({
  selectedModel: {
    type: String,
    default: "rsod-yolo11n",
  },
});

const emit = defineEmits(["back-to-single"]);

// 响应式状态
const fileInput = ref(null);
const isDragover = ref(false);
const isDetecting = ref(false);
const fileList = ref([]);
const batchResults = ref([]);
const showResultModal = ref(false);
const selectedResult = ref(null);

// 统计计算
const pendingCount = computed(() => fileList.value.filter(f => f.status === 'pending').length);
const completedCount = computed(() => fileList.value.filter(f => f.status === 'completed').length);
const failedCount = computed(() => fileList.value.filter(f => f.status === 'failed').length);
const totalObjects = computed(() => {
  return fileList.value.reduce((sum, file) => sum + (file.result?.total_objects || 0), 0);
});

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click();
};

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files);
  addFiles(files);
  event.target.value = "";
};

// 处理拖拽
const handleDrop = (event) => {
  isDragover.value = false;
  const files = Array.from(event.dataTransfer.files).filter(file => file.type.startsWith('image/'));
  addFiles(files);
};

// 添加文件
const addFiles = (files) => {
  const remainingSlots = 20 - fileList.value.length;
  if (remainingSlots <= 0) {
    ElMessage.warning("最多只能上传 20 张图片");
    return;
  }

  const filesToAdd = files.slice(0, remainingSlots);
  
  filesToAdd.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      fileList.value.push({
        file: file,
        name: file.name,
        size: file.size,
        preview: e.target.result,
        status: 'pending',
        result: null,
      });
    };
    reader.readAsDataURL(file);
  });

  if (files.length > remainingSlots) {
    ElMessage.warning(`已添加 ${filesToAdd.length} 张图片，超出部分被忽略`);
  }
};

// 移除文件
const removeFile = (index) => {
  fileList.value.splice(index, 1);
};

// 清空全部
const clearAll = () => {
  fileList.value = [];
  batchResults.value = [];
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 开始批量检测
const startBatchDetection = async () => {
  console.log("==============================");
  console.log("批量检测按钮已点击！");
  console.log("==============================");
  
  ElMessage.info("开始批量检测，请稍候...");
  
  if (fileList.value.length === 0) {
    ElMessage.warning("请先上传图片");
    return;
  }

  const pendingFiles = fileList.value.filter(f => f.status === 'pending');
  if (pendingFiles.length === 0) {
    ElMessage.info("所有图片已检测完成");
    return;
  }

  isDetecting.value = true;
  const loading = ElLoading.service({
    lock: true,
    text: `正在批量检测中 (0/${pendingFiles.length})...`,
    background: "rgba(0, 0, 0, 0.7)",
  });

  try {
    const formData = new FormData();
    pendingFiles.forEach(fileItem => {
      formData.append("files", fileItem.file);
    });
    formData.append("model_name", props.selectedModel);

    console.log("=== 批量检测请求信息 ===");
    console.log("请求URL:", "/api/detection/batch");
    console.log("待检测文件数量:", pendingFiles.length);
    console.log("模型名称:", props.selectedModel);
    console.log("FormData files数量:", formData.getAll("files").length);
    console.log("FormData model_name:", formData.get("model_name"));

    const response = await detectBatchImages(formData);
    
    console.log("=== 批量检测响应 ===");
    console.log("响应数据:", response);
    
    if (response.success && response.data) {
      const results = response.data.results;
      
      // 更新文件状态
      results.forEach((result, index) => {
        const fileItem = pendingFiles[index];
        if (fileItem) {
          fileItem.status = result.status;
          fileItem.result = result;
        }
      });

      // 更新批量结果
      batchResults.value = results;

      ElMessage.success(`批量检测完成！成功 ${response.data.completed} 张，失败 ${response.data.failed} 张`);
    } else {
      ElMessage.error(response.message || "批量检测失败");
    }
  } catch (error) {
    console.error("=== 批量检测错误 ===");
    console.error("错误类型:", error.name);
    console.error("错误消息:", error.message);
    console.error("错误详情:", error);
    if (error.response) {
      console.error("响应状态:", error.response.status);
      console.error("响应数据:", error.response.data);
    }
    if (error.request) {
      console.error("请求对象:", error.request);
    }
    ElMessage.error("批量检测失败，请稍后重试");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

// 查看结果
const viewResult = (file) => {
  if (file.result) {
    selectedResult.value = file.result;
    showResultModal.value = true;
  }
};

// 查看结果详情
const viewResultDetail = (row) => {
  selectedResult.value = row;
  showResultModal.value = true;
};

// 下载全部结果
const downloadAllResults = () => {
  const completedResults = batchResults.value.filter(r => r.status === 'completed');
  if (completedResults.length === 0) {
    ElMessage.warning("没有可下载的检测结果");
    return;
  }

  completedResults.forEach(result => {
    if (result.result_image_url) {
      const link = document.createElement("a");
      link.href = result.result_image_url;
      link.download = `result_${result.filename}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  });

  ElMessage.success("开始下载检测结果");
};
</script>

<style scoped lang="scss">
.batch-detection {
  width: 100%;
}

// 上传区域
.upload-area {
  background-color: #ffffff;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
  padding: 40px;
  text-align: center;
  transition: all 0.3s;
  position: relative;

  &.is-dragover {
    border-color: var(--primary-color);
    background-color: var(--primary-light);
  }

  &.has-files {
    padding: 24px;
    text-align: left;
  }
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0;
  cursor: pointer;
}

.upload-placeholder {
  .upload-icon {
    font-size: 64px;
    color: #d1d5db;
    margin-bottom: 16px;
  }

  .upload-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .upload-desc {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 24px;
  }
}

// 文件列表
.file-list {
  .file-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);

    .file-count {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.file-item {
  background-color: #f9fafb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  &.is-detected {
    border: 2px solid #22c55e;
  }

  .file-preview {
    position: relative;
    width: 100%;
    height: 120px;
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .file-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.5);
      color: white;
      font-size: 32px;

      &.success {
        background: rgba(34, 197, 94, 0.8);
      }

      &.error {
        background: rgba(239, 68, 68, 0.8);
      }

      .loading-icon {
        animation: rotate 1s linear infinite;
      }
    }
  }

  .file-info {
    padding: 8px 12px;

    .file-name {
      display: block;
      font-size: 12px;
      color: var(--text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .file-size {
      font-size: 11px;
      color: var(--text-secondary);
    }
  }

  .file-actions {
    display: flex;
    justify-content: center;
    gap: 8px;
    padding: 0 8px 8px;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 统计信息
.batch-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 24px;
  padding: 16px;
  background-color: #ffffff;
  border-radius: 12px;

  .stat-item {
    text-align: center;

    .stat-label {
      display: block;
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 4px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);

      &.pending {
        color: #f59e0b;
      }

      &.success {
        color: #22c55e;
      }

      &.error {
        color: #ef4444;
      }

      &.primary {
        color: var(--primary-color);
      }
    }
  }
}

// 操作按钮
.batch-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

// 批量结果
.batch-results {
  margin-top: 32px;
  background-color: #ffffff;
  border-radius: 12px;
  padding: 24px;

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .results-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

.result-filename {
  display: flex;
  align-items: center;
  gap: 8px;

  .status-icon {
    font-size: 16px;

    &.success {
      color: #22c55e;
    }

    &.error {
      color: #ef4444;
    }
  }
}

// 结果详情
.result-detail {
  .detail-images {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;

    .image-section {
      .section-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 8px;
      }

      .detail-image {
        width: 100%;
        max-height: 300px;
        object-fit: contain;
        border-radius: 8px;
        background: #f9fafb;
      }
    }
  }

  .detail-info {
    background: #f9fafb;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 24px;

    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #e5e7eb;

      &:last-child {
        border-bottom: none;
      }

      .info-label {
        font-size: 13px;
        color: var(--text-secondary);
      }

      .info-value {
        font-size: 13px;
        color: var(--text-primary);
        font-weight: 500;
      }
    }
  }

  .detail-boxes {
    .section-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 12px;
    }
  }
}
</style>
