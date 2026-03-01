from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


note_tags = db.Table(
    "note_tags",
    db.Column("note_id", db.Integer, db.ForeignKey("note.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True)
    
)

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    notes = db.relationship(
        "Note",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    categories = db.relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    tags = db.relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
class Note(db.Model):
    __tablename__ = "note"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="notes")

    # One-to-Many
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", back_populates="notes")

    # Many-to-Many
    tags = db.relationship(
        "Tag",
        secondary=note_tags,
        back_populates="notes"
    )
class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="categories")

    notes = db.relationship(
        "Note",
        back_populates="category",
        cascade="all, delete"
    )

class Tag(db.Model):
    __tablename__ = "tag"

    __table_args__ = (
        db.UniqueConstraint("name", "user_id", name="unique_tag_per_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="tags")

    notes = db.relationship(
        "Note",
        secondary=note_tags,
        back_populates="tags"
    )