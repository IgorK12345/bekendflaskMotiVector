from datetime import datetime
from database import db

class User(db.Model):
    """Таблица пользователей"""
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    sex = db.Column(db.String(1))  # 'M' или 'W'
    registr_date = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String(255), nullable=False)
    
    # Связи
    stats = db.relationship('UserStats', back_populates='user', uselist=False, cascade='all, delete-orphan')
    inventory_items = db.relationship('UserInventory', back_populates='user', cascade='all, delete-orphan')
    created_tasks = db.relationship('Task', back_populates='creator', foreign_keys='Task.created_by')
    completed_tasks = db.relationship('TaskHistory', back_populates='user', foreign_keys='TaskHistory.user_id')
    guild_memberships = db.relationship('GuildMembership', back_populates='user', cascade='all, delete-orphan')
    friends_initiated = db.relationship('FriendsGuild', back_populates='user', foreign_keys='FriendsGuild.user_id')
    friends_received = db.relationship('FriendsGuild', back_populates='friend', foreign_keys='FriendsGuild.friend_id')

class UserStats(db.Model):
    """Показатели пользователя"""
    __tablename__ = 'users_stats'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    health_points = db.Column(db.Integer, default=100)
    mana = db.Column(db.Integer, default=50)
    max_health_points = db.Column(db.Integer, default=100)
    max_mana = db.Column(db.Integer, default=50)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    money = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='stats')

class Product(db.Model):
    """Товары магазина"""
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    
    buff = db.relationship('ProductBuff', back_populates='product', uselist=False, cascade='all, delete-orphan')
    inventory_items = db.relationship('UserInventory', back_populates='product')

class ProductBuff(db.Model):
    """Бафы товаров"""
    __tablename__ = 'products_buffs'
    
    buff_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    buff_type = db.Column(db.String(50), nullable=False)
    buff_value = db.Column(db.Integer, nullable=False)
    buff_duration = db.Column(db.Integer)  # в минутах (None для постоянных)
    
    product = db.relationship('Product', back_populates='buff')

class UserInventory(db.Model):
    """Инвентарь пользователя"""
    __tablename__ = 'users_inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    acquire_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='inventory_items')
    product = db.relationship('Product', back_populates='inventory_items')

class Guild(db.Model):
    """Гильдии"""
    __tablename__ = 'guilds'
    
    guild_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logo_url = db.Column(db.String(255))
    
    members = db.relationship('GuildMembership', back_populates='guild', cascade='all, delete-orphan')
    tasks = db.relationship('GuildTask', back_populates='guild', cascade='all, delete-orphan')

class GuildMembership(db.Model):
    """Участники гильдий"""
    __tablename__ = 'guilds_membership'
    
    membership_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), default='member', nullable=False)  # 'leader', 'officer', 'member'
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    guild = db.relationship('Guild', back_populates='members')
    user = db.relationship('User', back_populates='guild_memberships')

class FriendsGuild(db.Model):
    """Друзья и гильдии пользователя"""
    __tablename__ = 'friends_guilds'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id', ondelete='CASCADE'))
    status = db.Column(db.String(20), nullable=False)  # 'friend', 'guild_member'
    
    user = db.relationship('User', foreign_keys=[user_id], back_populates='friends_initiated')
    friend = db.relationship('User', foreign_keys=[friend_id], back_populates='friends_received')
    guild = db.relationship('Guild')

class Task(db.Model):
    """Задания"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(50), nullable=False)  # 'easy', 'medium', 'hard'
    category = db.Column(db.String(100))  # 'study', 'sport', etc
    base_reward = db.Column(db.Integer, nullable=False)
    is_repeatable = db.Column(db.Boolean, default=False)
    cooldown_hours = db.Column(db.Integer)  # None для одноразовых
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    
    creator = db.relationship('User', back_populates='created_tasks', foreign_keys=[created_by])
    completions = db.relationship('TaskHistory', back_populates='task', cascade='all, delete-orphan')
    guild_tasks = db.relationship('GuildTask', back_populates='task', cascade='all, delete-orphan')

class TaskHistory(db.Model):
    """История выполнения заданий"""
    __tablename__ = 'tasks_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reward_earned = db.Column(db.Integer, nullable=False)
    
    task = db.relationship('Task', back_populates='completions')
    user = db.relationship('User', back_populates='completed_tasks')

class GuildTask(db.Model):
    """Гильдейские задания"""
    __tablename__ = 'guilds_tasks'
    
    guild_task_id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.guild_id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id', ondelete='CASCADE'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    guild = db.relationship('Guild', back_populates='tasks')
    task = db.relationship('Task', back_populates='guild_tasks')