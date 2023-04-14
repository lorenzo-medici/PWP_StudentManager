"""
This module contains all the classes related to the Student resource:
 - the collection of all students
 - a singular student
 - the related URL converter
"""
import json
import os

from flasgger import swag_from
from flask import request, url_for, Response
from flask_restful import Resource
from jsonschema import validate, ValidationError
from jsonschema.validators import Draft7Validator
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from studentmanager import cache
from studentmanager import db
from studentmanager.builder import StudentManagerBuilder, create_error_response
from studentmanager.constants \
    import STUDENT_PROFILE, MASON, LINK_RELATIONS_URL, NAMESPACE, DOC_FOLDER
from studentmanager.models import Student, require_admin_key
from studentmanager.utils import request_path_cache_key


class StudentCollection(Resource):
    """
    Class that represents a collection of students, reachable at '/api/students/'
    """

    # must explicitly specify current working directory because otherwise
    # it will look in in cache dir
    @swag_from(os.getcwd() + f"{DOC_FOLDER}student_collection/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """
        Get the list of al the students as a json response
        """

        body = StudentManagerBuilder(items=[])

        for student in Student.query.all():
            item = StudentManagerBuilder(student.serialize(short_form=True))
            item.add_control("self", url_for('api.studentitem', student=student))
            item.add_control("profile", STUDENT_PROFILE)
            body["items"].append(item)

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for('api.studentcollection'))
        body.add_control_add_student()
        body.add_control_all_courses()
        body.add_control_all_assessments()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(f"{DOC_FOLDER}student_collection/post.yml")
    @require_admin_key
    def post(self):
        """
        Adds a new student.
        takes as input a json file passed with the post request
        Returns 415 if the request is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (ssn is invalid or already present, date_of_birth
            is not in the past)
        Returns 201 and a location header containing the uri of the newly added student
        """

        student = Student()

        try:
            validate(request.json, Student.json_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)

            student.deserialize(request.json)

            db.session.add(student)
            db.session.commit()
        except ValidationError:
            return create_error_response(400, 'Bad Request', "Invalid request format")

        except ValueError:
            return create_error_response(400, 'Bad Request', 'Date_of_birth not in iso format')

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                'Conflict',
                f"Student with ssn '{student.ssn}' already exists."
            )

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

    # must explicitly specify current working directory because otherwise
    # it will look in in cache dir
    @swag_from(os.getcwd() + f"{DOC_FOLDER}student_item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, student):
        """
        Returns the representation of the student
        :param student: takes a student object containing the information about the student
        """

        body = StudentManagerBuilder(student.serialize())

        self_url = url_for('api.studentitem', student=student)

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", STUDENT_PROFILE)
        body.add_control_put("Modify a student", self_url, Student.json_schema())
        body.add_control_delete("Delete a student", self_url)
        body.add_control("collection", url_for('api.studentcollection'))
        body.add_control_all_assessments()
        body.add_control_student_assessments(student)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(f"{DOC_FOLDER}student_item/put.yml")
    @require_admin_key
    def put(self, student):
        """
        Edits the student's data.
        :param student: student object that contains the information of the student that has to
            be edited
        Returns 415 if the requests is not a valid json request.
        Returns 400 if the format of the request is not valid.
        Returns 409 if an IntegrityError happens (ssn is invalid or already present, date_of_birth
            is not in the past)
        Returns 204 if the student has correctly been updated
        """

        try:
            validate(request.json, Student.json_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)

            student.deserialize(request.json)

            db.session.add(student)
            db.session.commit()
        except ValidationError:
            return create_error_response(400, 'Bad Request', "Invalid request format")

        except ValueError:
            return create_error_response(400, 'Bad Request', 'Date_of_birth not in iso format')

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                'Conflict',
                f"Student with ssn '{student.ssn}' already exists."
            )

        self._clear_cache()
        return Response(status=204)

    @swag_from(f"{DOC_FOLDER}student_item/delete.yml")
    @require_admin_key
    def delete(self, student):
        """
        Deletes the existing student
        :param student: a student object that contains the information about the student that has
            to be modified
        :return: 204 if the student is correctly deleted
        """
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
