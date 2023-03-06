"""
This module contains all the classes related to the Course resource:
 - the collection of all courses
 - a singular course
 - the related URL converter
"""
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import cache
from studentmanager import db
from studentmanager.models import Course, require_admin_key
from studentmanager.utils import request_path_cache_key


class CourseCollection(Resource):
    """
    Class that represents a collection of courses, reachable at '/api/courses/'
    """
    @cache.cached(make_cache_key=request_path_cache_key)
    def get(self):
        """Get the list of courses from the database"""
        courses = Course.query.all()

        courses_list = [c.serialize(short_form=True) for c in courses]

        return courses_list

    @require_admin_key
    def post(self):
        """Adds a new course.
        takes as input a json file passed with the post request
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid, or the ects value is not integer.
        Returns 409 if an IntegrityError happens (code is already present)
        Returns 201 and a location header containing the uri of the newly added course"""

        try:
            validate(request.json, Course.json_schema())
        except ValidationError:
            return "JSON format is not valid", 400

        course = Course()
        course.deserialize(request.json)

        if not isinstance(course.ects, int):
            return "Ects value must be an integer", 400

        try:
            db.session.add(course)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Course already exists with code '{course.code}'", 409
        self._clear_cache()
        return Response(
            status=201,
            headers={
                'Location': url_for('api.courseitem', course=course)
            }
        )

    def _clear_cache(self):
        cache.delete(
            request.path
        )


class CourseItem(Resource):
    """
    Class that represents a Course Resource, reachable at '/api/courses/<course_id>/'
    Available methods are GET, PUT and DELETE
    """
    @cache.cached(make_cache_key=request_path_cache_key)
    def get(self, course):
        """Returns the representation of the course
        :param course: takes a student object containing the information about the student"""
        return course.serialize()

    @require_admin_key
    def put(self, course):
        """Edits the course's data.
        :param course: student object that contains the information of the student that has
            to be edited
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (code is already present)
        Returns 204 if the course has correctly been updated"""

        try:
            validate(request.json, Course.json_schema())
        except ValidationError as exc:
            return str(exc), 400

        course.deserialize(request.json)

        if not isinstance(course.ects, int):
            return "Ects value must be an integer", 400

        try:
            db.session.add(course)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Course with code '{course.code}' already exists.", 409
        self._clear_cache()
        return Response(status=204)

    @require_admin_key
    def delete(self, course):
        """Deletes the existing course
        :param course: a student object that contains the information about the student that
            has to be modified
        Returns: 204 if the course is correctly deleted"""
        db.session.delete(course)
        db.session.commit()
        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for('api.coursecollection')
        cache.delete_many(
            collection_path,
            request.path,
        )


class CourseConverter(BaseConverter):
    """
    URLConverter for course resource.
    to_python takes a course_id and returns a Course object.
    to_url takes a Course object and returns the corresponding course_id
    """

    def to_python(self, value):
        """
        Converts a course_id in a course object by retrieving the information from the database
        :param value: str representing the course id
        raises a NotFound error if it is impossible to convert the string in an int or if the
            course is not found
        :return: a course object corresponding to the course_id
        """
        try:
            int_id = int(value)
        except ValueError as exc:
            raise NotFound from exc

        db_course = Course.query.filter_by(course_id=int_id).first()
        if db_course is None:
            raise NotFound
        return db_course

    def to_url(self, value):
        """
        Transforms a course object in a value usable in the URI
        :param value: course Object
        :return: the value
        """
        return str(value.course_id)
