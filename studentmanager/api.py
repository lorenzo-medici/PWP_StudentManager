"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""

from flask import Blueprint
from flask_restful import Api

from studentmanager.resources.assessment import \
    CourseAssessmentCollection, StudentAssessmentCollection, \
    CourseAssessmentItem, StudentAssessmentItem, AssessmentCollection
from studentmanager.resources.course import CourseCollection, CourseItem
from studentmanager.resources.student import StudentCollection, StudentItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(CourseCollection, "/courses/")
api.add_resource(CourseItem, "/courses/<course:course>/")

api.add_resource(StudentCollection, "/students/")
api.add_resource(StudentItem, "/students/<student:student>/")

api.add_resource(AssessmentCollection, "/assessments/")
api.add_resource(StudentAssessmentCollection,
                 "/students/<student:student>/assessments/")
api.add_resource(StudentAssessmentItem,
                 "/students/<student:student>/assessments/<course:course>/")
api.add_resource(CourseAssessmentCollection,
                 "/courses/<course:course>/assessments/")
api.add_resource(CourseAssessmentItem,
                 "/courses/<course:course>/assessments/<student:student>/")
