"""
This module contains all the classes related to the Assessment resource:
 - the collection of all assessments for both a student and a course
 - a singular assessment for either a student or a course
 - the endpoint for adding new assessments
"""
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from studentmanager import db, cache
from studentmanager.models import Assessment, require_assessments_key
from studentmanager.utils import request_path_cache_key


def clear_cache(assessment):
    """
    Clears all cache entries related to an assessment:
     - the assessment's view
     - its course's assessments view
     - its student's assessments view
     - its course's and student's view (since assessments are included in serialize())
    :param assessment: an existing assessment database object
    """
    course_assessments_url = url_for(
        'api.courseassessmentcollection',
        course=assessment.course)
    course_url = url_for('api.courseitem', course=assessment.course)
    student_assessments_url = url_for(
        'api.studentassessmentcollection',
        student=assessment.student)
    student_url = url_for('api.studentitem', student=assessment.student)
    cache.delete_many(
        request.path,
        course_assessments_url,
        student_assessments_url,
        course_url,
        student_url
    )


class CourseAssessmentCollection(Resource):
    """
    The collection of all assessments of a specific course,
        reachable at '/api/courses/<course_id>/assessments/'
    """

    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, course):
        """Get the list of assessments from the database"""
        assessments = Assessment.query.filter_by(
            course_id=course.course_id).all()
        assessments_list = [c.serialize() for c in assessments]

        return assessments_list


class StudentAssessmentCollection(Resource):
    """
    The collection of all assessments of a specific student,
        reachable at '/api/students/<student_id>/assessments/''
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, student):
        """Get the list of assessments from the database"""
        assessments = Assessment.query.filter_by(
            student_id=student.student_id).all()
        assessments_list = [c.serialize() for c in assessments]

        return assessments_list


class AssessmentCollection(Resource):
    """
    The endpoint for adding a new assessment to the database, reachable at '/api/asssessments/'
    The only available method is POST
    """

    @require_assessments_key
    def post(self):
        """Adds a new assessment.
        Returns 400 if the requests is not a valid json request or if the format of the request
            is not valid, or the ects value is not integer.
        Returns 409 if an IntegrityError happens (assessment for pair (student_id, course_id) is
            already present)"""

        try:
            validate(request.json, Assessment.json_schema())

            assessment = Assessment()

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError:
            return "JSON format is not valid", 400

        except ValueError:
            return 'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and " \
                   f"student_id '{assessment.student_id}'", 409

        clear_cache(assessment)

        return Response(
            status=201,
            headers={
                'Location': url_for(
                    'api.courseassessmentitem',
                    course=assessment.course,
                    student=assessment.student)})


class StudentAssessmentItem(Resource):
    """
    Class that represents an Assessment of a Student in a specific Course
        reachable at '/api/students/<student_id>/assessments/<course_id>'
    Available methods are GET, PUT and DELETE
    """

    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, student, course):
        """
        Returns the representation of the assessment
        :param student: the student_id for which to retrieve the assessment
        :param course: the course_id for which to retrieve the assessment
        Returns the serialized list of assessments
        """

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        return assessment.serialize()

    @require_assessments_key
    def put(self, student, course):
        """Edits the assessment's data.
        :param student: the student_id for which to edit the assessment
        :param course: the course_id for which to edit the assessment
        Returns 400 if the requests is not a valid json request or if the format of the request
            is not valid.
        Returns 409 if an IntegrityError happens (code is already present)"""

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        try:
            validate(request.json, Assessment.json_schema())

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError as exc:
            return str(exc), 400

        except ValueError:
            return 'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and " \
                   f"student_id '{assessment.student_id}'", 409

        clear_cache(assessment)

        return Response(status=204)

    @require_assessments_key
    def delete(self, student, course):
        """
        Deletes the existing assessment
        :param student: the student_id for which to delete the assessment
        :param course: the course_id for which to delete the assessment
        """

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        db.session.delete(assessment)
        db.session.commit()

        clear_cache(assessment)

        return Response(status=204)


class CourseAssessmentItem(Resource):
    """
    Class that represents an Assessment of a Course for a specific Student
        reachable at '/api/courses/<course_id>/assessments/<student_id>'
    Available methods are GET, PUT and DELETE
    """

    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, student, course):
        """
        Returns the representation of the assessment
        :param student: the student_id for which to retrieve the assessment
        :param course: the course_id for which to retrieve the assessment
        Returns the serialized list of assessments
        """

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        return assessment.serialize()

    @require_assessments_key
    def put(self, student, course):
        """Edits the assessment's data.
        :param student: the student_id for which to edit the assessment
        :param course: the course_id for which to edit the assessment
        Returns 400 if the requests is not a valid json request or if the format of the request
            is not valid.
        Returns 409 if an IntegrityError happens (code is already present)"""

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        try:
            validate(request.json, Assessment.json_schema())

            assessment.deserialize(request.json)

            if not isinstance(assessment.grade, int):
                return "Grade value must be an integer", 400

        except ValidationError as exc:
            return str(exc), 400

        except ValueError:
            return 'Date_of_birth not in iso format', 400

        try:
            db.session.add(assessment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Assessment already exists with course_id '{assessment.course_id}' and " \
                   f"student_id '{assessment.student_id}'", 409

        clear_cache(assessment)

        return Response(status=204)

    @require_assessments_key
    def delete(self, student, course):
        """
        Deletes the existing assessment
        :param student: the student_id for which to delete the assessment
        :param course: the course_id for which to delete the assessment
        """

        assessment = Assessment.query \
            .filter_by(student_id=student.student_id) \
            .filter_by(course_id=course.course_id) \
            .first()

        db.session.delete(assessment)
        db.session.commit()

        clear_cache(assessment)

        return Response(status=204)
