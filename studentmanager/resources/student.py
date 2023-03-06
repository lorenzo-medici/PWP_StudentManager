"""
This module contains all the classes related to the Student resource:
 - the collection of all students
 - a singular student
 - the related URL converter
"""
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from jsonschema.validators import Draft7Validator
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import cache
from studentmanager import db
from studentmanager.models import Student, require_admin_key
from studentmanager.utils import request_path_cache_key


class StudentCollection(Resource):
    """
    Class that represents a collection of students, reachable at '/api/students/'
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """
        Get the list of al the students as a json response
        """

        students = Student.query.all()

        students_list = [s.serialize(short_form=True) for s in students]

        return students_list

    @require_admin_key
    def post(self):
        """Adds a new student.
        takes as input a json file passed with the post request
        Returns 415 if the request is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (ssn is invalid or already present, date_of_birth
            is not in the past)
        Returns 201 and a location header containing the uri of the newly added student"""

        student = Student()

        try:
            validate(request.json, Student.json_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)

            student.deserialize(request.json)

            db.session.add(student)
            db.session.commit()
        except ValidationError:
            return "Invalid request format", 400

        except ValueError:
            return 'Date_of_birth not in iso format', 400

        except IntegrityError:
            db.session.rollback()
            return f"Student with ssn '{student.ssn}' already exists.", 409
        self._clear_cache()
        return Response(
            status=201,
            headers={
                'Location': url_for('api.studentitem', student=student)
            }
        )

    def _clear_cache(self):
        cache.delete(
            request.path
        )


class StudentItem(Resource):
    """
    Class that represents a Student Resource, reachable at '/api/students/<student_id>/'
    Available methods are GET, PUT and DELETE
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, student):
        """Returns the representation of the student
        :param student: takes a student object containing the information about the student"""
        return student.serialize()

    @require_admin_key
    def put(self, student):
        """Edits the student's data.
        :param student: student object that contains the information of the student that has to
            be edited
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (ssn is invalid or already present, date_of_birth
            is not in the past)
        Returns 204 if the student has correctly been updated"""

        try:
            validate(request.json, Student.json_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)

            student.deserialize(request.json)

            db.session.add(student)
            db.session.commit()
        except ValidationError as exc:
            return str(exc), 400

        except ValueError:
            return 'Date_of_birth not in iso format', 400

        except IntegrityError:
            db.session.rollback()
            return f"Student with ssn '{student.ssn}' already exists.", 409
        self._clear_cache()
        return Response(status=204)

    @require_admin_key
    def delete(self, student):
        """Deletes the existing student
        :param student: a student object that contains the information about the student that has
            to be modified
        :return: 204 if the student is correctly deleted"""
        db.session.delete(student)
        db.session.commit()
        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for('api.studentcollection')
        cache.delete_many(
            collection_path,
            request.path,
        )


class StudentConverter(BaseConverter):
    """
    URLConverter for student resource.
    to_python takes a student_id and returns a Student object.
    to_url takes a Student object and returns the corresponding student_id
    """

    def to_python(self, value):
        """
        Converts a student_id in a student object by retrieving the information from the database
        :param value: str representing the student id
        :raise: a NotFound error if it is impossible to convert the string in an int or if the
            student is not found
        :return: a student object corresponding to the student_id
        """
        try:
            int_id = int(value)
        except ValueError as exc:
            raise NotFound from exc
        db_student = Student.query.filter_by(student_id=int_id).first()
        if db_student is None:
            raise NotFound
        return db_student

    def to_url(self, value):
        """
        Transforms a student object in a value usable in the URI
        :param value: Student Object
        :return: the value
        """
        return str(value.student_id)
