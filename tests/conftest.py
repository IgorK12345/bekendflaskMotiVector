import pytest
from app import app as flask_app
from database import db
from models import User, Task
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Фикстура приложения"""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
    yield flask_app
    with flask_app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Фикстура тестового пользователя с заданиями"""
    with app.app_context():
        # Создаем пользователя
        user = User(
            telegram_id='test_user_123',
            nickname='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        # Создаем тестовые задания для пользователя
        tasks = [
            Task(
                task_text="Пить воду",
                task_type="custom",
                reward_exp=10,
                reward_coins=5,
                penalty=3,
                cooldown=timedelta(hours=1),
                creator_id=user.user_id
            ),
            Task(
                task_text="Тестовое задание 1",
                task_type="custom",
                reward_exp=15,
                reward_coins=8,
                penalty=5,
                cooldown=timedelta(hours=2),
                creator_id=user.user_id
            )
        ]
        db.session.add_all(tasks)
        db.session.commit()
        
        yield user
        
        # Очистка после теста
        db.session.delete(user)
        db.session.commit()