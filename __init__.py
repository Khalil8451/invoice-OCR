from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .extensions import db

def create_app():
    application = Flask(__name__, instance_relative_config=False)

    application.config['SECRET_KEY'] = 'thisissupposedtobesecret'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    application.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'

    db.init_app(application)
    JWTManager(application)



    CORS(application, resources={r"/*":{"origins": "*", "send_wildcard": "False"}})
    application.config.from_object('config.Config')
    register_blueprints(application)
    return application

def register_blueprints(application):
    from app.Controllers import OCRController

    application.register_blueprint(OCRController.ocr_blueprint)