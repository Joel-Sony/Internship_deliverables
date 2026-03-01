from flask import Flask, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from config import Config
from extensions import db, jwt
from data.models import User, Note, Category, Tag
from services import (
    create_note,
    get_user_notes,
    update_user_note,
    delete_user_note
)
from flask_migrate import Migrate
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(Config)
migrate = Migrate(app, db)

db.init_app(app)
jwt.init_app(app)


@app.route("/")
def home():
    return {"message": "Flask API is working!"}


# -------------------------
# AUTH ROUTES
# -------------------------

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(username=data.get("username")).first()

    if not user or not user.check_password(data.get("password")):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({"access_token": access_token}), 200


# -------------------------
# NOTE ROUTES (PROTECTED)
# -------------------------
@app.route("/notes", methods=["GET"])
@jwt_required()
def get_notes_route():
    user_id = int(get_jwt_identity())

    category_id = request.args.get("category", type=int)
    tag_name = request.args.get("tag")
    search = request.args.get("search")

    notes = get_user_notes(user_id,category_id,tag_name,search) 

    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "category": n.category.name if n.category else None,
            "tags": [t.name for t in n.tags],
            "created_at": n.created_at,
            "updated_at": n.updated_at
        }
        for n in notes
    ]), 200

@app.route("/notes", methods=["POST"])
@jwt_required()
def create_note_route():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    title = data.get("title")
    content = data.get("content")
    category_id = data.get("category_id")
    tags = data.get("tags")  # should be list

    if not title or not content:
        return jsonify({"error": "Title and content required"}), 400

    note = create_note(
        title=title,
        content=content,
        user_id=user_id,
        category_id=category_id,
        tag_names=tags
    )

    return jsonify({
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "category": note.category.name if note.category else None,
        "tags": [t.name for t in note.tags]
    }), 201


@app.route("/notes/<int:note_id>", methods=["GET"])
@jwt_required()
def get_note_route(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    return jsonify({
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "category": note.category.name if note.category else None,
        "tags": [t.name for t in note.tags]
    }), 200


@app.route("/notes/<int:note_id>", methods=["PUT"])
@jwt_required()
def update_note_route(note_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    category_id = data.get("category_id")
    tags = data.get("tags")  # should be list

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    updated = update_user_note(user_id, note, data.get("title"), data.get("content"), category_id, tags)

    return jsonify({
        "id": updated.id,
        "title": updated.title,
        "content": updated.content
    }), 200


@app.route("/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note_route(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    delete_user_note(note)

    return jsonify({"message": "Note deleted"}), 200

@app.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get("name"):
        return {"error": "Category name required"}, 400

    category = Category(name=data["name"], user_id=user_id)

    db.session.add(category)
    db.session.commit()

    return {
        "id": category.id,
        "name": category.name
    }, 201

@app.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    user_id = int(get_jwt_identity())

    categories = Category.query.filter_by(user_id=user_id).all()

    return [
        {"id": c.id, "name": c.name}
        for c in categories
    ], 200

if __name__ == "__main__":
    app.run(debug=True)