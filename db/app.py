import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, CheckConstraint
from sqlalchemy.future import Engine
from sqlalchemy.orm import validates

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.root_path, "StudentManager.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Assessment(db.Model):

    # COLUMNS
    #
    # constraints
    #  - grade is between 0 and 5, with 0 meaning Fail
    #  - date is at most today

    course_id = db.Column(db.Integer, db.ForeignKey("course.course_id", ondelete="CASCADE"), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.student_id", ondelete="CASCADE"), primary_key=True)
    grade = db.Column(db.Integer, CheckConstraint('grade IN (0, 5)'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    # VALIDATORS

    # date is at most today
    @validates("date")
    def validate_date(self, key, date):
        assert date <= datetime.date.today()
        return date

    # RELATIONSHIPS
    #  - only one student and one course for each assessment (useList=False)

    student = db.relationship("Student", back_populates="assessments", uselist=False)
    course = db.relationship("Course", back_populates="assessments", uselist=False)

    # TABLENAME
    #   allows direct reference between Student and Course based on all the associations;
    #   it works in the same way as the db.Table construct

    __tablename__ = 'assessments'


class Student(db.Model):

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
        assert date_of_birth < datetime.date.today()
        return date_of_birth

    # ssn is valid for given date_of_birth
    @validates("ssn")
    def validate_ssn(self, key, ssn):
        assert ssn[0:6] == self.date_of_birth.strftime("%d%m%y")
        return ssn

    # RELATIONSHIPS
    #  - all of the student's assessments

    assessments = db.relationship("Assessment", back_populates="student")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of courses the student
    #   has assessments for
    # WARNING: changes will be reflected only after the Session has ended
    #   info at https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    courses = db.relationship("Course", secondary="assessments", back_populates="students", viewonly=True)


class Course(db.Model):

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

    assessments = db.relationship("Assessment", back_populates="course")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of students that have assessments
    #   for this course
    # WARNING: changes will be reflected only after the Session has ended
    #   info at: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    students = db.relationship("Student", secondary="assessments", back_populates="courses", viewonly=True)
