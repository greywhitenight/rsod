# =============================================================================
# 数据库模块
# =============================================================================
# 功能：提供数据库连接和会话管理
# 依赖：sqlalchemy
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
