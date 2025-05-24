from datetime import datetime
from database import db

class User(db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    exp = db.Column(db.Integer, default=0, nullable=False)
    coins = db.Column(db.Integer, default=0, nullable=False)
    hp = db.Column(db.Integer, default=100, nullable=False)
    max_hp = db.Column(db.Integer, default=100, nullable=False)
    shield_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    inventory_items = db.relationship('UserInventory', back_populates='user')
    created_tasks = db.relationship('Task', back_populates='creator')
    favorite_tasks = db.relationship('FavoriteTask', back_populates='user')
    clan_membership = db.relationship('ClanMember', back_populates='user', uselist=False)
    sent_friend_requests = db.relationship('FriendRequest', foreign_keys='FriendRequest.from_user_id', back_populates='from_user')
    received_friend_requests = db.relationship('FriendRequest', foreign_keys='FriendRequest.to_user_id', back_populates='to_user')
    friendships1 = db.relationship('Friendship', foreign_keys='Friendship.user1_id', back_populates='user1')
    friendships2 = db.relationship('Friendship', foreign_keys='Friendship.user2_id', back_populates='user2')


class Item(db.Model):
    """Модель предмета в магазине"""
    __tablename__ = 'items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    item_type = db.Column(db.String(20), nullable=False)  # 'headgear', 'clothing', 'pet', 'potion'
    slot = db.Column(db.String(20))  # 'head', 'body', 'legs', 'pet'
    base_price = db.Column(db.Integer, nullable=False)
    effect_type = db.Column(db.String(30))
    effect_value = db.Column(db.Numeric(5, 2))
    is_unique = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    owned_by = db.relationship('UserInventory', back_populates='item')


class UserInventory(db.Model):
    """Модель инвентаря пользователя"""
    __tablename__ = 'user_inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    equipped_slot = db.Column(db.String(20))
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_price = db.Column(db.Integer, nullable=False)

    # Связи
    user = db.relationship('User', back_populates='inventory_items')
    item = db.relationship('Item', back_populates='owned_by')


class Task(db.Model):
    """Модель задания"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    clan_id = db.Column(db.Integer, db.ForeignKey('clans.clan_id'))
    task_text = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.String(10), nullable=False)  # 'custom', 'clan'
    reward_exp = db.Column(db.Integer, nullable=False)
    reward_coins = db.Column(db.Integer, nullable=False)
    penalty = db.Column(db.Integer, nullable=False)
    cooldown = db.Column(db.Interval, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    creator = db.relationship('User', back_populates='created_tasks')
    clan = db.relationship('Clan', back_populates='tasks')
    favorited_by = db.relationship('FavoriteTask', back_populates='task')
    completions = db.relationship('CompletedTask', back_populates='task')


class CompletedTask(db.Model):
    """Модель выполненного задания"""
    __tablename__ = 'completed_tasks'
    
    completion_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_available = db.Column(db.DateTime, nullable=False)

    # Связи
    user = db.relationship('User')
    task = db.relationship('Task', back_populates='completions')


class FavoriteTask(db.Model):
    """Модель избранных заданий"""
    __tablename__ = 'favorite_tasks'
    
    favorite_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    # Связи
    user = db.relationship('User', back_populates='favorite_tasks')
    task = db.relationship('Task', back_populates='favorited_by')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'task_id', name='unique_user_task'),
        db.UniqueConstraint('user_id', 'position', name='unique_user_position'),
        db.CheckConstraint('position BETWEEN 1 AND 4', name='position_range')
    )


class Clan(db.Model):
    """Модель клана"""
    __tablename__ = 'clans'
    
    clan_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    creator = db.relationship('User')
    members = db.relationship('ClanMember', back_populates='clan')
    tasks = db.relationship('Task', back_populates='clan')
    join_requests = db.relationship('ClanRequest', back_populates='clan')


class ClanMember(db.Model):
    """Модель участника клана"""
    __tablename__ = 'clan_members'
    
    membership_id = db.Column(db.Integer, primary_key=True)
    clan_id = db.Column(db.Integer, db.ForeignKey('clans.clan_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_leader = db.Column(db.Boolean, default=False)

    # Связи
    clan = db.relationship('Clan', back_populates='members')
    user = db.relationship('User', back_populates='clan_membership')

    __table_args__ = (
        db.UniqueConstraint('user_id', name='unique_user_clan'),
    )


class ClanRequest(db.Model):
    """Модель заявки в клан"""
    __tablename__ = 'clan_requests'
    
    request_id = db.Column(db.Integer, primary_key=True)
    clan_id = db.Column(db.Integer, db.ForeignKey('clans.clan_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    # Связи
    clan = db.relationship('Clan', back_populates='join_requests')
    user = db.relationship('User')


class Friendship(db.Model):
    """Модель дружеских связей"""
    __tablename__ = 'friendships'
    
    friendship_id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    user1 = db.relationship('User', foreign_keys=[user1_id], back_populates='friendships1')
    user2 = db.relationship('User', foreign_keys=[user2_id], back_populates='friendships2')

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_friendship'),
        db.CheckConstraint('user1_id < user2_id', name='check_user_order')
    )


class FriendRequest(db.Model):
    """Модель заявки в друзья"""
    __tablename__ = 'friend_requests'
    
    request_id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    # Связи
    from_user = db.relationship('User', foreign_keys=[from_user_id], back_populates='sent_friend_requests')
    to_user = db.relationship('User', foreign_keys=[to_user_id], back_populates='received_friend_requests')

    __table_args__ = (
        db.CheckConstraint('from_user_id != to_user_id', name='check_not_self'),
    )