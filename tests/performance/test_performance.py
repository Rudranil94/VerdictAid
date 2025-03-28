import pytest
import asyncio
import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.document_service import document_service
from app.core.config import settings

pytestmark = [pytest.mark.performance, pytest.mark.asyncio]

async def test_notification_performance(
    test_user: User,
    test_devices: List[Dict[str, Any]],
    db: AsyncSession
):
    """Test notification system performance under load."""
    start_time = time.time()
    notification_count = 100
    tasks = []
    
    # Create multiple notifications
    for i in range(notification_count):
        notification = {
            "type": "test_notification",
            "data": {
                "message": f"Test message {i}",
                "timestamp": time.time()
            }
        }
        tasks.append(
            notification_service.send_notification(
                user_id=test_user.id,
                notification_type=notification["type"],
                data=notification["data"],
                db=db
            )
        )
    
    # Send notifications concurrently
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify results
    assert len(results) == notification_count
    assert all(result is not None for result in results)
    
    # Check performance
    total_time = end_time - start_time
    avg_time = total_time / notification_count
    assert avg_time < 0.1  # Each notification should take less than 100ms

async def test_document_processing_performance(
    test_user: User,
    db: AsyncSession
):
    """Test document processing performance."""
    # Create test documents
    document_count = 10
    tasks = []
    
    for i in range(document_count):
        document_data = {
            "content": f"Test document {i} content " * 100,  # Create some substantial content
            "metadata": {
                "title": f"Test Document {i}",
                "type": "text/plain"
            }
        }
        tasks.append(
            document_service.process_document(
                user_id=test_user.id,
                document_data=document_data,
                db=db
            )
        )
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify results
    assert len(results) == document_count
    assert all(result.get("status") == "completed" for result in results)
    
    # Check performance
    total_time = end_time - start_time
    avg_time = total_time / document_count
    assert avg_time < 5.0  # Each document should process in less than 5 seconds

async def test_redis_cache_performance(
    test_user: User,
    redis_client
):
    """Test Redis cache performance."""
    key_count = 1000
    pipeline = redis_client.pipeline()
    
    # Test write performance
    start_time = time.time()
    for i in range(key_count):
        pipeline.set(f"test_key_{i}", f"test_value_{i}")
    await pipeline.execute()
    write_time = time.time() - start_time
    
    # Test read performance
    start_time = time.time()
    pipeline = redis_client.pipeline()
    for i in range(key_count):
        pipeline.get(f"test_key_{i}")
    results = await pipeline.execute()
    read_time = time.time() - start_time
    
    # Verify results
    assert len(results) == key_count
    assert all(result.decode() == f"test_value_{i}" for i, result in enumerate(results))
    
    # Check performance
    assert write_time < 1.0  # Bulk write should take less than 1 second
    assert read_time < 1.0  # Bulk read should take less than 1 second

async def test_database_performance(
    test_user: User,
    db: AsyncSession
):
    """Test database performance."""
    # Test bulk insert
    device_count = 1000
    devices = []
    
    start_time = time.time()
    for i in range(device_count):
        device = UserDevice(
            user_id=test_user.id,
            device_type="web",
            device_name=f"Test Device {i}",
            notification_channel="email"
        )
        devices.append(device)
    
    db.add_all(devices)
    await db.commit()
    insert_time = time.time() - start_time
    
    # Test bulk query
    start_time = time.time()
    result = await db.execute(
        select(UserDevice).filter(UserDevice.user_id == test_user.id)
    )
    devices = result.scalars().all()
    query_time = time.time() - start_time
    
    # Verify results
    assert len(devices) == device_count
    
    # Check performance
    assert insert_time < 5.0  # Bulk insert should take less than 5 seconds
    assert query_time < 1.0  # Bulk query should take less than 1 second

async def test_concurrent_requests(
    test_user: User,
    db: AsyncSession,
    client
):
    """Test API endpoint performance under concurrent load."""
    request_count = 100
    tasks = []
    
    # Create concurrent API requests
    for i in range(request_count):
        tasks.append(
            client.get(
                f"/api/v1/documents?page={i % 10 + 1}&per_page=10",
                headers={"Authorization": f"Bearer {test_user.id}"}
            )
        )
    
    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify responses
    assert len(responses) == request_count
    assert all(response.status_code == 200 for response in responses)
    
    # Check performance
    total_time = end_time - start_time
    avg_time = total_time / request_count
    assert avg_time < 0.05  # Each request should take less than 50ms
