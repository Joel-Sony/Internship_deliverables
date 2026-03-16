from extensions import db
from data.models import Note, Tag, Category
from sqlalchemy import or_

def create_note(title, content, user_id, category_id=None, tag_names=None):
    note = Note(title=title, content=content, user_id=user_id, category_id=category_id)
    if tag_names:
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name, user_id=user_id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=user_id)
                db.session.add(tag)
            note.tags.append(tag)
    db.session.add(note)
    db.session.commit()
    return note

def get_user_notes(user_id, category_id=None, tag_name=None, search=None):
    query = Note.query.filter_by(user_id=user_id)

    if category_id is not None:
        query = query.filter_by(category_id=category_id)

    if tag_name:
        query = query.join(Note.tags).filter(
            Tag.name == tag_name,
            Tag.user_id == user_id
        ).distinct()

    if search:
        query = query.filter(
            or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%")
            )
        )

    notes = query.all()
    return notes

def update_user_note(user_id, note, title=None, content=None, category_id=None, tag_names=None):
    if title:
        note.title = title
    if content:
        note.content = content
    if category_id is not None:
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if not category:
            raise ValueError("Invalid category")
        note.category = category
    if tag_names is not None:
        # Clear existing tags
        note.tags.clear()
        # Add new tags
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name, user_id=note.user_id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=note.user_id)
                db.session.add(tag)
            note.tags.append(tag)
    db.session.commit()
    return note

def delete_user_note(note):
    db.session.delete(note)
    db.session.commit()