# Week 5 – Flask Notes API with JWT Authentication
This project implements a RESTful API using Flask.  
The Postman Collection is present in [api_tests.yaml](./api_tests.yaml).  
The API can be hosted locally

## Setup
1. Clone the repository
2. Create a virtual environment
```
   python -m venv venv
   source venv/bin/activate
```
3. Install dependencies
```
   pip install -r requirements.txt
```
4. Create MySQL database
```
   CREATE DATABASE notes_db;
```
5. Configure .env file:
```
   MYSQL_USER=your_user
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=notes_db
   SECRET_KEY=your_secret
   JWT_SECRET_KEY=your_jwt_secret
```
6. Run the application
   python app.py

### API Endpoints
```
POST    /register
POST    /login
POST    /notes        (Protected)
GET     /notes        (Protected)
GET     /notes/<id>   (Protected)
PUT     /notes/<id>   (Protected)
DELETE  /notes/<id>   (Protected)
```
