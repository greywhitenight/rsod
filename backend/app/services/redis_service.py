# =============================================================================
# Redis 缓存服务模块
# =============================================================================
# 功能说明：
#   - 封装 Redis 缓存的所有操作
#   - 提供键值存储、会话管理、数据缓存等接口
#   - 支持自动序列化和反序列化
#
# Redis 简介：
#   Redis 是一个开源的内存数据结构存储系统，可用作：
#   - 数据库：存储持久化数据
#   - 缓存：存储热点数据，减少数据库压力
#   - 消息队列：实现异步通信
#   - 会话存储：保存用户登录状态
#
# 缓存策略：
#   - 用户缓存：24小时过期
#   - 会话缓存：2小时过期
#   - 目标类别缓存：1小时过期
#   - 检测结果缓存：30分钟过期
#   - 热点数据缓存：10分钟过期
#
# 使用示例：
#   from app.services.redis_service import redis_service
#
#   # 基本操作
#   redis_service.set("key", "value", expire=3600)
#   value = redis_service.get("key")
#
#   # 用户缓存
#   redis_service.set_user(user_id, user_data)
#   user_data = redis_service.get_user(user_id)
#
#   # 会话管理
#   redis_service.set_session(session_id, user_id)
#   user_id = redis_service.get_session(session_id)
# =============================================================================

# 导入 Redis Python 客户端
import redis

# 导入 json 模块，用于序列化/反序列化复杂数据类型
import json

# 导入类型提示
from typing import Optional, Any

# 导入 timedelta，用于时间相关操作
from datetime import timedelta

# 导入应用配置
from app.config import settings


class RedisService:
    """
    Redis 缓存服务类

    该类封装了所有 Redis 缓存的操作，包括：
    - 基础键值操作（SET/GET/DEL）
    - 用户信息缓存
    - 会话管理
    - 检测结果缓存
    - 热点数据缓存
    - 计数器操作
    """

    def __init__(self):
        """
        初始化 Redis 客户端

        功能：
        - 创建 Redis 客户端连接
        - 配置连接参数
        """
        # 创建 Redis 客户端实例
        self.client = redis.Redis(
            host=settings.redis.host,                        # Redis 服务器地址
            port=settings.redis.port,                        # Redis 服务器端口
            # Redis 访问密码（如果配置了的话）
            password=settings.redis.password if settings.redis.password else None,
            decode_responses=True                            # 自动将响应解码为字符串（而非字节）
        )

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置键值对

        参数：
            key: 键名
            value: 值（可以是基本类型、字典或列表）
            expire: 过期时间（秒），None 表示永不过期

        返回：
            bool: 设置是否成功

        功能：
            - 自动将字典和列表序列化为 JSON
            - 支持设置过期时间
        """
        # 如果值是字典或列表，序列化为 JSON 字符串
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        # 设置值
        if expire:
            # 带过期时间设置（SETEX 命令）
            return self.client.setex(key, expire, value)
        else:
            # 永久设置（SET 命令）
            return self.client.set(key, value)

    def get(self, key: str) -> Optional[Any]:
        """
        获取键值对

        参数：
            key: 键名

        返回：
            Optional[Any]: 值（自动反序列化 JSON），不存在返回 None

        功能：
            - 自动反序列化 JSON 字符串为字典或列表
            - 如果不是 JSON，返回原始值
        """
        # 获取值
        value = self.client.get(key)

        if value:
            try:
                # 尝试将 JSON 字符串反序列化为对象
                return json.loads(value)
            except (ValueError, TypeError):
                # 如果不是 JSON 格式，返回原始值
                return value
        return None

    def delete(self, key: str) -> int:
        """
        删除键

        参数：
            key: 键名

        返回：
            int: 删除的键数量（0 或 1）
        """
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        参数：
            key: 键名

        返回：
            bool: 是否存在
        """
        return self.client.exists(key) > 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间

        参数：
            key: 键名
            seconds: 过期时间（秒）

        返回：
            bool: 设置是否成功
        """
        return self.client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        参数：
            key: 键名

        返回：
            int: 剩余秒数，-1 表示永不过期，-2 表示键不存在
        """
        return self.client.ttl(key)

    # =========================================================================
    # 用户缓存操作
    # =========================================================================

    def set_user(self, user_id: str, user_data: dict, expire: int = 86400) -> bool:
        """
        缓存用户信息

        参数：
            user_id: 用户 ID
            user_data: 用户数据字典
            expire: 过期时间（秒），默认 24 小时

        返回：
            bool: 是否成功

        键格式：user:{user_id}
        """
        # 构建缓存键，格式：user:{用户ID}
        key = f"user:{user_id}"
        return self.set(key, user_data, expire)

    def get_user(self, user_id: str) -> Optional[dict]:
        """
        获取缓存的用户信息

        参数：
            user_id: 用户 ID

        返回：
            Optional[dict]: 用户数据，不存在返回 None

        键格式：user:{user_id}
        """
        key = f"user:{user_id}"
        return self.get(key)

    def delete_user(self, user_id: str) -> int:
        """
        删除缓存的用户信息

        参数：
            user_id: 用户 ID

        返回：
            int: 删除的键数量

        键格式：user:{user_id}
        """
        key = f"user:{user_id}"
        return self.delete(key)

    # =========================================================================
    # 会话管理
    # =========================================================================

    def set_session(self, session_id: str, user_id: str, expire: int = 7200) -> bool:
        """
        创建用户会话

        参数：
            session_id: 会话 ID（通常由登录时生成）
            user_id: 用户 ID
            expire: 过期时间（秒），默认 2 小时

        返回：
            bool: 是否成功

        功能：
            - 用于保存用户登录状态
            - 会话过期后需要重新登录

        键格式：session:{session_id}
        """
        key = f"session:{session_id}"
        return self.set(key, user_id, expire)

    def get_session(self, session_id: str) -> Optional[str]:
        """
        获取会话对应的用户 ID

        参数：
            session_id: 会话 ID

        返回：
            Optional[str]: 用户 ID，不存在返回 None

        键格式：session:{session_id}
        """
        key = f"session:{session_id}"
        return self.get(key)

    def delete_session(self, session_id: str) -> int:
        """
        删除会话（登出）

        参数：
            session_id: 会话 ID

        返回：
            int: 删除的键数量

        键格式：session:{session_id}
        """
        key = f"session:{session_id}"
        return self.delete(key)

    # =========================================================================
    # 目标类别缓存
    # =========================================================================

    def set_target_categories(self, categories: list, expire: int = 3600) -> bool:
        """
        缓存目标类别列表

        参数：
            categories: 目标类别列表
            expire: 过期时间（秒），默认 1 小时

        返回：
            bool: 是否成功

        功能：
            - 缓存所有可检测的目标类别
            - 减少数据库查询压力

        键格式：target_categories
        """
        key = "target_categories"
        return self.set(key, categories, expire)

    def get_target_categories(self) -> Optional[list]:
        """
        获取缓存的目标类别列表

        返回：
            Optional[list]: 目标类别列表，不存在返回 None

        键格式：target_categories
        """
        key = "target_categories"
        return self.get(key)

    # =========================================================================
    # 检测结果缓存
    # =========================================================================

    def set_detection(self, record_id: str, detection_data: dict, expire: int = 1800) -> bool:
        """
        缓存检测结果

        参数：
            record_id: 检测记录 ID
            detection_data: 检测结果数据
            expire: 过期时间（秒），默认 30 分钟

        返回：
            bool: 是否成功

        功能：
            - 缓存检测结果，加快重复查询
            - 过期后重新计算

        键格式：detection:{record_id}
        """
        key = f"detection:{record_id}"
        return self.set(key, detection_data, expire)

    def get_detection(self, record_id: str) -> Optional[dict]:
        """
        获取缓存的检测结果

        参数：
            record_id: 检测记录 ID

        返回：
            Optional[dict]: 检测结果，不存在返回 None

        键格式：detection:{record_id}
        """
        key = f"detection:{record_id}"
        return self.get(key)

    def invalidate_detection(self, record_id: str) -> int:
        """
        使检测结果缓存失效

        参数：
            record_id: 检测记录 ID

        返回：
            int: 删除的键数量

        功能：
            - 当检测结果更新时调用
            - 强制重新计算

        键格式：detection:{record_id}
        """
        key = f"detection:{record_id}"
        return self.delete(key)

    # =========================================================================
    # 模型信息缓存
    # =========================================================================

    def set_model(self, model_name: str, version: str, model_data: dict, expire: int = 3600) -> bool:
        """
        缓存模型信息

        参数：
            model_name: 模型名称
            version: 模型版本
            model_data: 模型数据
            expire: 过期时间（秒），默认 1 小时

        返回：
            bool: 是否成功

        功能：
            - 缓存模型配置信息
            - 减少数据库查询

        键格式：model:{model_name}:{version}
        """
        key = f"model:{model_name}:{version}"
        return self.set(key, model_data, expire)

    def get_model(self, model_name: str, version: str) -> Optional[dict]:
        """
        获取缓存的模型信息

        参数：
            model_name: 模型名称
            version: 模型版本

        返回：
            Optional[dict]: 模型数据，不存在返回 None

        键格式：model:{model_name}:{version}
        """
        key = f"model:{model_name}:{version}"
        return self.get(key)

    # =========================================================================
    # 热点数据缓存
    # =========================================================================

    def set_hot_detections(self, user_id: str, detections: list, expire: int = 600) -> bool:
        """
        缓存用户的热点检测记录

        参数：
            user_id: 用户 ID
            detections: 检测记录列表
            expire: 过期时间（秒），默认 10 分钟

        返回：
            bool: 是否成功

        功能：
            - 缓存用户频繁访问的检测记录
            - 加快列表加载速度

        键格式：hot_detections:{user_id}
        """
        key = f"hot_detections:{user_id}"
        return self.set(key, detections, expire)

    def get_hot_detections(self, user_id: str) -> Optional[list]:
        """
        获取缓存的热点检测记录

        参数：
            user_id: 用户 ID

        返回：
            Optional[list]: 检测记录列表，不存在返回 None

        键格式：hot_detections:{user_id}
        """
        key = f"hot_detections:{user_id}"
        return self.get(key)

    # =========================================================================
    # 计数器操作
    # =========================================================================

    def increment_counter(self, key: str) -> int:
        """
        递增计数器

        参数：
            key: 计数器键名

        返回：
            int: 递增后的值

        功能：
            - 原子递增操作
            - 适用于统计访问次数等场景
        """
        return self.client.incr(key)

    def get_counter(self, key: str) -> int:
        """
        获取计数器值

        参数：
            key: 计数器键名

        返回：
            int: 计数器值，不存在返回 0
        """
        value = self.client.get(key)
        return int(value) if value else 0

    # =========================================================================
    # 连接测试和其他工具方法
    # =========================================================================

    def ping(self) -> bool:
        """
        测试 Redis 连接

        返回：
            bool: 连接是否成功

        功能：
            - 用于健康检查
            - 验证 Redis 服务是否可用
        """
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False

    def flush_all(self) -> bool:
        """
        清空所有数据（谨慎使用！）

        返回：
            bool: 操作是否成功

        功能：
            - 删除 Redis 数据库中的所有键
            - ⚠️ 仅在测试环境或需要完全重置时使用
        """
        return self.client.flushall()


# =============================================================================
# 全局 Redis 服务实例
# =============================================================================
# 创建全局唯一的 Redis 服务实例（单例模式）
# 在应用的任何地方都可以通过 import redis_service 访问
redis_service = RedisService()
