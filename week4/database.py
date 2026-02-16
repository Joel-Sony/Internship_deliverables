from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os   

load_dotenv()  
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_USER = os.getenv("MYSQL_USER", "root")  # Default to root if not found
DB_NAME = "student_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost:3306/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
