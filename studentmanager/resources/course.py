from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import db
from studentmanager.models import Course, require_admin_key
from studentmanager import cache


class CourseCollection(Resource):
    @cache.cached()
    def get(self):
        """Get the lsit of courses from the database"""
        courses = Course.query.all()

        courses_list = [c.serialize(short_form=True) for c in courses]

        return courses_list

    @require_admin_key
    def post(self):
        """Adds a new course.
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid, or the ects value is not integer.
        Returns 409 if an IntegrityError happens (code is already present)"""
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Course.json_schema())
        except ValidationError as exc:
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
    @cache.cached()
    def get(self, course):
        """Returns the representation of the course"""
        # TODO remove short_form
        return course.serialize(short_form=True)

    @require_admin_key
    def put(self, course):
        """Edits the course's data.
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (code is already present)"""
        if not request.json:
            return "Unsupported media type", 415

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
        """Deletes the existing course"""
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

    def to_python(self, course_id):
        try:
            int_id = int(course_id)
        except ValueError:
            raise NotFound

        db_course = Course.query.filter_by(course_id=int_id).first()
        if db_course is None:
            raise NotFound
        return db_course

    def to_url(self, value):
        return str(value.course_id)
