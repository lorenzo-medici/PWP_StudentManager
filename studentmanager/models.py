"""
This module contains all Model classes for our API, as well as click functions callable
    from the command line
The classes are:
 - Assessment
 - Student
 - Course
 - ApiKey
The functions are responsible for initiliazing and populating the database, generating the
    admin key, and running the tests
"""
import datetime
import hashlib
import secrets

import click
import pytest
from flask import request
from flask.cli import with_appcontext
from sqlalchemy import event, CheckConstraint
from sqlalchemy.future import Engine
from sqlalchemy.orm import validates
from werkzeug.exceptions import Forbidden

from studentmanager import db
from studentmanager.utils import is_valid_ssn


# from the Exercise 1 webpage
# https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/introduction-to-web-development/#sidenote-foreign-keys-in-sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Called when a connection to the database is established.
    Activates the constraints on foreign keys.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Assessment(db.Model):
    """
    A class that represents an assessment. Contains references to the student and the course
        it is related to.
    Additionally, stores the grade accomplished and the date of the assessment. The grade must be
        between 0 (Fail) and 5.
    The date must be at most the current day.
    """

    # COLUMNS
    #
    # constraints
    #  - grade is between 0 and 5, with 0 meaning Fail
    #  - date is at most today

    course_id = db.Column(db.Integer, db.ForeignKey(
        "course.course_id", ondelete="CASCADE"), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(
        "student.student_id", ondelete="CASCADE"), primary_key=True)
    grade = db.Column(db.Integer, CheckConstraint(
        'grade IN (0,1,2,3,4,5)'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    # VALIDATORS

    # date is at most today
    @validates("date")
    def validate_date(self, key, date):
        """
        Checks that the given date is at most the current date
        :param key: the name of the attribute to validate (date)
        :param date: datetime.date object representing the date the assessment has
            been conducted on
        :return: the date if it is at most today
        :raise AssertionError: if date is in the future
        """
        assert date <= datetime.date.today()
        return date

    # RELATIONSHIPS
    #  - only one student and one course for each assessment (useList=False)

    student = db.relationship(
        "Student", back_populates="assessments", uselist=False)
    course = db.relationship(
        "Course", back_populates="assessments", uselist=False)

    # TABLENAME
    #   allows direct reference between Student and Course based on all the associations;
    #   it works in the same way as the db.Table construct

    __tablename__ = 'assessments'

    # SERIALIZER
    def serialize(self):
        """
        Serializes the current object into JSON representation
        :return: the dictionary containing the object's attributes with realtive keys
        """
        doc = {'course_id': self.course_id,
               'student_id': self.student_id,
               'grade': self.grade,
               'date': self.date.strftime('%Y-%m-%d')}

        return doc

    # DESERIALIZER
    def deserialize(self, doc):
        """
        Populates the self object with the values contained in doc
        :param doc: the dictionary containing all mandatory fields for this class
            (refer to json_schema)
        :return: nothing if the deserialization is successful
        :raise ValueError: if the date is not in ISO format
        """
        self.course_id = doc["course_id"]
        self.student_id = doc["student_id"]
        self.grade = doc["grade"]
        self.date = datetime.date.fromisoformat(doc["date"])

    # JSON SCHEMA
    @staticmethod
    def json_schema():
        """
        :return: the valid JSON schema for the Assessment class
        """
        schema = {
            "type": "object",
            "required": ["course_id", "student_id", "grade", "date"]
        }
        props = schema["properties"] = {}
        props["course_id"] = {
            "description": "Course identifier that this assessment belongs to",
            "type": "number",
        }
        props["student_id"] = {
            "description": "Student identifier that this assessment belongs to",
            "type": "number",
        }
        props["grade"] = {
            "description": "Achieved grade on this assessment",
            "type": "number"
        }
        props["date"] = {
            "description": "Date of assessment marking in format yyyy-mm-dd",
            "type": "string",
            "format": "date-time"
        }
        return schema


class Student(db.Model):
    """
    A class that represents a student. Contains personal information, as well as the assessments a
        student has, and all the courses they have assessments for.
    The date of birth has to be in the past, and the Social Security Number has to be valid for the
        given date, as well as unique.
    """

    # COLUMNS
    #
    # constraints
    #  - date_of_birth is in the past
    #  - ssn is valid for given date_of_birth

    student_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    ssn = db.Column(db.String(11), nullable=False, unique=True)

    # VALIDATORS

    # date_of_birth is in the past

    @validates("date_of_birth")
    def validate_date_of_birth(self, key, date_of_birth):
        """
        Checks that the given date_of_birth is before the current date
        :param key: the name of the attribute to validate (date_of_birth)
        :param date_of_birth: datetime.date object representing the date of birth to check
        :return: the date if it is in the past
        :raise AssertionError: if date_of_birth is not in the past
        """
        assert date_of_birth < datetime.date.today()
        return date_of_birth

    # ssn is valid for given date_of_birth
    @validates("ssn")
    def validate_ssn(self, key, ssn):
        """
        Checks that the given ssn is valid for the date of birth of the object
        :param key: the name of the attribute to validate (ssn)
        :param ssn: the string representing the ssn
        :return: the ssn if it is valid
        :raise AssertionError: if the ssn is not valid
        """
        assert is_valid_ssn(ssn, self.date_of_birth)
        return ssn

    # RELATIONSHIPS
    #  - all of the student's assessments

    assessments = db.relationship(
        "Assessment", cascade="all, delete-orphan", back_populates="student")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of courses
    #   the student has assessments for
    # WARNING: changes will be reflected only after the Session has ended
    # info at
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    courses = db.relationship(
        "Course",
        secondary="assessments",
        back_populates="students",
        viewonly=True)

    # SERIALIZER
    def serialize(self, short_form=False):
        """
        Transforms a student object in a json file
        :param short_form: bool parameter that determines if json file has to contain assessments
        :return doc: return a json file containing the information about the student
        """
        doc = {'student_id': self.student_id,
               'first_name': self.first_name,
               'last_name': self.last_name,
               'date_of_birth': self.date_of_birth.strftime('%Y-%m-%d'),
               'ssn': self.ssn}
        if not short_form:
            doc["assessments"] = [a.serialize() for a in self.assessments]

        return doc

    # DESERIALIZER
    def deserialize(self, doc):
        """
        Deserialize a json file converting each field in one of the field of a student object
        :param doc: Json file
        :raise ValueError: if the date_of_birth parameter in doc is not a valid iso format
        """
        self.first_name = doc["first_name"]
        self.last_name = doc["last_name"]
        self.date_of_birth = datetime.date.fromisoformat(doc["date_of_birth"])
        self.ssn = doc["ssn"]

    # JSON SCHEMA
    @staticmethod
    def json_schema():
        """
        :return: the valid JSON schema for the Student class
        """
        schema = {
            "type": "object",
            "required": ["first_name", "last_name", "ssn", "date_of_birth"]
        }
        props = schema["properties"] = {}
        props["ssn"] = {
            "description": "student social security number",
            "type": "string",
        }
        props["first_name"] = {
            "description": "Student first name",
            "type": "string",
        }
        props["last_name"] = {
            "description": "Student last name",
            "type": "string"
        }
        props["date_of_birth"] = {
            "description": "Student birth date in the format yyyy-mm-dd",
            "type": "string",
            "format": "date-time"
        }
        return schema


class Course(db.Model):
    """A class that represents a course. Stores the course name, code, teacher and ects.
        Additionally, stores all the assessments for the course, as well as all the students
         that have an assessment for it.
    The ects value must be greater than and the course code must be unique."""
    # COLUMNS
    #
    # constraints
    #  - ects is positive (with no upper bound)

    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    teacher = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(12), nullable=False, unique=True)
    ects = db.Column(db.Integer, CheckConstraint('ects > 0'), nullable=False)

    # RELATIONSHIPS
    #  - all of the assessments for this course

    assessments = db.relationship(
        "Assessment", cascade="all, delete-orphan", back_populates="course")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of students that
    #   have assessments for this course
    # WARNING: changes will be reflected only after the Session has ended
    # info at:
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    students = db.relationship(
        "Student",
        secondary="assessments",
        back_populates="courses",
        viewonly=True)

    # SERIALIZATION METHODS

    def serialize(self, short_form=False):
        """
        Transforms a course object in a json file
        :param short_form: bool parameter that determines if json file has to contain assessments
        :return doc: return a json file containing the information about the course
        """
        doc = {
            "course_id": self.course_id,
            "title": self.title,
            "teacher": self.teacher,
            "code": self.code,
            "ects": self.ects
        }
        if not short_form:
            doc["assessments"] = [a.serialize() for a in self.assessments]

        return doc

    def deserialize(self, doc):
        """
        Deserialize a json file converting each field in one of the field of a course object
        :param doc: Json file
        """
        self.title = doc["title"]
        self.teacher = doc["teacher"]
        self.code = doc["code"]
        self.ects = doc["ects"]

    # JSON schema for validation

    @staticmethod
    def json_schema():
        """
        :return: the valid JSON schema for the Course class
        """
        schema = {
            "type": "object",
            "required": ["title", "teacher", "code", "ects"]
        }
        props = schema["properties"] = {}
        props["title"] = {
            "description": "Name of the course",
            "type": "string",
        }
        props["teacher"] = {
            "description": "Teacher responsible for the course",
            "type": "string",
        }
        props["code"] = {
            "description": "Code of the course",
            "type": "string",
        }
        props["ects"] = {
            "description": "Number of ECTS granted by the course",
            "type": "number",
        }

        return schema


class ApiKey(db.Model):
    """
    A class representing the API keys saved in the database. Keys can be admin (write permission
        to all resources) or not (write permission only on assessments)
    """
    key = db.Column(
        db.String(32),
        nullable=False,
        unique=True,
        primary_key=True)
    admin = db.Column(db.Boolean, default=False)

    @staticmethod
    def key_hash(key):
        """
        Generates the hash for the given randomly generated token
        :param key: a string representing the token to use for the API
        :return: the sha256 digest of the key parameter
        """
        return hashlib.sha256(key.encode()).digest()


# From the Sensorhub example project
def require_admin_key(func):
    """
    Decorator function that runs the parameter function only if the request contains an admin key
    :param func: function to be executed if the request contains a key with admin privileges
    :raise Forbidden: if the request doesn't contain an admin key
    """

    def wrapper(*args, **kwargs):
        key_hash = ApiKey.key_hash(request.headers.get(
            "Studentmanager-Api-Key", "").strip())
        db_key = ApiKey.query.filter_by(admin=True).first()
        if db_key is None or secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden

    return wrapper


# From the Sensorhub example project
def require_assessments_key(func):
    """
    Decorator function that runs the parameter function only if the request contains an API key
    :param func: function to be executed if the request contains a valid key
    :raise Forbidden: if the request doesn't contain an API key'
    """

    def wrapper(*args, **kwargs):
        key_hash = ApiKey.key_hash(request.headers.get(
            "Studentmanager-Api-Key", "").strip())
        db_keys = ApiKey.query.all()
        for k in db_keys:
            if secrets.compare_digest(key_hash, k.key):
                return func(*args, **kwargs)
        raise Forbidden

    return wrapper


@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    Click function callable from the command line, initializes the database
    """
    db.create_all()


@click.command("testgen")
@with_appcontext
def generate_test_data():
    """
    Click function callable from the command line, populates the already initialized database
        with test data
    """
    s_1 = Student(
        first_name='Draco',
        last_name='Malfoy',
        date_of_birth=datetime.date.fromisoformat('1980-06-05'),
        ssn='050680-6367'
    )

    s_2 = Student(
        first_name='Harry',
        last_name='Potter',
        date_of_birth=datetime.date.fromisoformat('1980-07-31'),
        ssn='310780-6176'
    )

    s_3 = Student(
        first_name='Hermione',
        last_name='Granger',
        date_of_birth=datetime.date.fromisoformat('1979-09-19'),
        ssn='190979-8400'
    )

    c_1 = Course(
        title='Transfiguration',
        teacher='Minerva Mcgonagall',
        code='004723',
        ects=5
    )

    c_2 = Course(
        title='Defence Against the Dark Arts',
        teacher='Professur Severus Snape',
        code='006031',
        ects=8
    )

    c_3 = Course(
        title='Advanced Defence Against the Dark Arts',
        teacher='Professur Severus Snape',
        code='006032',
        ects=8
    )

    a_s1_c1 = Assessment(
        student=s_1,
        course=c_1,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s1_c2 = Assessment(
        student=s_1,
        course=c_2,
        grade=4,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    a_s2_c1 = Assessment(
        student=s_2,
        course=c_1,
        grade=3,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s2_c2 = Assessment(
        student=s_2,
        course=c_2,
        grade=4,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    a_s3_c1 = Assessment(
        student=s_3,
        course=c_1,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s3_c2 = Assessment(
        student=s_3,
        course=c_2,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    db.session.add(s_1)
    db.session.add(s_2)
    db.session.add(s_3)

    db.session.add(c_1)
    db.session.add(c_2)
    db.session.add(c_3)

    db.session.add(a_s1_c1)
    db.session.add(a_s1_c2)
    db.session.add(a_s2_c1)
    db.session.add(a_s2_c2)
    db.session.add(a_s3_c1)
    db.session.add(a_s3_c2)

    db.session.commit()


@click.command("testrun")
def run_tests():
    """
    Click function callable from the command line, runs the tests contained in the
        `tests/` subfolder
    """
    pytest.main(["-x", "tests"])


@click.command("masterkey")
@with_appcontext
def generate_master_key():
    """
    Click function callable from the command line, used to generate the admin key for the database.
    Prints the key after adding it.
    """
    # admin key
    token = secrets.token_urlsafe()
    db_key = ApiKey(
        key=ApiKey.key_hash(token),
        admin=True
    )
    db.session.add(db_key)
    print("admin key: " + token)

    # non-admin assessment key
    token = secrets.token_urlsafe()
    db_key = ApiKey(
        key=ApiKey.key_hash(token),
        admin=False
    )
    db.session.add(db_key)
    print("assessment key: " + token)

    db.session.commit()
