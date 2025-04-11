import pytest



pytestmark = pytest.mark.django_db

class TestCategoryModel:
    def test_str_method(self, category_factory):
        # Arrange (preparación)
        x = category_factory(name="test_cat")
        
        # Act (ejecución) y Assert (verificación)
        assert x.__str__()== "test_cat"
        # assert obj.name == "Electronics"
        # assert obj.parent is None  # Probando valor por defecto

@pytest.mark.django_db
class TestBrandModel:
    def test_str_method(self, brand_factory):
        # Arrange (preparación)
        obj = brand_factory(name="test_brand")
        # Act (ejecución) y Assert (verificación)
        assert obj.__str__() == "test_brand"

@pytest.mark.django_db
class TestProductModel:
    def test_str_method(self, product_factory):
        # Arrange (preparación)
        obj = product_factory(name="test_product")
        # Act (ejecución) y Assert (verificación)
        assert obj.__str__() == "test_product"