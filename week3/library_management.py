import uuid 
from datetime import datetime, timedelta
import csv

class Book:
    def __init__(self, title, author, book_id):
        self.book_id = book_id
        self.title = title
        self.author = author 
        self.isBorrowed = False

class Member:
    def __init__(self,member_id,name):
        self.name = name
        self.member_id = member_id
        self.borrowed_books = []
    
    def borrow_book(self, book):
        if not book.isBorrowed:
            book.isBorrowed = True
            self.borrowed_books.append(book)
        else:
            raise ValueError(f"Book: {book.title} is already borrowed.")
    
    def return_book(self, book):
        if book in self.borrowed_books:
            book.isBorrowed = False
            self.borrowed_books.remove(book)
        else:
            raise ValueError(f"Book: {book.title} was not borrowed by {self.name}.")


class Transactions:
    def __init__(self, transaction_type, member, book, id = None):
        self.id = id if id else str(uuid.uuid4())
        self.type =  transaction_type
        self.member = member
        self.book = book
        self.due_date = datetime.now() + timedelta(days=14) # Assuming a 2-week borrowing period
        self.return_date = None
        self.fine = 0
    


class Librarian:
    def __init__(self):
        self.books = {}
        self.members = {}
        self.transactions = {}

    def load_data(self):
        try:
            # Change 'w' to 'r' for ALL loading blocks
            with open('books.csv', 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader,None)
                for row in reader: 
                    book = Book(row[1], row[2], row[0])
                    book.isBorrowed = row[3] == 'True' #cuz csv stores everything as strings 
                    self.books[row[0]] = book

            with open('transactions.csv', 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader,None)

                for row in reader:
                    # Convert strings back to datetime objects
                    due_date = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
                    
                    # return_date might be "None"
                    ret_date = None
                    if row[5] and row[5] != "None":
                        ret_date = datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S.%f")
                    
                    t = Transactions(row[1], row[2], row[3], id=row[0])
                    t.due_date = due_date
                    t.return_date = ret_date
                    t.fine = float(row[6])
                    self.transactions[row[0]] = t
        
            with open('members.csv', 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader,None)
                for row in reader:
                    self.members[row[0]] = Member(row[0], row[1])

            for t in self.transactions.values():
                if t.type == 'borrow' and t.return_date is None:
                    if t.member in self.members and t.book in self.books:
                        book_obj = self.books[t.book]
                        member_obj = self.members[t.member]
                        
                        if book_obj not in member_obj.borrowed_books:
                            member_obj.borrowed_books.append(book_obj)
        except FileNotFoundError:
            print("Data files not found. Starting with empty library.")
            
    def save_data(self):
        with open('books.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['book_id', 'title', 'author', 'isBorrowed'])
            for book in self.books.values(): 
                writer.writerow([book.book_id, book.title, book.author, book.isBorrowed])
        
        with open('transactions.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['transaction_id', 'type', 'member_id', 'book_id', 'due_date', 'return_date', 'fine'])
            for transaction in self.transactions.values():
                writer.writerow([transaction.id, 
                                transaction.type, 
                                transaction.member, 
                                transaction.book,
                                transaction.due_date,
                                transaction.return_date,
                                transaction.fine])
                
        with open('members.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['member_id', 'name'])
            for member in self.members.values():
                writer.writerow([member.member_id, member.name])
    
    def add_book(self, title, author):
        if not title.strip() or not author.strip():
            raise ValueError("Book title and author cannot be empty.")
        
        book_id = str(len(self.books) + 1)
        new_book = Book(title, author, book_id)
        self.books[book_id] = new_book
        self.save_data()
    
    def add_member(self, name):
        if not name.strip():
            raise ValueError("Member name cannot be empty.")
        
        member_id = str(len(self.members) + 1)
        new_member = Member(member_id, name )
        self.members[member_id] = new_member
        self.save_data()
    
    def borrow_book(self, member_id, book_id):
        if member_id not in self.members:
            raise KeyError(f"Member ID '{member_id}' not found.")
        if book_id not in self.books:
            raise KeyError(f"Book ID '{book_id}' not found.")
        
        if member_id in self.members and book_id in self.books:
            member = self.members[member_id]
            book = self.books[book_id]
            if not book.isBorrowed:
                member.borrow_book(book)
                transaction = Transactions('borrow', member_id, book_id)
                self.transactions[transaction.id] = transaction
                self.save_data()
                print(f"\nBook: {book.title} borrowed by {member.name}. Due on {transaction.due_date.strftime('%Y-%m-%d')}.")
            else:
                print(f"\nSorry, Book: {book.title} is already borrowed.")
    
    def return_book(self, member_id, book_id):
        if member_id in self.members and book_id in self.books:
            member = self.members[member_id]
            book = self.books[book_id]
            if book in member.borrowed_books:
                member.return_book(book)
                for transaction in self.transactions.values():
                    if transaction.member == member_id and transaction.book == book_id and transaction.type == 'borrow' and transaction.return_date is None:
                        transaction.return_date = datetime.now()
                        time_diff = transaction.return_date - transaction.due_date

                        if time_diff.days > 0:
                            transaction.fine = max(0,time_diff.days * 10)  
                        else:   
                            transaction.fine = 0
                        
                self.save_data()
                print(f"\nBook: {book.title} returned by {member.name}. Fine: ${transaction.fine:.2f}")
            else:
                print(f"\nBook: {book.title} was not borrowed by {member.name}.")
        else:
            print("Invalid member ID or book ID.")

    def show_books(self):
        if(not self.books):
            print("\nNo books in the library.")
            return
        print("\n--- Library Books ---")
        for book in self.books.values():
            status = "Borrowed" if book.isBorrowed else "Available"
            print(f"{book.book_id}: {book.title} by {book.author} - {status}")
    
    def display_available_books(self):
        if(not self.books):
            print("\nNo books in the library.")
            return
        print("\n--- Available Books ---")
        for book in self.books.values():
            if not book.isBorrowed:
                print(f"{book.book_id}: {book.title} by {book.author}")
    
    def list_members(self):
        if(not self.members):
            print("\nNo members in the library.")
            return
        print("\n--- Library Members ---")
        for member in self.members.values():
            print(f"{member.member_id}: {member.name}")

def main():
    lib = Librarian()
    lib.load_data()

    while True:
        print("\n--- Library System ---")
        print("1. Add Book\n2. Add Member\n3. Borrow Book\n4. Return Book\n5. Show Books\n6. List Members\n7. Exit")
        choice = input("Select an option: ")

        try:
            if choice == '1':
                title = input("Title: ")
                author = input("Author: ")
                lib.add_book(title, author)
            elif choice == '2':
                name = input("Member Name: ")
                lib.add_member(name)
            elif choice == '3':
                lib.display_available_books()
                m_id = input("\nMember ID: ")
                b_id = input("Book ID: ")
                lib.borrow_book(m_id, b_id)
            elif choice == '4':
                m_id = input("Member ID: ")
                b_id = input("Book ID: ")
                lib.return_book(m_id, b_id)
            elif choice == '5':
                lib.show_books()
            elif choice == '6':
                lib.list_members()
            elif choice == '7':
                break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()