<template>
  <div class="validation-result" v-if="validation">
    <!-- 验证状态头部 -->
    <div class="validation-header" :class="validationClass">
      <div class="validation-status">
        <el-icon :class="['status-icon', validationClass]"><component :is="statusIcon" /></el-icon>
        <span class="status-text">{{ validation.message }}</span>
      </div>
      <div class="validation-meta">
        <span class="meta-item">验证版本: {{ validation.version || '1.0.0' }}</span>
        <span class="meta-item">验证时间: {{ formatTime(validation.validated_at) }}</span>
      </div>
    </div>

    <!-- 警告列表 -->
    <div v-if="validation.warnings && validation.warnings.length > 0" class="validation-section warnings-section">
      <div class="section-header">
        <el-icon class="section-icon warning-icon"><component :is="'AlertTriangle'" /></el-icon>
        <span class="section-title">警告信息 ({{ validation.warnings.length }})</span>
      </div>
      <div class="warning-list">
        <div v-for="(warning, index) in validation.warnings" :key="index" class="warning-item">
          <el-icon><component :is="'CircleAlert'" /></el-icon>
          <span>{{ warning }}</span>
        </div>
      </div>
    </div>

    <!-- 错误列表 -->
    <div v-if="validation.errors && validation.errors.length > 0" class="validation-section errors-section">
      <div class="section-header">
        <el-icon class="section-icon error-icon"><component :is="'XCircle'" /></el-icon>
        <span class="section-title">错误信息 ({{ validation.errors.length }})</span>
      </div>
      <div class="error-list">
        <div v-for="(error, index) in validation.errors" :key="index" class="error-item">
          <el-icon><component :is="'Close'" /></el-icon>
          <span>{{ error }}</span>
        </div>
      </div>
    </div>

    <!-- 详细验证信息 -->
    <div v-if="validation.validation_details" class="validation-details">
      <div class="section-header">
        <el-icon class="section-icon info-icon"><component :is="'InfoFilled'" /></el-icon>
        <span class="section-title">验证详情</span>
      </div>
      
      <!-- 数据完整性验证 -->
      <div v-if="validation.validation_details.integrity" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">数据完整性</span>
          <span :class="['detail-status', validation.validation_details.integrity.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.integrity.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div v-if="validation.validation_details.integrity.missing_fields?.length > 0" class="detail-content">
          <span class="detail-desc">缺失字段: {{ validation.validation_details.integrity.missing_fields.join(', ') }}</span>
        </div>
      </div>

      <!-- 目标数量验证 -->
      <div v-if="validation.validation_details.target_count" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">目标数量</span>
          <span :class="['detail-status', validation.validation_details.target_count.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.target_count.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div class="detail-content">
          <span class="detail-desc">检测目标: {{ validation.validation_details.target_count.total_objects }} 个</span>
        </div>
      </div>

      <!-- 置信度验证 -->
      <div v-if="validation.validation_details.confidence" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">置信度分布</span>
          <span :class="['detail-status', validation.validation_details.confidence.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.confidence.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div class="detail-content">
          <span class="detail-desc">检测框数: {{ validation.validation_details.confidence.total_boxes }}</span>
          <span class="detail-desc">平均置信度: {{ (validation.validation_details.confidence.avg_confidence * 100).toFixed(1) }}%</span>
          <span class="detail-desc">最低置信度: {{ (validation.validation_details.confidence.min_confidence * 100).toFixed(1) }}%</span>
          <span class="detail-desc">最高置信度: {{ (validation.validation_details.confidence.max_confidence * 100).toFixed(1) }}%</span>
          <span v-if="validation.validation_details.confidence.low_confidence_count > 0" class="detail-desc warning-desc">
            低置信度目标: {{ validation.validation_details.confidence.low_confidence_count }} 个
          </span>
        </div>
      </div>

      <!-- 检测时间验证 -->
      <div v-if="validation.validation_details.detection_time" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">检测耗时</span>
          <span :class="['detail-status', validation.validation_details.detection_time.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.detection_time.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div class="detail-content">
          <span class="detail-desc">耗时: {{ validation.validation_details.detection_time.detection_time.toFixed(3) }} 秒</span>
        </div>
      </div>

      <!-- 图像尺寸验证 -->
      <div v-if="validation.validation_details.dimensions" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">图像尺寸</span>
          <span :class="['detail-status', validation.validation_details.dimensions.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.dimensions.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div class="detail-content">
          <span class="detail-desc">尺寸: {{ validation.validation_details.dimensions.width }} × {{ validation.validation_details.dimensions.height }}</span>
          <span class="detail-desc">宽高比: {{ validation.validation_details.dimensions.aspect_ratio.toFixed(2) }}</span>
        </div>
      </div>

      <!-- 状态验证 -->
      <div v-if="validation.validation_details.status" class="detail-item">
        <div class="detail-header">
          <span class="detail-label">检测状态</span>
          <span :class="['detail-status', validation.validation_details.status.pass ? 'pass' : 'fail']">
            {{ validation.validation_details.status.pass ? '通过' : '失败' }}
          </span>
        </div>
        <div class="detail-content">
          <span class="detail-desc">状态: {{ validation.validation_details.status.status }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  validation: {
    type: Object,
    default: null
  }
});

// 根据验证结果确定样式类
const validationClass = computed(() => {
  if (!props.validation) return '';
  if (props.validation.is_valid) {
    return props.validation.warnings?.length > 0 ? 'validation-warning' : 'validation-success';
  }
  return 'validation-error';
});

// 根据验证结果确定状态图标
const statusIcon = computed(() => {
  if (!props.validation) return 'InfoFilled';
  if (props.validation.is_valid) {
    return props.validation.warnings?.length > 0 ? 'AlertTriangle' : 'CircleCheck';
  }
  return 'XCircle';
});

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '未知';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
</script>

<style scoped>
.validation-result {
  border-radius: 8px;
  overflow: hidden;
  margin-top: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 验证头部 */
.validation-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.validation-success {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-left: 4px solid #4caf50;
}

.validation-warning {
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  border-left: 4px solid #ff9800;
}

.validation-error {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border-left: 4px solid #f44336;
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon {
  font-size: 24px;
}

.validation-success .status-icon {
  color: #4caf50;
}

.validation-warning .status-icon {
  color: #ff9800;
}

.validation-error .status-icon {
  color: #f44336;
}

.status-text {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.validation-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.meta-item {
  background: rgba(255, 255, 255, 0.8);
  padding: 4px 12px;
  border-radius: 4px;
}

/* 验证区域 */
.validation-section {
  padding: 16px 20px;
  background: #fafafa;
  border-top: 1px solid #eee;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #333;
}

.section-icon {
  font-size: 18px;
}

.warning-icon {
  color: #ff9800;
}

.error-icon {
  color: #f44336;
}

.info-icon {
  color: #1989fa;
}

.warning-list,
.error-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.warning-item,
.error-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
}

.warning-item {
  background: #fff8e1;
  color: #e65100;
}

.error-item {
  background: #ffebee;
  color: #c62828;
}

/* 详细信息 */
.validation-details {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #eee;
}

.detail-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e0e0e0;
}

.detail-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.detail-label {
  font-weight: 600;
  color: #333;
}

.detail-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.detail-status.pass {
  background: #e8f5e9;
  color: #2e7d32;
}

.detail-status.fail {
  background: #ffebee;
  color: #c62828;
}

.detail-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.detail-desc {
  font-size: 14px;
  color: #666;
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.detail-desc.warning-desc {
  background: #fff8e1;
  color: #e65100;
}
</style>
