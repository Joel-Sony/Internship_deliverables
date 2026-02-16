from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base 

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    
    # This connects to the marks table
    marks = relationship("Mark", back_populates="student", cascade="all, delete-orphan")

class Mark(Base):
    __tablename__ = 'marks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(50), nullable=False) # Essential for school records!
    score = Column(Integer, nullable=False)
    grade = Column(String(5), nullable=False)
    
    # The Foreign Key link
    student_id = Column(Integer, ForeignKey('students.id')) 
    
    # The Relationship link
    student = relationship("Student", back_populates="marks")