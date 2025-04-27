from datetime import datetime
from database import db

class User(db.Model):
    """Таблица пользователей"""
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.String(1))  # 'M' или 'W'
    registr_date = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String(255), nullable=False)
    
    # Обновленные связи
    stats = db.relationship('UserStats', backref='user', uselist=False)
    inventory = db.relationship('UserInventory', backref='user', uselist=False)
    created_tasks = db.relationship('Task', backref='creator', foreign_keys='Task.created_by')
    completed_tasks_history = db.relationship('TaskHistory', backref='user', foreign_keys='TaskHistory.user_id')
    
    # Удалите старую связь friends, так как мы перенесли её в FriendsGuild

class UserStats(db.Model):
    """Показатели пользователя"""
    __tablename__ = 'usersstats'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    health_points = db.Column(db.Integer, default=100)
    mana = db.Column(db.Integer, default=50)
    max_health_points = db.Column(db.Integer, default=100)
    max_mana = db.Column(db.Integer, default=50)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    money = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    """Товары магазина"""
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255))
    price = db.Column(db.Integer)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    
    # Связь с бафами
    buffs = db.relationship('ProductBuff', backref='product', uselist=False)

class ProductBuff(db.Model):
    """Бафы товаров"""
    __tablename__ = 'productbuffs'
    
    buff_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'))
    buff_type = db.Column(db.String(50))  # 'hp', 'mana', 'speed' и т.д.
    buff_value = db.Column(db.Integer)
    buff_duration = db.Column(db.Integer)  # в минутах (None для постоянных)

class UserInventory(db.Model):
    """Инвентарь пользователя"""
    __tablename__ = 'userinventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'))
    is_equipped = db.Column(db.Boolean, default=False)
    acquire_date = db.Column(db.DateTime, default=datetime.utcnow)

class Guild(db.Model):
    """Гильдии"""
    __tablename__ = 'guilds'
    
    guild_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logo_url = db.Column(db.String(255))
    
    # Связи
    members = db.relationship('GuildMembership', backref='guild')
    tasks = db.relationship('GuildTask', backref='guild')

class GuildMembership(db.Model):
    """Участники гильдий"""
    __tablename__ = 'guildmembership'
    
    membership_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    role = db.Column(db.String(50), default='member')  # 'leader', 'officer', 'member'
    join_date = db.Column(db.DateTime, default=datetime.utcnow)

class FriendsGuild(db.Model):
    """Друзья и гильдии пользователя"""
    __tablename__ = 'friends'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # Основной пользователь
    friend_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # Друг пользователя
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id'))  # Гильдия
    status = db.Column(db.String(20))  # 'friend', 'guild_member'
    
    # Явно указываем связи
    user = db.relationship('User', foreign_keys=[user_id], backref='friends_as_user')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friends_as_friend')
    guild = db.relationship('Guild', backref='memberships')

class Task(db.Model):
    """Задания"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(50))  # 'easy', 'medium', 'hard'
    category = db.Column(db.String(100))  # 'study', 'sport', etc
    base_reward = db.Column(db.Integer)
    is_repeatable = db.Column(db.Boolean, default=False)
    cooldown_hours = db.Column(db.Integer)  # None для одноразовых
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # None для системных
    
    # Связи
    completions = db.relationship('TaskHistory', backref='task')
    guild_tasks = db.relationship('GuildTask', backref='task')

class TaskHistory(db.Model):
    """История выполнения заданий"""
    __tablename__ = 'task_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    reward_earned = db.Column(db.Integer)  # Может отличаться от base_reward
    
    # Дополнительные поля при необходимости
    # completion_time = db.Column(db.Integer)  # Время выполнения в секундах
    # rating = db.Column(db.Integer)  # Оценка выполнения

class GuildTask(db.Model):
    """Гильдейские задания"""
    __tablename__ = 'guildtasks'
    
    guild_task_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)