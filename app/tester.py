#from __init__ import mongo
from flask_pymongo import PyMongo
from flask import Flask

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test" 
mongo = PyMongo(app)

        
        
business_data = {
            "bname": "Carls Burgers",
            "email": "bickers@gmail.com",
            "password": "password",
            "industry": "Fast Food",
            "location": "Sydney, Australia",
            "description": "blah blah blah im a big Huge business who wants a couple of interns to work under me",
            "jobposts": [{"title": "Engineer Intern",
                         "location": "Sydney, NSW",
                         "industry": "Robotics",
                         "description": "blah blah come work for me you donkey",
                         "responses": 10,
            }],
            "savedstudents": [],
            "currentstudents": [],
}       
        
mongo.db.business.insert_one(business_data) 