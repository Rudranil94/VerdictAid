import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from app.services.document_analyzer import DocumentAnalyzer
from app.core.config import settings

@pytest.mark.asyncio
async def test_document_analysis():
    analyzer = DocumentAnalyzer()
    test_content = """
    This Agreement ("Agreement") is made on [DATE] between [PARTY A] and [PARTY B].
    
    1. The parties agree to the following terms:
       a) Payment of $1,000 shall be made within 30 days.
       b) Services shall be delivered by [DEADLINE].
    """
    
    # Test document simplification
    simplified = await analyzer.simplify_document(test_content)
    assert simplified is not None
    assert isinstance(simplified, str)
    
    # Test risk analysis
    risks = await analyzer.analyze_risks(test_content)
    assert risks is not None
    assert isinstance(risks, dict)
    assert "risks" in risks
    assert "recommendations" in risks
    
    # Test key terms extraction
    terms = await analyzer.extract_key_terms(test_content)
    assert terms is not None
    assert isinstance(terms, list)
    assert len(terms) > 0
    assert all(isinstance(term, dict) for term in terms)

@pytest.mark.asyncio
async def test_document_api_endpoints(client: AsyncClient, test_user: dict):
    # Login user
    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test document upload and analysis
    test_file_content = b"This is a test legal document."
    files = {"file": ("test.txt", test_file_content, "text/plain")}
    response = await client.post(
        "/api/v1/documents/analyze",
        files=files,
        headers=headers,
        params={"target_language": "en"}
    )
    assert response.status_code == 200
    result = response.json()
    assert "simplified_content" in result
    assert "key_terms" in result
    assert "risks" in result
    
    # Test document generation
    template_data = {
        "template_name": "nda_template",
        "data": {
            "party_a": "Company A",
            "party_b": "Company B",
            "effective_date": "2025-03-28"
        },
        "language": "en",
        "output_format": "docx"
    }
    response = await client.post(
        "/api/v1/templates/generate",
        json=template_data,
        headers=headers
    )
    assert response.status_code == 200
    result = response.json()
    assert "task_id" in result
    assert result["status"] == "processing"
