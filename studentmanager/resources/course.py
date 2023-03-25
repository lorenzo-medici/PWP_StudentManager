"""
This module contains all the classes related to the Course resource:
 - the collection of all courses
 - a singular course
 - the related URL converter
"""
import json
import os

from flasgger import swag_from
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import cache
from studentmanager import db
from studentmanager.builder import StudentManagerBuilder, create_error_response
from studentmanager.constants import COURSE_PROFILE, LINK_RELATIONS_URL, MASON
from studentmanager.models import Course, require_admin_key
from studentmanager.utils import request_path_cache_key


class CourseCollection(Resource):
    """
    Class that represents a collection of courses, reachable at '/api/courses/'
    """

    # must explicitly specify current working directory because otherwise
    # it will look in in cache dir
    @swag_from(os.getcwd() + "/studentmanager/doc/course_collection/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """Get the list of courses from the database"""

        body = StudentManagerBuilder(items=[])

        for course in Course.query.all():
            item = StudentManagerBuilder(course.serialize(short_form=True))
            item.add_control("self", url_for('api.courseitem', course=course))
            item.add_control("profile", COURSE_PROFILE)
            body["items"].append(item)

        body.add_namespace("studman", LINK_RELATIONS_URL)
        body.add_control("self", url_for('api.coursecollection'))
        body.add_control_add_course()
        body.add_control_all_students()
        body.add_control_all_assessments()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from("/studentmanager/doc/course_collection/post.yml")
    @require_admin_key
    def post(self):
        """
        Adds a new course.
        takes as input a json file passed with the post request
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid, or the ects value is not integer.
        Returns 409 if an IntegrityError happens (code is already present)
        Returns 201 and a location header containing the uri of the newly added course
        """

        try:
            validate(request.json, Course.json_schema())
        except ValidationError:
            return create_error_response(400, 'Bad Request', "Invalid request format")

        course = Course()
        course.deserialize(request.json)

        if not isinstance(course.ects, int):
            return "Ects value must be an integer", 400

        try:
            db.session.add(course)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                'Conflict',
                f"Course with code '{course.code}' already exists."
            )

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

    # must explicitly specify current working directory because otherwise
    # it will look in in cache dir
    @swag_from(os.getcwd() + "/studentmanager/doc/course_item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, course):
        """
        Returns the representation of the course
        :param course: takes a student object containing the information about the student
        """

        body = StudentManagerBuilder(course.serialize())

        self_url = url_for('api.courseitem', course=course)

        body.add_namespace("studman", LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", COURSE_PROFILE)
        body.add_control_put("Modify a course", self_url, Course.json_schema())
        body.add_control_delete("Delete a course", self_url)
        body.add_control("collection", url_for('api.coursecollection'))
        body.add_control_all_assessments()
        body.add_control_course_assessments(course)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from("/studentmanager/doc/course_item/put.yml")
    @require_admin_key
    def put(self, course):
        """
        Edits the course's data.
        :param course: student object that contains the information of the student that has
            to be edited
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (code is already present)
        Returns 204 if the course has correctly been updated
        """

        try:
            validate(request.json, Course.json_schema())
        except ValidationError as exc:
            return create_error_response(400, 'Bad Request', "Invalid request format")

        course.deserialize(request.json)

        if not isinstance(course.ects, int):
            return create_error_response(400, 'Bad Request', 'Ects must be an integer')

        try:
            db.session.add(course)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                'Conflict',
                f"Course with code '{course.code}' already exists."
            )
        self._clear_cache()
        return Response(status=204)

    @swag_from("/studentmanager/doc/course_item/delete.yml")
    @require_admin_key
    def delete(self, course):
        """
        Deletes the existing course
        :param course: a student object that contains the information about the student that
            has to be modified
        Returns: 204 if the course is correctly deleted
        """
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
