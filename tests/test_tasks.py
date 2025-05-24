from app import db  # Добавляем импорт db
from models import Task  # Импорт модели Task
from datetime import timedelta

def test_get_tasks(client, test_user):
    """Тест получения списка заданий"""
    # Сначала создаем тестовое задание
    with client.application.app_context():
        from models import Task
        from datetime import timedelta
        task = Task(
            task_text="Тестовое задание",
            task_type="custom",
            reward_exp=10,
            reward_coins=5,
            penalty=3,
            cooldown=timedelta(hours=1),
            creator_id=test_user.user_id
        )
        db.session.add(task)
        db.session.commit()
    
    response = client.get(f'/api/tasks?telegram_id={test_user.telegram_id}')
    assert response.status_code == 200
    tasks = response.json
    assert isinstance(tasks, list)
    assert any(t['text'] == "Тестовое задание" for t in tasks)

def test_complete_task(client, test_user):
    """Тест выполнения задания"""
    # Создаем тестовое задание
    with client.application.app_context():
        from models import Task
        task = Task(
            task_text="Задание для выполнения",
            task_type="custom",
            reward_exp=15,
            reward_coins=8,
            penalty=5,
            cooldown=timedelta(hours=1),
            creator_id=test_user.user_id
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.task_id
    
    # Выполняем задание
    response = client.post('/api/tasks/complete', json={
        'telegram_id': test_user.telegram_id,
        'task_id': task_id
    })
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['coins'] == 8  # Проверяем начисление монет

def test_create_task(client, test_user):
    """Тест создания нового задания"""
    new_task = {
        'telegram_id': test_user.telegram_id,
        'task_text': 'Новое кастомное задание',
        'task_type': 'custom',
        'reward_exp': 12,
        'reward_coins': 6,
        'penalty': 2,
        'cooldown_hours': 2
    }
    
    response = client.post('/api/tasks/create', json=new_task)
    assert response.status_code == 201
    assert 'task_id' in response.json
    
    # Проверяем, что задание создалось
    with client.application.app_context():
        from models import Task
        task = Task.query.get(response.json['task_id'])
        assert task is not None
        assert task.task_text == new_task['task_text']