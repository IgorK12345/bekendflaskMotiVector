from flask import Flask, request, jsonify
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
from database import init_db, db
from models import (
    User, UserStats, Product, ProductBuff, 
    UserInventory, Guild, GuildMembership,
    FriendsGuild, Task, TaskHistory, GuildTask
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'  # Замените на реальный секретный ключ
jwt = JWTManager(app)

# Инициализация БД
init_db(app)

# ====================== Аутентификация ======================

@app.route('/api/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя.
    Принимает: name, password, sex (опционально)
    Возвращает: access_token
    """
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    
    new_user = User(
        name=data['name'],
        sex=data.get('sex'),
        password=hashed_password
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Создаем связанные записи
        db.session.add(UserStats(user_id=new_user.user_id))
        db.session.add(UserInventory(user_id=new_user.user_id))
        db.session.commit()
        
        access_token = create_access_token(identity=new_user.user_id)
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """
    Аутентификация пользователя.
    Принимает: name, password
    Возвращает: access_token и user_id
    """
    data = request.get_json()
    user = User.query.filter_by(name=data['name']).first()
    
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.user_id)
        return jsonify({
            'access_token': access_token,
            'user_id': user.user_id
        })
    return jsonify({'error': 'Invalid credentials'}), 401

# ====================== Пользователи ======================

@app.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Получение информации о пользователе.
    Возвращает: user_id, name, level
    """
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.user_id,
        'name': user.name,
        'level': user.stats.level if user.stats else 1
    })

@app.route('/api/users/<int:user_id>/stats', methods=['GET', 'PUT'])
@jwt_required()
def user_stats(user_id):
    """
    Получение/обновление статистики пользователя.
    GET: Возвращает health, mana, level, money
    PUT: Обновляет health, mana, money (только для текущего пользователя)
    """
    if request.method == 'GET':
        stats = UserStats.query.get_or_404(user_id)
        return jsonify({
            'health': stats.health_points,
            'mana': stats.mana,
            'level': stats.level,
            'money': stats.money
        })
    
    elif request.method == 'PUT':
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        stats = UserStats.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'health' in data:
            stats.health_points = data['health']
        if 'mana' in data:
            stats.mana = data['mana']
        if 'money' in data:
            stats.money = data['money']
            
        db.session.commit()
        return jsonify({'message': 'Stats updated'})

# ====================== Магазин и инвентарь ======================

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Получение списка всех товаров.
    Возвращает: id, name, price, category для каждого товара
    """
    products = Product.query.all()
    return jsonify([{
        'id': p.product_id,
        'name': p.product_name,
        'price': p.price,
        'category': p.category
    } for p in products])

@app.route('/api/products/<int:product_id>/buy', methods=['POST'])
@jwt_required()
def buy_product(product_id):
    """
    Покупка товара пользователем.
    Возвращает: сообщение об успехе/ошибке
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    product = Product.query.get_or_404(product_id)
    
    if user.stats.money < product.price:
        return jsonify({'error': 'Not enough money'}), 400
    
    try:
        new_item = UserInventory(
            user_id=user_id,
            product_id=product_id,
            is_equipped=False
        )
        
        user.stats.money -= product.price
        
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Product purchased'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ====================== Задания ======================

@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """
    Получение списка доступных заданий.
    Возвращает: id, title, reward, difficulty, is_completed, can_repeat
    """
    user_id = get_jwt_identity()
    
    # Получаем ID выполненных пользователем заданий
    completed_tasks = [th.task_id for th in 
                      TaskHistory.query.filter_by(user_id=user_id).all()]
    
    tasks = Task.query.filter(
        or_(
            Task.created_by == None,  # Системные задания
            Task.created_by == user_id  # Созданные текущим пользователем
        )
    ).all()
    
    response = []
    for task in tasks:
        completed = task.task_id in completed_tasks
        response.append({
            'id': task.task_id,
            'title': task.title,
            'reward': task.base_reward,
            'difficulty': task.difficulty,
            'is_completed': completed,
            'can_repeat': task.is_repeatable and not completed
        })
    
    return jsonify(response)

@app.route('/api/tasks/complete', methods=['POST'])
@jwt_required()
def complete_task():
    """
    Завершение задания пользователем.
    Принимает: task_id
    Возвращает: сообщение об успехе/ошибке
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    task = Task.query.get_or_404(data['task_id'])
    user = User.query.get_or_404(user_id)
    
    # Проверка на повторное выполнение
    if not task.is_repeatable:
        last_completion = TaskHistory.query.filter_by(
            task_id=task.task_id,
            user_id=user_id
        ).first()
        
        if last_completion:
            return jsonify({'error': 'Task already completed'}), 400
    
    # Проверка cooldown для повторяемых заданий
    if task.is_repeatable and task.cooldown_hours:
        last_completion = TaskHistory.query.filter_by(
            task_id=task.task_id,
            user_id=user_id
        ).order_by(TaskHistory.completed_at.desc()).first()
        
        if last_completion and (datetime.utcnow() - last_completion.completed_at) < timedelta(hours=task.cooldown_hours):
            return jsonify({'error': f'Task on cooldown. Try again later'}), 400
    
    try:
        # Запись в историю
        history_entry = TaskHistory(
            task_id=task.task_id,
            user_id=user_id,
            reward_earned=task.base_reward,
            completed_at=datetime.utcnow()
        )
        
        # Начисление награды
        user.stats.money += task.base_reward
        user.stats.experience += task.base_reward * 10
        
        db.session.add(history_entry)
        db.session.commit()
        
        return jsonify({'message': 'Task completed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ====================== Гильдии ======================

@app.route('/api/guilds', methods=['GET', 'POST'])
@jwt_required()
def guilds():
    """
    Управление гильдиями.
    GET: Список всех гильдий (id, name, members_count)
    POST: Создание новой гильдии (name, description)
    """
    if request.method == 'GET':
        guilds = Guild.query.all()
        return jsonify([{
            'id': g.guild_id,
            'name': g.name,
            'members_count': len(g.members)
        } for g in guilds])
    
    elif request.method == 'POST':
        user_id = get_jwt_identity()
        data = request.get_json()
        
        try:
            new_guild = Guild(
                name=data['name'],
                description=data.get('description')
            )
            db.session.add(new_guild)
            db.session.flush()
            
            # Создателя делаем лидером
            db.session.add(GuildMembership(
                guild_id=new_guild.guild_id,
                user_id=user_id,
                role='leader'
            ))
            
            db.session.commit()
            return jsonify({'guild_id': new_guild.guild_id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

# ====================== Запуск приложения ======================

if __name__ == '__main__':
    with app.app_context():
        # Удаляем и пересоздаем таблицы
        db.reflect()
        db.drop_all()  # Удаляем без параметров
        db.create_all()
        
        # Тестовые данные
        if not User.query.first():
            hashed_password = generate_password_hash('admin123')
            test_user = User(name="admin", password=hashed_password)
            db.session.add(test_user)
            db.session.commit()
    
    app.run(debug=True)