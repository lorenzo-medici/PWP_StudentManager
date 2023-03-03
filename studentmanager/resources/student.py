import datetime
from datetime import datetime

from jsonschema import validate, ValidationError
from flask import abort, request, Response, url_for
# from sqlalchemy.exc import IntegrityError
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError

from studentmanager import db
from studentmanager.models import Student

# from werkzeug.exceptions import NotFound
# from werkzeug.routing import BaseConverter

api = Api()


class StudentCollection(Resource):

    def get(self):
        """gets the list of the students from the database"""
        response_data = []
        students = Student.query.all()

        for student in students:
            response_data.append(student.serialize())
        return response_data

    def post(self):
        """Adds a new student
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid, or the date format is not YYYY-MM-DD.
        Returns 409 if an IntegrityError happens (code is already present)"""

        if not request.json:
            return "unsupported media type", 415

        try:
            validate(request.json, Student.json_schema())
        except ValidationError as exc:
            return str(exc), 400

        student = Student()
        student.deserialize(request.json)

        try:
            db.session.add(student)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409)
        except AssertionError:
            abort(400)

        return Response(
            status=201,
            headers={"Location": url_for('api.studentitem')}
        )


class StudentItem(Resource):

    def get(self, student):
        """Returns the representation of the student"""
        return student.serialize()

    def put(self, student):
        """Edit the student data.
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (student is already present)"""
        if not request.json:
            return "unsupported media type", 415

        try:
            validate(request.json, Student.json_schema())
        except ValidationError as exc:
            return str(exc), 400

        try:
            student.deserialize(request.json)
        except ValueError:
            return "The date format is wrong", 400

        try:
            db.session.add(student)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return f"Student with id '{student.student_id}' already exists", 409

        return Response(status=204)

    def delete(self, student):
        """Delete existing course"""
        db.session.delete(student)
        db.session.commit()

        return Response(status=204)
