# Student Record Management System
A Python CLI application that implements a Relational Database architecture using SQLAlchemy ORM to manage student academic records.

---
## Project Architecture
The project follows a Layered Architecture (Service Pattern) to ensure separation of concerns:

### Presentation Layer (main.py):

Handles the CLI menu loop and user input/output.

### Service Layer (services.py):

Contains business logic (e.g., automated grade calculation).

Manages database transactions (commit, rollback).

### Data Layer (models.py & database.py):

Models: Defines the relational schema using Python classes.

Database: Configures the SQLAlchemy engine and session factory via environment variables.

---

## Database Design
The system implements a One-to-Many relationship between two normalized tables:

students Table: Stores identity data (ID, Name).

marks Table: Stores academic performance linked via a Foreign Key (student_id).

---

## Setup & Usage
1. Environment Configuration
Create a .env file in the root directory:

```
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```
2. Execution
Ensure you have the required drivers installed 
```
pymysql
cryptography
python-dotenv
sqlalchemy
```
then run:

python main.py