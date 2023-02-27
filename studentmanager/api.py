from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

from studentmanager.resources.course import CourseCollection, CourseItem

api.add_resource(CourseCollection, "/courses/")
api.add_resource(CourseItem, "/courses/<course:course>/")


@api_bp.route("/")
def index():
    return ""
