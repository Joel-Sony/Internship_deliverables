import sys
from database import SessionLocal, engine
from data.models import Base, Student, Mark
from services import add_student, view_records, search_student, update_student, delete_student, export_to_csv   


def main():
    Base.metadata.create_all(bind=engine)
    
    while True:
        print("\n=== Student Record Management (MySQL) ===")
        print("1. Add New Student & Marks")
        print("2. View All Records")
        print("3. Search Student (Name/Grade/ID)")
        print("4. Update Student Record")
        print("5. Delete Student Record")
        print("6. Export to CSV")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        session = SessionLocal()

        try:
            if choice == '1':
                name = input("\nEnter student name: ")
                marks = []
                while True:
                    subject = input("Enter subject (or 'done' to finish): ")
                    if subject.lower() == 'done':
                        break
                    score = int(input(f"Enter score for {subject}: "))
                    marks.append({'subject': subject, 'score': score})

                add_student(session, name, marks)
                pass 
            elif choice == '2':
                view_records(session)
                pass
            elif choice == '3':
                sub_choice = input("\nSearch by: (n)ame, (g)rade, or (i)d? ").lower()
                value = input("\nEnter search value: ")
                search_student(session, sub_choice, value)
                pass
            elif choice == '4':
                print("\n--- Update Records ---")                
                student_id = int(input("Enter student ID to update: "))
                new_name = input("Enter new name (or press Enter to skip): ").strip()
                new_marks = []
                while True:
                    subject = input("Enter new subject (or 'done' to finish): ")
                    if subject.lower() == 'done':
                        break
                    score = int(input(f"Enter new score for {subject}: "))
                    new_marks.append({'subject': subject, 'score': score})
                update_student(session, student_id, new_name or None, new_marks if new_marks else None)
                pass

            elif choice == '5':
                id = input("Enter student ID to delete: ")
                delete_student(session, int(id))
                pass
            elif choice == '6':
                export_to_csv(session)
                pass
            elif choice == '7':
                print("Goodbye!")
                session.close()
                sys.exit()
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"⚠️ Error: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    main()