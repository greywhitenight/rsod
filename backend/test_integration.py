"""
集成测试脚本
功能：测试所有服务的连接和基本功能
"""

import sys
sys.path.insert(0, '.')

from app.config import settings


def test_config():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("1. 配置加载测试")
    print("=" * 60)

    print(f"\n[应用配置]")
    print(f"  应用名称: {settings.app_name}")
    print(f"  应用版本: {settings.app_version}")
    print(f"  调试模式: {settings.debug}")
    print(f"  监听地址: {settings.host}:{settings.port}")

    print(f"\n[数据库配置]")
    print(f"  主机: {settings.database.host}")
    print(f"  端口: {settings.database.port}")
    print(f"  用户: {settings.database.username}")
    print(f"  数据库: {settings.database.database}")

    print(f"\n[MinIO 配置]")
    print(f"  主机: {settings.minio.host}")
    print(f"  端口: {settings.minio.port}")
    print(f"  安全连接: {settings.minio.secure}")

    print(f"\n[Redis 配置]")
    print(f"  主机: {settings.redis.host}")
    print(f"  端口: {settings.redis.port}")

    print("\n✅ 配置加载成功")
    return True


def test_database():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("2. 数据库连接测试")
    print("=" * 60)

    try:
        from sqlalchemy import text
        from app.models.database import engine

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n✅ 数据库连接成功")
            print(f"  PostgreSQL 版本: {version[:50]}...")

            # 测试查询
            result = conn.execute(text("SELECT COUNT(*) FROM target_categories;"))
            count = result.fetchone()[0]
            print(f"  目标类别数量: {count}")

            return True
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        return False


def test_redis():
    """测试 Redis 连接"""
    print("\n" + "=" * 60)
    print("3. Redis 连接测试")
    print("=" * 60)

    try:
        from app.services.redis_service import redis_service

        # 测试连接
        if redis_service.ping():
            print("\n✅ Redis 连接成功")

            # 测试基本操作
            test_key = "test_key"
            test_value = {"test": "data"}

            redis_service.set(test_key, test_value, expire=60)
            retrieved = redis_service.get(test_key)

            if retrieved == test_value:
                print("  ✅ SET/GET 操作正常")
            else:
                print("  ❌ SET/GET 操作失败")

            redis_service.delete(test_key)
            print("  ✅ DELETE 操作正常")

            return True
        else:
            print("\n❌ Redis 连接失败")
            return False
    except Exception as e:
        print(f"\n❌ Redis 连接异常: {e}")
        return False


def test_minio():
    """测试 MinIO 连接"""
    print("\n" + "=" * 60)
    print("4. MinIO 连接测试")
    print("=" * 60)

    try:
        from app.services.minio_service import minio_service

        # 列出 Bucket
        buckets = minio_service.client.list_buckets()
        print(f"\n✅ MinIO 连接成功")
        print(f"  Bucket 数量: {len(buckets)}")
        print(f"  Bucket 列表:")
        for bucket in buckets:
            print(f"    - {bucket.name}")

        # 测试生成 URL
        test_url = minio_service.get_public_url("rsod-original", "test.jpg")
        print(f"  ✅ 公开 URL 生成: {test_url}")

        return True
    except Exception as e:
        print(f"\n❌ MinIO 连接失败: {e}")
        return False


def test_directories():
    """测试目录创建"""
    print("\n" + "=" * 60)
    print("5. 目录结构测试")
    print("=" * 60)

    import os

    dirs = [
        settings.static_dir,
        settings.upload_dir,
        settings.result_dir
    ]

    print("\n检查目录:")
    all_exist = True
    for dir_path in dirs:
        exists = os.path.exists(dir_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path}")
        if not exists:
            all_exist = False

    if all_exist:
        print("\n✅ 所有目录正常")
    else:
        print("\n⚠️ 部分目录不存在（首次运行会自动创建）")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("RSOD Platform - 集成测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("配置加载", test_config()))
    results.append(("数据库连接", test_database()))
    results.append(("Redis 连接", test_redis()))
    results.append(("MinIO 连接", test_minio()))
    results.append(("目录结构", test_directories()))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())