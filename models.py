from datetime import datetime
from database import db

class User(db.Model):
    """Таблица пользователей"""
    __tablename__ = 'пользователи'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.String(1))  # 'M' или 'W'
    registr_date = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String(255), nullable=False)
    
    # Связи с другими таблицами
    stats = db.relationship('UserStats', backref='user', uselist=False)
    inventory = db.relationship('UserInventory', backref='user', uselist=False)
    tasks = db.relationship('UserTasks', backref='user', uselist=False)
    friends = db.relationship('FriendsGuild', backref='user', uselist=False)

class UserStats(db.Model):
    """Показатели пользователя"""
    __tablename__ = 'показатели_пользователя'
    
    user_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'), primary_key=True)
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
    __tablename__ = 'товары_магазина'
    
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255))
    price = db.Column(db.Integer)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    
    # Связь с бафами
    buffs = db.relationship('ProductBuff', backref='product', uselist=False)

class ProductBuff(db.Model):
    """Бафы товаров"""
    __tablename__ = 'бафы_инвентаря'
    
    buff_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('товары_магазина.product_id'))
    buff_type = db.Column(db.String(50))  # 'hp', 'mana', 'speed' и т.д.
    buff_value = db.Column(db.Integer)
    buff_duration = db.Column(db.Integer)  # в минутах (None для постоянных)

class UserInventory(db.Model):
    """Инвентарь пользователя"""
    __tablename__ = 'инвентарь_пользователя'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('товары_магазина.product_id'))
    is_equipped = db.Column(db.Boolean, default=False)
    acquire_date = db.Column(db.DateTime, default=datetime.utcnow)

class Guild(db.Model):
    """Гильдии"""
    __tablename__ = 'гильдия'
    
    guild_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logo_url = db.Column(db.String(255))
    
    # Связи
    members = db.relationship('GuildMembership', backref='guild')

class GuildMembership(db.Model):
    """Участники гильдий"""
    __tablename__ = 'участники_гильдии'
    
    membership_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('гильдия.guild_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'), unique=True)
    role = db.Column(db.String(50), default='member')  # 'leader', 'officer', 'member'
    join_date = db.Column(db.DateTime, default=datetime.utcnow)

class FriendsGuild(db.Model):
    """Друзья и гильдии пользователя"""
    __tablename__ = 'друзья_гильдия'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))
    guild_id = db.Column(db.Integer, db.ForeignKey('гильдия.guild_id'))
    status = db.Column(db.String(20))  # 'friend', 'guild_member'

class Task(db.Model):
    """Задания"""
    __tablename__ = 'задания'
    
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(50))  # 'easy', 'medium', 'hard'
    category = db.Column(db.String(100))  # 'study', 'sport', etc
    base_reward = db.Column(db.Integer)
    is_repeatable = db.Column(db.Boolean, default=False)
    cooldown_hours = db.Column(db.Integer)  # None для одноразовых
    created_by = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))  # None для системных

class UserTask(db.Model):
    """Задания пользователей"""
    __tablename__ = 'задания_пользователя'
    
    user_task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('задания.task_id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))  # Кто назначил
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

class GuildTask(db.Model):
    """Гильдейские задания"""
    __tablename__ = 'гильдейские_задания'
    
    guild_task_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('гильдия.guild_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('задания.task_id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('пользователи.user_id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)