from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

from studentmanager.resources.course import CourseCollection, CourseItem
from studentmanager.resources.student import StudentCollection, StudentItem

api.add_resource(CourseCollection, "/courses/")
api.add_resource(CourseItem, "/courses/<course:course>/")

api.add_resource(StudentCollection, "/students/")
api.add_resource(StudentItem, "/students/<student:student>/")


@api_bp.route("/")
def index():
    return ""
