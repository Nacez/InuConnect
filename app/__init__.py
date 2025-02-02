from flask import Flask
from flask_pymongo import PyMongo
import os

mongo = PyMongo()

def create_app():
    app = Flask(__name__)

    # Configure MongoDB URI
    app.config["MONGO_URI"] = "mongodb+srv://kyej2005:I7OSPUvbx38wth2jd@inuconnectcluster.smivt.mongodb.net/?retryWrites=true&w=majority&appName=InuConnectCluster"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit

    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    mongo.init_app(app)

    # Set a secret key for session management
    app.config["SECRET_KEY"] = os.urandom(24)  # Random 24-byte string as the secret key
    # OR, you can use a manually set secret key (though not recommended for production)
    # app.config["SECRET_KEY"] = "your-secret-key-here"

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
