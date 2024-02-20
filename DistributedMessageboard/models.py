from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class User(db.Model):
    """Represents a user account."""

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    active = db.Column("is_active", db.Boolean(), nullable=False, server_default="1")
    username = db.Column(
        db.String(100, collation="NOCASE"), nullable=False, unique=True
    )
    messages = db.relationship("ChannelMessage", backref="user", lazy=True)


class Channel(db.Model):
    """Represents a channel in the message board."""

    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column("is_active", db.Boolean(), nullable=False, server_default="1")
    name = db.Column(db.String(100, collation="NOCASE"), nullable=False)


class ChannelMessage(db.Model):
    """Represents a message in a channel."""

    __tablename__ = "channel_messages"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    sender = db.Column(
        db.String(100, collation="NOCASE"),
        db.ForeignKey("users.username"),
        nullable=False,
    )
    timestamp = db.Column(db.DateTime(), nullable=False)
    channel = db.relationship("Channel", backref="channel_messages", lazy=True)
    __table_args__ = (UniqueConstraint("channel_id", "content", "sender", "timestamp"),)
