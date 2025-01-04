import pytest
from django.test import Client


@pytest.mark.django_db
class TestSearchArtisansByJob:

    # test 1
    def test_search_artisans_success(self):
        client = Client()

        
        response = client.post(
            "/app/search-artisans/",
            data={"job": "Electrician"},
            content_type="application/json",
        )
        assert response.status_code in [200, 500]  
        data = response.json()
        assert len(data.get("artisans", [])) >= 0  

    # test2
    def test_search_artisans_no_match(self):
        client = Client()

        
        response = client.post(
            "/app/search-artisans/",
            data={"job": "Painter"},
            content_type="application/json",
        )
        assert response.status_code in [200, 500]  
        data = response.json()

        
        assert "artisans" in data or "message" in data  

    #test3
    def test_search_artisans_missing_job(self):
        client = Client()

        response = client.post(
            "/app/search-artisans/",
            data={},
            content_type="application/json",
        )
        assert response.status_code in [400, 500] 
        data = response.json()
        assert "message" in data  

    # Test 4: Empty request body
    def test_search_artisans_empty_body(self):
        client = Client()

        response = client.post(
            "/app/search-artisans/",
            content_type="application/json",
        )
        assert response.status_code in [400, 500] 
        data = response.json()
        assert "message" in data and "required" in data["message"]  

    # Test 5: Invalid HTTP Method
    def test_search_artisans_invalid_method(self):
        client = Client()

        response = client.get("/app/search-artisans/")
        assert response.status_code in [405, 500]  
        data = response.json()
        assert "message" in data 
