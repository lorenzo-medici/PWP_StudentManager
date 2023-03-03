from flask import Blueprint
from flask_restful import Api

from studentmanager.resources.student import StudentCollection, StudentItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(StudentCollection, "/students/")
api.add_resource(StudentItem, "/students/<student:student>/")
