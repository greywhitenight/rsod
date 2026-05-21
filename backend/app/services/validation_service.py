# =============================================================================
# 检测数据验证服务
# =============================================================================
# 功能说明：
#   - 对图像检测结果进行全面的数据验证
#   - 确保检测结果的完整性、准确性和可靠性
#   - 提供详细的验证报告和问题警告
#
# 验证维度：
#   1. 数据完整性验证 - 检查必要字段是否存在
#   2. 目标数量验证 - 检测目标数量是否在合理范围内
#   3. 置信度验证 - 检查检测目标的置信度分布
#   4. 检测时间验证 - 验证检测耗时是否正常
#   5. 数据格式验证 - 检查数据格式是否符合规范
#   6. 异常情况检测 - 识别潜在的异常检测结果
#
# 使用示例：
#   from app.services.validation_service import validation_service
#   
#   # 验证检测结果
#   validation_result = validation_service.validate_detection(result)
#   
#   # 检查验证状态
#   if validation_result['is_valid']:
#       print("检测结果通过验证")
#   else:
#       print(f"验证失败: {validation_result['message']}")
# =============================================================================

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ValidationService:
    """
    检测数据验证服务
    
    提供对目标检测结果的全面验证功能，确保数据质量和可靠性。
    """
    
    def __init__(self):
        """初始化验证服务，设置验证阈值"""
        # 验证阈值配置
        self.thresholds = {
            # 置信度相关阈值
            'min_confidence': 0.01,           # 最小置信度阈值
            'low_confidence_threshold': 0.3,   # 低置信度警告阈值
            'high_confidence_threshold': 0.95, # 高置信度阈值
            
            # 目标数量相关阈值
            'min_targets': 0,                  # 最小目标数量
            'max_targets': 100,                # 最大目标数量（异常检测）
            'large_target_warning': 50,        # 大量目标警告阈值
            
            # 检测时间相关阈值（毫秒）
            'normal_detection_time': 3000,     # 正常检测时间（3秒）
            'slow_detection_warning': 10000,   # 慢速检测警告（10秒）
            'timeout_threshold': 60000,        # 超时阈值（60秒）
            
            # 图像尺寸相关阈值（像素）
            'min_image_width': 100,
            'min_image_height': 100,
            'max_image_width': 10000,
            'max_image_height': 10000,
        }
    
    def validate_detection(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        对检测结果进行全面验证
        
        参数：
            detection_result: 检测结果字典，包含以下字段：
                - detection_id: 检测ID
                - filename: 文件名
                - image_url: 原始图片URL
                - result_image_url: 结果图片URL
                - total_objects: 检测到的目标数量
                - detection_time: 检测耗时（秒）
                - model_name: 使用的模型名称
                - status: 检测状态
                - boxes: 检测框列表（可选）
                - image_width: 图片宽度（可选）
                - image_height: 图片高度（可选）
        
        返回：
            dict: 验证结果，包含：
                - is_valid: 是否通过验证
                - message: 验证结果摘要
                - warnings: 警告信息列表
                - errors: 错误信息列表
                - validation_details: 各维度验证详情
        """
        validation_details = {}
        warnings = []
        errors = []
        is_valid = True
        
        # 1. 数据完整性验证
        integrity_result = self._validate_integrity(detection_result)
        validation_details['integrity'] = integrity_result
        if not integrity_result['pass']:
            is_valid = False
            errors.extend(integrity_result['errors'])
        
        # 2. 目标数量验证
        count_result = self._validate_target_count(detection_result)
        validation_details['target_count'] = count_result
        if not count_result['pass']:
            is_valid = False
            errors.extend(count_result['errors'])
        warnings.extend(count_result['warnings'])
        
        # 3. 置信度验证（如果有boxes数据）
        if 'boxes' in detection_result and detection_result['boxes']:
            confidence_result = self._validate_confidence(detection_result['boxes'])
            validation_details['confidence'] = confidence_result
            if not confidence_result['pass']:
                is_valid = False
                errors.extend(confidence_result['errors'])
            warnings.extend(confidence_result['warnings'])
        
        # 4. 检测时间验证
        time_result = self._validate_detection_time(detection_result)
        validation_details['detection_time'] = time_result
        if not time_result['pass']:
            is_valid = False
            errors.extend(time_result['errors'])
        warnings.extend(time_result['warnings'])
        
        # 5. 图像尺寸验证（如果有尺寸信息）
        if 'image_width' in detection_result and 'image_height' in detection_result:
            dimension_result = self._validate_image_dimensions(detection_result)
            validation_details['dimensions'] = dimension_result
            if not dimension_result['pass']:
                is_valid = False
                errors.extend(dimension_result['errors'])
            warnings.extend(dimension_result['warnings'])
        
        # 6. 状态验证
        status_result = self._validate_status(detection_result)
        validation_details['status'] = status_result
        if not status_result['pass']:
            is_valid = False
            errors.extend(status_result['errors'])
        
        # 生成验证摘要消息
        if is_valid:
            if warnings:
                message = f"检测结果通过验证，但存在 {len(warnings)} 条警告"
            else:
                message = "检测结果通过验证"
        else:
            message = f"检测结果验证失败，存在 {len(errors)} 个错误"
        
        # 记录验证日志
        logger.info(f"验证完成 - 检测ID: {detection_result.get('detection_id', 'N/A')}, "
                   f"有效: {is_valid}, 警告: {len(warnings)}, 错误: {len(errors)}")
        
        return {
            'is_valid': is_valid,
            'message': message,
            'warnings': warnings,
            'errors': errors,
            'validation_details': validation_details,
            'validated_at': datetime.now().isoformat(),
            'version': '1.0.0'
        }
    
    def _validate_integrity(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证数据完整性
        
        检查检测结果是否包含所有必要字段
        """
        required_fields = [
            'detection_id',
            'filename',
            'image_url',
            'result_image_url',
            'total_objects',
            'detection_time',
            'model_name',
            'status'
        ]
        
        missing_fields = []
        errors = []
        
        for field in required_fields:
            if field not in result:
                missing_fields.append(field)
                errors.append(f"缺少必要字段: {field}")
        
        return {
            'pass': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'errors': errors,
            'warnings': []
        }
    
    def _validate_target_count(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证目标数量是否在合理范围内
        """
        total_objects = result.get('total_objects', 0)
        errors = []
        warnings = []
        is_pass = True
        
        # 检查目标数量是否为非负整数
        if not isinstance(total_objects, int) or total_objects < self.thresholds['min_targets']:
            errors.append(f"目标数量无效: {total_objects}")
            is_pass = False
        
        # 检查目标数量是否异常过多
        if total_objects > self.thresholds['max_targets']:
            errors.append(f"目标数量异常过多: {total_objects}（最大允许 {self.thresholds['max_targets']}）")
            is_pass = False
        
        # 大量目标警告
        if total_objects > self.thresholds['large_target_warning'] and total_objects <= self.thresholds['max_targets']:
            warnings.append(f"检测到大量目标: {total_objects} 个，建议人工复核")
        
        # 零目标警告（可选场景）
        if total_objects == 0:
            warnings.append("未检测到任何目标，建议检查图片质量或调整检测参数")
        
        return {
            'pass': is_pass,
            'total_objects': total_objects,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_confidence(self, boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证检测目标的置信度分布
        
        参数：
            boxes: 检测框列表，每个框包含 confidence 字段
        """
        errors = []
        warnings = []
        is_pass = True
        
        low_confidence_targets = []
        very_low_confidence_targets = []
        
        for idx, box in enumerate(boxes):
            confidence = box.get('confidence', 0.0)
            
            # 检查置信度是否在有效范围内
            if confidence < 0.0 or confidence > 1.0:
                errors.append(f"第 {idx+1} 个目标置信度无效: {confidence}")
                is_pass = False
                continue
            
            # 低置信度警告
            if confidence < self.thresholds['low_confidence_threshold']:
                class_name = box.get('class_name', '未知类别')
                low_confidence_targets.append({
                    'index': idx + 1,
                    'class_name': class_name,
                    'confidence': confidence
                })
            
            # 极低置信度（接近阈值）警告
            if confidence < self.thresholds['min_confidence']:
                very_low_confidence_targets.append(idx + 1)
        
        # 生成警告信息
        if low_confidence_targets:
            warnings.append(f"发现 {len(low_confidence_targets)} 个低置信度目标（置信度 < {self.thresholds['low_confidence_threshold']}）")
        
        if very_low_confidence_targets:
            warnings.append(f"发现 {len(very_low_confidence_targets)} 个极低置信度目标，建议复核")
        
        # 计算置信度统计
        confidences = [box.get('confidence', 0.0) for box in boxes]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        min_confidence = min(confidences) if confidences else 0.0
        max_confidence = max(confidences) if confidences else 0.0
        
        # 平均置信度过低警告
        if avg_confidence < self.thresholds['low_confidence_threshold']:
            warnings.append(f"平均置信度过低: {avg_confidence:.2f}")
        
        return {
            'pass': is_pass,
            'total_boxes': len(boxes),
            'avg_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'low_confidence_count': len(low_confidence_targets),
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_detection_time(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证检测耗时是否在合理范围内
        """
        detection_time = result.get('detection_time', 0.0)
        errors = []
        warnings = []
        is_pass = True
        
        # 转换为毫秒便于比较
        detection_time_ms = detection_time * 1000
        
        # 检查检测时间是否为正数
        if detection_time <= 0:
            errors.append(f"检测时间无效: {detection_time}秒")
            is_pass = False
        
        # 检查是否超时
        if detection_time_ms > self.thresholds['timeout_threshold']:
            errors.append(f"检测超时: {detection_time:.2f}秒（超时阈值 {self.thresholds['timeout_threshold']/1000}秒）")
            is_pass = False
        
        # 慢速检测警告
        if detection_time_ms > self.thresholds['slow_detection_warning'] and detection_time_ms <= self.thresholds['timeout_threshold']:
            warnings.append(f"检测速度较慢: {detection_time:.2f}秒，建议检查系统性能")
        
        # 过快检测警告（可能存在问题）
        if detection_time > 0 and detection_time < 0.01:
            warnings.append(f"检测速度异常快: {detection_time:.4f}秒，建议验证结果准确性")
        
        return {
            'pass': is_pass,
            'detection_time': detection_time,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_image_dimensions(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证图像尺寸是否在合理范围内
        """
        width = result.get('image_width', 0)
        height = result.get('image_height', 0)
        errors = []
        warnings = []
        is_pass = True
        
        # 检查宽度
        if width < self.thresholds['min_image_width']:
            errors.append(f"图片宽度过小: {width}px（最小 {self.thresholds['min_image_width']}px）")
            is_pass = False
        
        if width > self.thresholds['max_image_width']:
            errors.append(f"图片宽度过大: {width}px（最大 {self.thresholds['max_image_width']}px）")
            is_pass = False
        
        # 检查高度
        if height < self.thresholds['min_image_height']:
            errors.append(f"图片高度过小: {height}px（最小 {self.thresholds['min_image_height']}px）")
            is_pass = False
        
        if height > self.thresholds['max_image_height']:
            errors.append(f"图片高度过大: {height}px（最大 {self.thresholds['max_image_height']}px）")
            is_pass = False
        
        # 宽高比异常警告
        if width > 0 and height > 0:
            aspect_ratio = width / height
            if aspect_ratio < 0.1 or aspect_ratio > 10:
                warnings.append(f"图片宽高比异常: {aspect_ratio:.2f}，建议检查图片是否正常")
        
        return {
            'pass': is_pass,
            'width': width,
            'height': height,
            'aspect_ratio': width / height if height > 0 else 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_status(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证检测状态是否有效
        """
        valid_statuses = ['completed', 'processing', 'failed', 'pending']
        status = result.get('status', '')
        errors = []
        is_pass = True
        
        if status not in valid_statuses:
            errors.append(f"无效的检测状态: {status}（有效值: {', '.join(valid_statuses)}）")
            is_pass = False
        
        # 如果状态为failed，检查是否有错误信息
        if status == 'failed' and 'error' not in result:
            errors.append("检测失败但未提供错误信息")
            is_pass = False
        
        return {
            'pass': is_pass,
            'status': status,
            'errors': errors,
            'warnings': []
        }
    
    def validate_batch_detection(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量验证检测结果
        
        参数：
            batch_results: 批量检测结果列表
        
        返回：
            dict: 批量验证结果汇总
        """
        individual_results = []
        total_valid = 0
        total_warnings = 0
        total_errors = 0
        
        for result in batch_results:
            validation = self.validate_detection(result)
            individual_results.append(validation)
            
            if validation['is_valid']:
                total_valid += 1
            total_warnings += len(validation['warnings'])
            total_errors += len(validation['errors'])
        
        overall_pass = total_valid == len(batch_results)
        
        return {
            'is_valid': overall_pass,
            'total_count': len(batch_results),
            'valid_count': total_valid,
            'invalid_count': len(batch_results) - total_valid,
            'total_warnings': total_warnings,
            'total_errors': total_errors,
            'message': f"批量验证完成: {total_valid}/{len(batch_results)} 通过验证",
            'individual_results': individual_results,
            'validated_at': datetime.now().isoformat()
        }


# 创建全局验证服务实例
validation_service = ValidationService()
