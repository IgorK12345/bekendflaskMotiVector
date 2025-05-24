def test_register(client):
    """Тест регистрации нового пользователя"""
    test_data = {
        'telegram_id': 'test_user_123',
        'nickname': 'Test User'
    }
    
    response = client.post('/api/register', json=test_data)
    assert response.status_code == 201
    assert 'user_id' in response.json
    
    # Проверяем, что создались дефолтные задания
    with client.application.app_context():
        from models import Task
        tasks = Task.query.filter_by(creator_id=response.json['user_id']).all()
        assert len(tasks) == 5  # 5 дефолтных заданий

def test_get_user(client, test_user):
    """Тест получения информации о пользователе"""
    response = client.get(f'/api/user/{test_user.telegram_id}')
    assert response.status_code == 200
    data = response.json
    assert data['nickname'] == test_user.nickname
    assert data['level'] == 1
    assert data['coins'] == 0