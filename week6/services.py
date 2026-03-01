from extensions import db
from data.models import Note

def create_note(title, content, user_id):
    note = Note(title=title, content=content, user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return note

def get_user_notes(user_id):
    return Note.query.filter_by(user_id=user_id).all()

def get_user_note_by_id(note_id, user_id):
    return Note.query.filter_by(id=note_id, user_id=user_id).first()

def update_user_note(note, title=None, content=None):
    if title:
        note.title = title
    if content:
        note.content = content
    db.session.commit()
    return note

def delete_user_note(note):
    db.session.delete(note)
    db.session.commit()