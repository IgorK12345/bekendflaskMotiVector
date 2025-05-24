from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import User, Item, Task, UserInventory, Clan, ClanMember, Friendship, FriendRequest, FavoriteTask, CompletedTask
from database import db
import os
from dotenv import load_dotenv

# Инициализация приложения
load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Создаем таблицы при первом запуске
with app.app_context():
    db.create_all()

# Вспомогательные функции
def get_current_user(telegram_id):
    return User.query.filter_by(telegram_id=telegram_id).first_or_404()

# API Endpoints

# 1. Аутентификация и пользователь
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(telegram_id=data['telegram_id']).first():
        return jsonify({"error": "User already exists"}), 400
    
    new_user = User(
        telegram_id=data['telegram_id'],
        nickname=data['nickname']
    )
    db.session.add(new_user)
    db.session.commit()
    
    # Добавляем дефолтные задания
    default_tasks = [
        Task(task_text="Пить воду", reward_exp=10, reward_coins=5, penalty=3, 
             cooldown=timedelta(hours=1), is_default=True, creator_id=new_user.user_id),
        # ... другие дефолтные задания
    ]
    db.session.add_all(default_tasks)
    db.session.commit()
    
    return jsonify({"user_id": new_user.user_id}), 201

@app.route('/api/user/<telegram_id>', methods=['GET'])
def get_user(telegram_id):
    user = get_current_user(telegram_id)
    return jsonify({
        "nickname": user.nickname,
        "level": user.level,
        "coins": user.coins,
        "hp": f"{user.hp}/{user.max_hp}"
    })

# 2. Система заданий
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    telegram_id = request.args.get('telegram_id')
    user = get_current_user(telegram_id)
    
    # Получаем все задания пользователя (личные + клановые если есть)
    tasks = Task.query.filter(
        (Task.creator_id == user.user_id) | 
        (Task.clan_id == user.clan_membership.clan_id if user.clan_membership else False)
    ).all()
    
    return jsonify([{
        "id": task.task_id,
        "text": task.task_text,
        "type": task.task_type,
        "rewards": {"exp": task.reward_exp, "coins": task.reward_coins},
        "penalty": task.penalty,
        "cooldown": str(task.cooldown)
    } for task in tasks])

@app.route('/api/tasks/complete', methods=['POST'])
def complete_task():
    data = request.get_json()
    user = get_current_user(data['telegram_id'])
    task = Task.query.get_or_404(data['task_id'])
    
    # Проверка что задание принадлежит пользователю или его клану
    if task.creator_id != user.user_id and (
        not user.clan_membership or task.clan_id != user.clan_membership.clan_id
    ):
        return jsonify({"error": "Not your task"}), 403
    
    # Начисляем награды
    user.exp += task.reward_exp
    user.coins += task.reward_coins
    
    # Проверка на повышение уровня
    if user.exp >= user.level * 100:  # Пример формулы
        user.level += 1
        user.max_hp += 10
    
    # Записываем выполнение
    completion = CompletedTask(
        user_id=user.user_id,
        task_id=task.task_id,
        next_available=datetime.utcnow() + task.cooldown
    )
    db.session.add(completion)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "new_level": user.level,
        "coins": user.coins,
        "exp": user.exp
    })

# 3. Магазин и инвентарь
@app.route('/api/shop', methods=['GET'])
def get_shop():
    items = Item.query.all()
    return jsonify([{
        "id": item.item_id,
        "name": item.name,
        "price": item.base_price,
        "type": item.item_type
    } for item in items])

@app.route('/api/shop/buy', methods=['POST'])
def buy_item():
    data = request.get_json()
    user = get_current_user(data['telegram_id'])
    item = Item.query.get_or_404(data['item_id'])
    
    if user.coins < item.base_price:
        return jsonify({"error": "Not enough coins"}), 400
    
    # Для зелий - мгновенное применение
    if item.item_type == 'potion':
        if item.effect_type == 'hp_restore':
            user.hp = min(user.hp + item.effect_value, user.max_hp)
        elif item.effect_type == 'shield':
            user.shield_expires_at = datetime.utcnow() + timedelta(hours=item.effect_value)
    else:
        # Добавляем в инвентарь
        inventory = UserInventory(
            user_id=user.user_id,
            item_id=item.item_id,
            purchase_price=item.base_price
        )
        db.session.add(inventory)
    
    user.coins -= item.base_price
    db.session.commit()
    
    return jsonify({"success": True, "coins_left": user.coins})

# 4. Кланы
@app.route('/api/clans/create', methods=['POST'])
def create_clan():
    data = request.get_json()
    user = get_current_user(data['telegram_id'])
    
    if user.clan_membership:
        return jsonify({"error": "Already in a clan"}), 400
    
    if user.coins < 500:
        return jsonify({"error": "Not enough coins"}), 400
    
    new_clan = Clan(
        name=data['name'],
        creator_id=user.user_id
    )
    db.session.add(new_clan)
    
    membership = ClanMember(
        clan_id=new_clan.clan_id,
        user_id=user.user_id,
        is_leader=True
    )
    db.session.add(membership)
    
    user.coins -= 500
    db.session.commit()
    
    return jsonify({"clan_id": new_clan.clan_id}), 201

# 5. Друзья
@app.route('/api/friends/add', methods=['POST'])
def add_friend():
    data = request.get_json()
    from_user = get_current_user(data['telegram_id'])
    to_user = User.query.filter_by(telegram_id=data['friend_telegram_id']).first_or_404()
    
    if from_user.user_id == to_user.user_id:
        return jsonify({"error": "Cannot add yourself"}), 400
    
    # Проверяем нет ли уже дружбы или заявки
    existing = FriendRequest.query.filter(
        ((FriendRequest.from_user_id == from_user.user_id) & 
         (FriendRequest.to_user_id == to_user.user_id)) |
        ((FriendRequest.from_user_id == to_user.user_id) & 
         (FriendRequest.to_user_id == from_user.user_id))
    ).first()
    
    if existing:
        return jsonify({"error": "Request already exists"}), 400
    
    request = FriendRequest(
        from_user_id=from_user.user_id,
        to_user_id=to_user.user_id
    )
    db.session.add(request)
    db.session.commit()
    
    return jsonify({"success": True})

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)