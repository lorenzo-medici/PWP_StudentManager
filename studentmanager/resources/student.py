from flask import Flask, abort, request, json, Response, app
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.exc import IntegrityError
from flask_restful import Api, Resource
from studentmanager.models import Student
import datetime
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from studentmanager import create_app, db

# from werkzeug.exceptions import NotFound
# from werkzeug.routing import BaseConverter

api = Api()


class StudentCollection(Resource):

    def get(self):
        response_data = []
        students = Student.query.all()

        for student in students:
            response_data.append(student.serialize())
        return response_data

    def post(self):
        if not request.json:
            abort(415)

        name = request.json['name']
        surname = request.json['surname']
        date_of_birth_string = request.json['date_of_birth']
        ssn = request.json['ssn']
        try:
            date_of_birth = datetime.date.fromisoformat(date_of_birth_string)
        except ValueError:
            return "The date format is wrong", 400

        try:
            student = Student(
                firt_name=name,
                last_name=surname,
                date_of_birth=date_of_birth,
                ssn=ssn
            )

            db.session.add(student)
            db.session.commit()

        except IntegrityError:
            abort(409)

        except AssertionError:
            abort(400)

        return "", 201


class StudentItem(Resource):

    def get(self, student):
        return student.serialize()

    def put(self, student):
        if not request.json:
            abort(405)

        try:
            student.deserialize(request.json)
        except ValueError:
            return "The date format is wrong", 400

        try:
            db.session.add(student)
            db.session.commit()
        except IntegrityError:
            abort(400)

        return "", 201

    def delete(self, student):
        db.session.delete(student)
        db.session.commit()

        return "", 204


