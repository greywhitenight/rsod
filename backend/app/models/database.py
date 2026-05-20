# =============================================================================
# 数据库 ORM 模型定义
# =============================================================================
# 功能：定义数据库表结构，使用 SQLAlchemy ORM 映射
# 依赖：sqlalchemy（ORM 框架）
# =============================================================================

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from app.config import settings

# 构建 PostgreSQL 数据库连接 URL
# 格式：postgresql+psycopg2://用户名:密码@主机:端口/数据库名
DATABASE_URL = (
    f"postgresql+psycopg2://{settings.database.username}:{settings.database.password}"
    f"@{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类（所有模型的父类）
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数

    用法：在 FastAPI 路由中使用 Depends(get_db) 注入数据库会话

    示例：
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# 用户模型
# =============================================================================
class User(Base):
    """用户表模型"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    role = Column(String(20), default="user")                      # admin 或 user
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系：一个用户可以有多个检测记录
    detection_records = relationship("DetectionRecord", back_populates="user")
    # 关系：一个用户可以有多个 AI 问答记录
    ai_qa_records = relationship("AIQARecord", back_populates="user")


# =============================================================================
# 检测记录模型
# =============================================================================
class DetectionRecord(Base):
    """检测记录表模型"""
    __tablename__ = "detection_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(20), nullable=False)                        # single/batch/folder/video
    status = Column(String(20), default="pending")                  # pending/processing/completed/failed
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20), default="1.0.0")
    total_objects = Column(Integer, default=0)                      # 检测到的目标总数
    detection_time = Column(Float)                                  # 检测耗时（秒）
    original_image_key = Column(String(500))                         # 原始图片在 MinIO 中的 Key
    result_image_key = Column(String(500))                          # 结果图片在 MinIO 中的 Key
    error_message = Column(Text)                                    # 错误信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系：属于某个用户
    user = relationship("User", back_populates="detection_records")
    # 关系：包含多个检测结果
    results = relationship("DetectionResult", back_populates="record")


# =============================================================================
# 检测结果模型
# =============================================================================
class DetectionResult(Base):
    """检测结果表模型"""
    __tablename__ = "detection_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(36), ForeignKey("detection_records.id", ondelete="CASCADE"), nullable=False)
    x1 = Column(Float, nullable=False)                               # 检测框左上角 X
    y1 = Column(Float, nullable=False)                               # 检测框左上角 Y
    x2 = Column(Float, nullable=False)                               # 检测框右下角 X
    y2 = Column(Float, nullable=False)                               # 检测框右下角 Y
    confidence = Column(Float, nullable=False)                       # 置信度（0-1）
    class_id = Column(Integer, nullable=False)                      # 类别 ID
    class_name = Column(String(50), nullable=False)                  # 英文类别名
    chinese_name = Column(String(50))                               # 中文类别名

    # 关系：属于某条检测记录
    record = relationship("DetectionRecord", back_populates="results")


# =============================================================================
# 目标类别模型
# =============================================================================
class TargetCategory(Base):
    """目标类别表模型"""
    __tablename__ = "target_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)           # 英文名称
    chinese_name = Column(String(50), unique=True, nullable=False)  # 中文名称
    description = Column(Text)                                      # 描述
    icon_url = Column(String(500))                                   # 图标 URL
    color = Column(String(20), default="#10b981")                    # 显示颜色
    enabled = Column(Boolean, default=True)                          # 是否启用
    sort_order = Column(Integer, default=0)                         # 排序顺序
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# =============================================================================
# AI 问答记录模型
# =============================================================================
class AIQARecord(Base):
    """AI 问答记录表模型"""
    __tablename__ = "ai_qa_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    question = Column(Text, nullable=False)                          # 问题
    answer = Column(Text)                                            # 回答
    model_name = Column(String(50))                                  # 使用的 AI 模型
    status = Column(String(20), default="pending")                  # pending/completed/failed
    created_at = Column(DateTime, default=datetime.now)

    # 关系：属于某个用户
    user = relationship("User", back_populates="ai_qa_records")


# =============================================================================
# 模型版本模型
# =============================================================================
class ModelVersion(Base):
    """模型版本表模型"""
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)                       # 模型名称
    version = Column(String(20), nullable=False)                     # 版本号
    description = Column(Text)                                        # 描述
    model_key = Column(String(500))                                  # 模型文件在 MinIO 中的 Key
    status = Column(String(20), default="active")                     # active/inactive
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 创建所有表（仅在模型定义改变时执行）
def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # 单独运行此文件时初始化数据库
    init_db()
    print("Database tables created successfully!")