import pytest
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User
from app.core.security import create_access_token, verify_password, get_password_hash

pytestmark = [pytest.mark.security, pytest.mark.asyncio]

async def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password123"
    hashed = get_password_hash(password)
    
    # Verify hashed password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)
    
    # Ensure hash is different each time
    another_hash = get_password_hash(password)
    assert hashed != another_hash
    assert verify_password(password, another_hash)

async def test_jwt_token_creation_and_validation():
    """Test JWT token creation and validation."""
    user_data = {"sub": "test@example.com", "user_id": 1}
    token = create_access_token(user_data)
    
    # Decode and verify token
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    
    assert decoded["sub"] == user_data["sub"]
    assert decoded["user_id"] == user_data["user_id"]
    assert "exp" in decoded
    
    # Test token expiration
    expired_token = create_access_token(
        user_data,
        expires_delta=timedelta(microseconds=1)
    )
    await asyncio.sleep(0.1)
    
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

async def test_api_authentication(client, test_user: User):
    """Test API authentication and authorization."""
    # Test without token
    response = await client.get("/api/v1/documents")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test with invalid token
    response = await client.get(
        "/api/v1/documents",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test with valid token
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    response = await client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

async def test_role_based_access(client, test_user: User, db: AsyncSession):
    """Test role-based access control."""
    # Create users with different roles
    normal_user = test_user
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin_password"),
        is_superuser=True
    )
    db.add(admin_user)
    await db.commit()
    
    # Test admin-only endpoint
    admin_token = create_access_token({"sub": admin_user.email, "user_id": admin_user.id})
    normal_token = create_access_token({"sub": normal_user.email, "user_id": normal_user.id})
    
    # Normal user should not access admin endpoint
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Admin should access admin endpoint
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == status.HTTP_200_OK

async def test_sql_injection_prevention(client, test_user: User):
    """Test SQL injection prevention."""
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    
    # Test potential SQL injection in query parameters
    injection_attempts = [
        "1 OR 1=1",
        "1; DROP TABLE users;",
        "1 UNION SELECT * FROM users",
        "1' OR '1'='1"
    ]
    
    for attempt in injection_attempts:
        response = await client.get(
            f"/api/v1/documents?id={attempt}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if response.status_code == status.HTTP_200_OK:
            # Ensure response doesn't contain sensitive data
            data = response.json()
            assert "password" not in str(data)
            assert "hashed_password" not in str(data)

async def test_xss_prevention(client, test_user: User):
    """Test Cross-Site Scripting (XSS) prevention."""
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    
    # Test XSS payload in document content
    xss_payload = "<script>alert('xss')</script>"
    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Document",
            "content": xss_payload
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert xss_payload not in data["content"]
    assert "&lt;script&gt;" in data["content"]

async def test_rate_limiting(client, test_user: User):
    """Test API rate limiting."""
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    
    # Make multiple requests in quick succession
    responses = []
    for _ in range(50):  # Adjust based on rate limit
        response = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token}"}
        )
        responses.append(response.status_code)
    
    # Verify rate limiting is working
    assert status.HTTP_429_TOO_MANY_REQUESTS in responses

async def test_secure_file_upload(client, test_user: User):
    """Test secure file upload handling."""
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    
    # Test file type validation
    files = [
        ("test.txt", b"text content", "text/plain"),
        ("test.exe", b"binary content", "application/x-msdownload"),
        ("test.jpg", b"image content", "image/jpeg"),
        ("test.php", b"<?php echo 'hack'; ?>", "text/x-php"),
    ]
    
    for filename, content, content_type in files:
        response = await client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, content, content_type)}
        )
        
        if content_type in ["text/plain", "image/jpeg"]:
            assert response.status_code == status.HTTP_200_OK
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
