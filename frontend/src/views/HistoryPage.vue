<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">检测历史记录</h1>
      <p class="page-subtitle">查看和管理您的所有检测记录</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名..."
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="filterStatus"
        placeholder="状态筛选"
        size="default"
        class="filter-select"
      >
        <el-option label="全部" value="" />
        <el-option label="检测完成" value="completed" />
        <el-option label="检测中" value="processing" />
        <el-option label="失败" value="failed" />
      </el-select>

      <el-select
        v-model="filterType"
        placeholder="类型筛选"
        size="default"
        class="filter-select"
      >
        <el-option label="全部" value="" />
        <el-option label="单图检测" value="single" />
        <el-option label="批量检测" value="batch" />
        <el-option label="文件夹" value="folder" />
        <el-option label="视频检测" value="video" />
      </el-select>
    </div>

    <!-- 统计信息 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon completed">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ completedCount }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon processing">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ processingCount }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon failed">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ failedCount }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon><DataLine /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ totalRecords }}</div>
          <div class="stat-label">总记录</div>
        </div>
      </div>
    </div>

    <!-- 记录列表 -->
    <div class="history-list" v-loading="isLoading">
      <div
        v-for="record in filteredRecords"
        :key="record.id"
        class="history-card"
        @click="viewRecordDetail(record)"
      >
        <div class="record-preview">
          <img
            :src="record.result_image_url || record.image_url"
            :alt="record.filename"
            class="preview-image"
            :loading="lazy"
          />
          <div
            class="status-badge"
            :class="record.status"
          >
            <el-icon><component :is="getStatusIcon(record.status)" /></el-icon>
            {{ getStatusText(record.status) }}
          </div>
        </div>

        <div class="record-info">
          <div class="record-header">
            <span class="record-filename">{{ record.filename }}</span>
            <span class="record-type">{{ getTypeText(record.type) }}</span>
          </div>
          <div class="record-meta">
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ formatDate(record.created_at) }}
            </span>
            <span class="meta-item">
              <el-icon><Picture /></el-icon>
              {{ record.count || 1 }} 张
            </span>
            <span class="meta-item">
              <el-icon><Target /></el-icon>
              {{ record.total_objects }} 个目标
            </span>
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ record.detection_time ? record.detection_time.toFixed(2) + 's' : '--' }}
            </span>
          </div>
          <div class="record-tags">
            <span
              v-for="(tag, index) in record.detected_targets.slice(0, 5)"
              :key="index"
              class="detected-tag"
            >
              {{ tag }}
            </span>
            <span
              v-if="record.detected_targets && record.detected_targets.length > 5"
              class="detected-tag more"
            >
              +{{ record.detected_targets.length - 5 }}
            </span>
          </div>
        </div>

        <div class="record-actions">
          <el-button size="small" @click.stop="viewRecordDetail(record)" type="primary">
            <el-icon><Monitor/></el-icon>
            详情
          </el-button>
          <el-button size="small" @click.stop="downloadRecord(record)">
            <el-icon><Download/></el-icon>
            下载
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click.stop="confirmDelete(record)"
          >
            <el-icon><Delete/></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!isLoading && filteredRecords.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Help /></el-icon>
      <p class="empty-text">暂无检测记录</p>
      <el-button type="primary" @click="goToDetection">
        <el-icon><Plus /></el-icon>
        开始检测
      </el-button>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-if="totalRecords > 0"
        :total="totalRecords"
        :page-size="pageSize"
        :current-page="currentPage"
        :disabled="isLoading"
        @current-change="handlePageChange"
        layout="total, prev, pager, next, jumper"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="showDetailModal"
      title="检测详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRecord" class="detail-content">
        <div class="detail-images">
          <div class="image-section">
            <h4 class="section-title">原始图片</h4>
            <img
              :src="selectedRecord.image_url"
              alt="原始图片"
              class="detail-image"
            />
          </div>
          <div class="image-section">
            <h4 class="section-title">检测结果</h4>
            <img
              :src="selectedRecord.result_image_url"
              alt="检测结果"
              class="detail-image"
            />
          </div>
        </div>

        <div class="detail-info">
          <div class="info-row">
            <span class="info-label">文件名</span>
            <span class="info-value">{{ selectedRecord.filename }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测类型</span>
            <span class="info-value">{{ getTypeText(selectedRecord.type) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测时间</span>
            <span class="info-value">{{ formatDate(selectedRecord.created_at) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测耗时</span>
            <span class="info-value">{{ selectedRecord.detection_time ? selectedRecord.detection_time.toFixed(2) + ' 秒' : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">使用模型</span>
            <span class="info-value">{{ selectedRecord.model_name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">检测目标数</span>
            <span class="info-value">{{ selectedRecord.total_objects }} 个</span>
          </div>
        </div>

        <div v-if="selectedRecord.boxes && selectedRecord.boxes.length > 0" class="detail-boxes">
          <h4 class="section-title">检测目标详情</h4>
          <el-table :data="selectedRecord.boxes" border size="small">
            <el-table-column prop="class_name" label="目标类别" />
            <el-table-column prop="chinese_name" label="中文名称" />
            <el-table-column prop="confidence" label="置信度" formatter="formatConfidence" />
            <el-table-column prop="x1" label="X1" />
            <el-table-column prop="y1" label="Y1" />
            <el-table-column prop="x2" label="X2" />
            <el-table-column prop="y2" label="Y2" />
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 删除确认弹窗 -->
    <el-dialog
      v-model="showDeleteModal"
      title="确认删除"
      width="400px"
      :close-on-click-modal="false"
    >
      <p>确定要删除检测记录 <strong>"{{ deletingRecord?.filename }}"</strong> 吗？</p>
      <p class="delete-warning">此操作不可恢复，相关的检测结果图片也将被删除。</p>
      <template #footer>
        <el-button @click="showDeleteModal = false">取消</el-button>
        <el-button type="danger" @click="doDelete" :loading="isDeleting">
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  Search,
  Clock,
  Picture,
  Monitor,
  Download,
  Delete,
  Plus,
  Help,
  CircleCheck,
  Loading,
  CircleClose,
  DataLine,
  User,
  Message,
  Lock,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import {
  getDetectionHistory,
  getDetectionDetail,
  deleteDetectionRecord,
} from "../api/detection";

const router = useRouter();

// 响应式状态
const searchQuery = ref("");
const filterStatus = ref("");
const filterType = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const isLoading = ref(false);
const isDeleting = ref(false);

const historyRecords = ref([]);
const totalRecords = ref(0);

const showDetailModal = ref(false);
const showDeleteModal = ref(false);
const selectedRecord = ref(null);
const deletingRecord = ref(null);

// 统计数据
const completedCount = computed(() =>
  historyRecords.value.filter((r) => r.status === "completed").length
);
const processingCount = computed(() =>
  historyRecords.value.filter((r) => r.status === "processing").length
);
const failedCount = computed(() =>
  historyRecords.value.filter((r) => r.status === "failed").length
);

// 筛选后的记录
const filteredRecords = computed(() => {
  return historyRecords.value.filter((record) => {
    const matchesSearch =
      !searchQuery.value ||
      record.filename.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesStatus = !filterStatus.value || record.status === filterStatus.value;
    const matchesType = !filterType.value || record.type === filterType.value;
    return matchesSearch && matchesStatus && matchesType;
  });
});

// 获取历史记录
const fetchHistory = async () => {
  isLoading.value = true;
  try {
    const response = await getDetectionHistory({
      page: currentPage.value,
      page_size: pageSize.value,
    });
    if (response.success && response.data) {
      historyRecords.value = response.data;
      totalRecords.value = response.total;
    }
  } catch (error) {
    console.error("获取历史记录失败:", error);
    ElMessage.error("获取历史记录失败，请稍后重试");
    historyRecords.value = [];
    totalRecords.value = 0;
  } finally {
    isLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchHistory();
});

// 状态图标映射
const getStatusIcon = (status) => {
  const icons = {
    completed: CircleCheck,
    processing: Loading,
    failed: CircleClose,
  };
  return icons[status] || CircleCheck;
};

// 状态文本映射
const getStatusText = (status) => {
  const texts = {
    completed: "检测完成",
    processing: "检测中",
    failed: "失败",
  };
  return texts[status] || status;
};

// 类型文本映射
const getTypeText = (type) => {
  const texts = {
    single: "单图检测",
    batch: "批量检测",
    folder: "文件夹",
    video: "视频检测",
  };
  return texts[type] || type;
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return "--";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 格式化置信度
const formatConfidence = (row) => {
  return (row.confidence * 100).toFixed(1) + "%";
};

// 查看详情
const viewRecordDetail = async (record) => {
  try {
    const response = await getDetectionDetail(record.id);
    if (response.success && response.data) {
      selectedRecord.value = response.data;
      showDetailModal.value = true;
    } else {
      ElMessage.error("获取检测详情失败");
    }
  } catch (error) {
    console.error("获取检测详情失败:", error);
    ElMessage.error("获取检测详情失败，请稍后重试");
  }
};

// 下载记录
const downloadRecord = (record) => {
  if (record.result_image_url) {
    const link = document.createElement("a");
    link.href = record.result_image_url;
    link.download = `result_${record.filename}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    ElMessage.success("下载开始");
  } else {
    ElMessage.warning("暂无可下载的结果文件");
  }
};

// 确认删除
const confirmDelete = (record) => {
  deletingRecord.value = record;
  showDeleteModal.value = true;
};

// 执行删除
const doDelete = async () => {
  if (!deletingRecord.value) return;

  isDeleting.value = true;
  try {
    const response = await deleteDetectionRecord(deletingRecord.value.id);
    if (response.success) {
      ElMessage.success("删除成功");
      // 从列表中移除
      const index = historyRecords.value.findIndex(
        (r) => r.id === deletingRecord.value.id
      );
      if (index > -1) {
        historyRecords.value.splice(index, 1);
        totalRecords.value--;
      }
    } else {
      ElMessage.error(response.message || "删除失败");
    }
  } catch (error) {
    console.error("删除失败:", error);
    ElMessage.error("删除失败，请稍后重试");
  } finally {
    isDeleting.value = false;
    showDeleteModal.value = false;
    deletingRecord.value = null;
  }
};

// 跳转到检测页面
const goToDetection = () => {
  router.push("/detection");
};

// 分页变化
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchHistory();
};
</script>

<style scoped lang="scss">
.history-page {
  width: 100%;
  padding: 24px;
  box-sizing: border-box;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .search-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    align-items: center;

    .search-input {
      flex: 1;
      max-width: 300px;
    }

    .filter-select {
      width: 140px;
    }
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 12px;
      background: #fff;
      padding: 16px;
      border-radius: 12px;
      box-shadow: var(--card-shadow);

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;

        &.completed {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }
        &.processing {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }
        &.failed {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }
        &.total {
          background: rgba(168, 85, 247, 0.1);
          color: #a855f7;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
        }
        .stat-label {
          font-size: 13px;
          color: var(--text-secondary);
        }
      }
    }
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 300px;
  }

  .history-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: var(--card-shadow);
    display: flex;
    align-items: center;
    gap: 20px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }

    .record-preview {
      position: relative;
      width: 120px;
      height: 80px;
      border-radius: 8px;
      overflow: hidden;
      flex-shrink: 0;

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .status-badge {
        position: absolute;
        bottom: 8px;
        left: 8px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
        backdrop-filter: blur(4px);

        &.completed {
          background-color: rgba(34, 197, 94, 0.9);
          color: white;
        }

        &.processing {
          background-color: rgba(59, 130, 246, 0.9);
          color: white;
        }

        &.failed {
          background-color: rgba(239, 68, 68, 0.9);
          color: white;
        }
      }
    }

    .record-info {
      flex: 1;
      min-width: 0;

      .record-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;

        .record-filename {
          font-size: 15px;
          font-weight: 500;
          color: var(--text-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .record-type {
          padding: 3px 8px;
          background-color: #f3f4f6;
          border-radius: 4px;
          font-size: 12px;
          color: var(--text-secondary);
          flex-shrink: 0;
        }
      }

      .record-meta {
        display: flex;
        gap: 20px;
        margin-bottom: 10px;
        flex-wrap: wrap;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: var(--text-secondary);

          :deep(.el-icon) {
            font-size: 14px;
          }
        }
      }

      .record-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;

        .detected-tag {
          padding: 3px 8px;
          background-color: rgba(39, 174, 96, 0.1);
          color: #27ae60;
          border-radius: 4px;
          font-size: 12px;

          &.more {
            background-color: #f3f4f6;
            color: var(--text-secondary);
          }
        }
      }
    }

    .record-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;

    .empty-icon {
      color: #9ca3af;
      margin-bottom: 16px;
    }

    .empty-text {
      font-size: 15px;
      color: var(--text-secondary);
      margin-bottom: 24px;
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 32px;
  }

  .detail-content {
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

  .delete-warning {
    color: #ef4444;
    font-size: 13px;
    margin-top: 8px;
  }
}
</style>