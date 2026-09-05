from backend.schemas.auth import RegisterIn

def test_register_schema():
    item = RegisterIn(username='fenix_test', password='secret123', display_name='Fenix')
    assert item.username == 'fenix_test'
