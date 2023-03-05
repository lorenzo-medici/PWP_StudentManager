import datetime
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import db
from studentmanager.models import Assessment, require_assessments_key


class CourseAssessmentCollection(Resource):

    def get(self, course):
        """Get the list of assessments from the database"""
        assessments = Assessment.query.filter_by(
            course_id=course.course_id).all()
        assessments_list = [c.serialize(short_form=True) for c in assessments]

        return assessments_list


class StudentAssessmentCollection(Resource):

    def get(self, student):
        """Get the list of assessments from the database"""
        assessments = Assessment.query.filter_by(
            student_id=student.student_id).all()
        assessments_list = [c.serialize(short_form=True) for c in assessments]

        return assessments_list


class AssessmentCollection(Resource):

    @require_assessments_key
    def post(self):
        """Adds a new assessment.
        Returns 400 if the requests is not a valid json request or if the format of the request is not valid, or the ects value is not integer.
        Returns 409 if an IntegrityError happens (code is already present)"""

        try:
            validate(request.json, Assessment.json_schema())

            assessment = Assessment()

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError as exc:
            return "JSON format is not valid", 400

        except ValueError:
            return f'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and student_id '{assessment.student_id}'", 409

        return Response(
            status=201,
            headers={
                'Location': url_for('api.courseassessmentitem', course=assessment, student=assessment)
            }
        )


class StudentAssessmentItem(Resource):

    def get(self, student, course):
        """Returns the representation of the assessment"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        # TODO remove short_form
        return assessment.serialize(short_form=True)

    @require_assessments_key
    def put(self, student, course):
        """Edits the assessment's data.
        Returns 400 if the requests is not a valid json request or if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (code is already present)"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        try:
            validate(request.json, Assessment.json_schema())

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError as exc:
            return str(exc), 400

        except ValueError:
            return f'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and student_id '{assessment.student_id}'", 409

        return Response(status=204)

    @require_assessments_key
    def delete(self, student, course):
        """Deletes the existing assessment"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        db.session.delete(assessment)
        db.session.commit()

        return Response(status=204)


class CourseAssessmentItem(Resource):

    def get(self, student, course):
        """Returns the representation of the assessment"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        # TODO remove short_form
        return assessment.serialize(short_form=True)

    @require_assessments_key
    def put(self, student, course):
        """Edits the assessment's data.
       Returns 400 if the requests is not a valid json request or if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (code is already present)"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        try:
            validate(request.json, Assessment.json_schema())

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError as exc:
            return str(exc), 400

        except ValueError:
            return f'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and student_id '{assessment.student_id}'", 409

        return Response(status=204)

    @require_assessments_key
    def delete(self, student, course):
        """Deletes the existing assessment"""

        assessment = Assessment.query.filter_by(
            student_id=student.student_id).filter_by(
            course_id=course.course_id).first()

        db.session.delete(assessment)
        db.session.commit()

        return Response(status=204)
