# import pytest
# from rest_framework.test import APIClient
# from django.urls import reverse
# from django.http import JsonResponse
# import psycopg2

# @pytest.fixture
# def api_client():
#   return APIClient()

# @pytest.fixture
# def setup_test_database(monkeypatch: pytest.MonkeyPatch):
  
#     def mock_get_db_connection():
#         class MockCursor:
#             def execute(self, query, parms):
#                 if parms == ('cyndia',):
#                     self.data = [(1,'cyndia','halfoun','cyndia@example.com')]
#                 else:
#                     self.data = []
#             def fetchall(self):
#                 return self.data
#             def close(self):
#                 pass
#         class MockConnection:
#             def cursor(self):
#                 return MockCursor()
#             def close(self):
#                 pass
#         return MockConnection()
    
#     monkeypatch.setattr('your_app.views.get_db_connection', mock_get_db_connection)

# @pytest.mark.django_db
# def test_search_user_found(api_client, setup_test_database):
#     response = api_client.get(reverse('Search_user'),{'first_name':'cyndia'})
#     assert response.status_code == 200
#     assert response.json() == [
#         {'id': 1,
#         'fist_name':'cyndia',
#         'last_name':'halfoun',
#         'email':'cyndia@example.com'}
#     ]

# @pytest.mark.django_db
# def test_search_user_not_found(api_client,setup_test_database):
#     response = api_client.get(reverse('Search_user'),{'first_name':'bob'})
#     assert response.status_code == 404
#     assert response.json() == {'message':'utilisateur introuvable.'}

# @pytest.mark.django_db
# def test_search_user_no_first_name(api_client):
#     response = api_client.get(reverse('Search_user'))
#     assert response.status_code == 400
#     assert response.json() == {'error':'le nom est requis.'}