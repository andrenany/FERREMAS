import json
import pytest

pytestmark = pytest.mark.django_db


class TestCategoryEndpoints:
    endpoint = "/api/category/"

    def test_category_get(self, category_factory, api_client):
        # arrange
        category_factory.create_batch(4)
        # act
        response = api_client.get(self.endpoint)
        # assert
        assert response.status_code == 200
        assert len(json.loads(response.content))


class TestBrandEndpoints:
    endpoint = "/api/brand/"

    def test_brand_get(self, brand_factory, api_client):
        # arrange
        brand_factory.create_batch(4)
        # act
        response = api_client.get(self.endpoint)
        # assert
        assert response.status_code == 200
        assert len(json.loads(response.content))


class TestProductEndpoints:
    endpoint = "/api/product/"

    def test_product_get(self, product_factory, api_client):
        # arrange
        product_factory.create_batch(4)
        # act
        response = api_client.get(self.endpoint)
        # assert
        assert response.status_code == 200
        assert len(json.loads(response.content))
