from sqlalchemy.orm import Session
from data.models import Student, Mark
from database import SessionLocal

def add_student(db: Session, name: str, marks: list):
    try:
        new_student = Student(name = name)

        for m in marks:
            score = m['score']
            if score >= 90:
                grade = 'A'
            elif score >= 80:
                grade = 'B'
            elif score >= 70:
                grade = 'C'
            elif score >= 60:
                grade = 'D'
            else:
                grade = 'F'
            new_mark = Mark(subject = m['subject'], score = score, grade = grade)
            new_student.marks.append(new_mark)

        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        print(f"\nAdded student: {new_student.name} with ID {new_student.id}")
    except Exception as e:
        db.rollback()
        print(f"\nError adding student: {e}")


def view_records(db: Session):
    try:
        students = db.query(Student).all()
        if not students:
            print("\nNo student records found.")
            return
        for student in students:
            print(f"\nID: {student.id} | Name: {student.name}")
            for mark in student.marks:
                print(f"  - Subject: {mark.subject}, Score: {mark.score}, Grade: {mark.grade}")
    except Exception as e:
        print(f"\nError viewing students: {e}")


def search_student(db: Session, search_type: str, value: str):
    if search_type == 'name' or search_type == 'n':
        students = db.query(Student).filter(Student.name.ilike(f"%{value}%")).all()
    elif search_type == 'grade' or search_type == 'g':
        students = db.query(Student).join(Mark).filter(Mark.grade == value.upper()).all()
    elif search_type == 'id' or search_type == 'i':
        students = db.query(Student).filter(Student.id == int(value)).all()
    else:
        print("Invalid search type. Use 'name', 'grade', or 'id'.")
        return
    if not students:
        print("\nNo matching student records found.")
        return
    for student in students:
        print(f"\nID: {student.id} | Name: {student.name}")
        for mark in student.marks:
            print(f"  - Subject: {mark.subject}, Score: {mark.score}, Grade: {mark.grade}")

def update_student(db: Session, student_id: int, new_name: str = None, new_marks: list = None):
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            print(f"\nStudent with ID {student_id} not found.")
            return
        
        if new_name:
            student.name = new_name
        if new_marks is not None:

            student.marks.clear()
            for m in new_marks:
                score = m['score']
                if score >= 90:
                    grade = 'A'
                elif score >= 80:
                    grade = 'B'
                elif score >= 70:
                    grade = 'C'
                elif score >= 60:
                    grade = 'D'
                else:
                    grade = 'F'
                new_mark = Mark(subject=m['subject'], score=score, grade=grade)
                student.marks.append(new_mark)

        db.commit()
        print(f"\nUpdated student with ID {student_id}.")
    except Exception as e:
        db.rollback()
        print(f"\nError updating student: {e}")

def delete_student(db: Session, student_id: int):
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            print(f"\nStudent with ID {student_id} not found.")
            return
        
        db.delete(student)
        db.commit()
        print(f"\nDeleted student with ID {student_id}.")
    except Exception as e:
        db.rollback()
        print(f"\nError deleting student: {e}")


def export_to_csv(db: Session, filename: str = "exported_students.csv"):
    import csv
    try:
        students = db.query(Student).all()
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Name", "Subject", "Score", "Grade"])
            for student in students:
                for mark in student.marks:
                    writer.writerow([student.id, student.name, mark.subject, mark.score, mark.grade])
        print(f"\nExported records to {filename}.")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")

