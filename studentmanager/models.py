import datetime

import click
from flask.cli import with_appcontext
from sqlalchemy import event, CheckConstraint
from sqlalchemy.future import Engine
from sqlalchemy.orm import validates

from studentmanager import db
from studentmanager.utils import is_valid_ssn


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Assessment(db.Model):
    """A class that represents an assessment. Contains references to the student and the course it is related to.
    Additionally, stores the grade accomplished and the date of the assessment. The grade must be between 0 (Fail) and 5.
    The date must be at most the current day-"""

    # COLUMNS
    #
    # constraints
    #  - grade is between 0 and 5, with 0 meaning Fail
    #  - date is at most today

    course_id = db.Column(db.Integer, db.ForeignKey("course.course_id", ondelete="CASCADE"), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.student_id", ondelete="CASCADE"), primary_key=True)
    grade = db.Column(db.Integer, CheckConstraint('grade IN (0,1,2,3,4,5)'), nullable=False)
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
    """A class that represents a student. Contains personal information, as well as the assessments a student has, and all the courses they have assessments for.
    The date of birth has to be in the past, and the Social Security Number has to be valid for the given date, as well as unique."""

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
        assert is_valid_ssn(ssn, self.date_of_birth)
        return ssn

    # RELATIONSHIPS
    #  - all of the student's assessments

    assessments = db.relationship("Assessment", cascade="all, delete-orphan", back_populates="student")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of courses the student
    #   has assessments for
    # WARNING: changes will be reflected only after the Session has ended
    #   info at https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    courses = db.relationship("Course", secondary="assessments", back_populates="students", viewonly=True)


class Course(db.Model):
    """A class that represents a course. Stores the course name, code, teacher and ects. Addittionally, stores all the assessments for the course, as well as all the students that have an assessment for it.
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

    assessments = db.relationship("Assessment", cascade="all, delete-orphan", back_populates="course")

    # DIRECT REFERENCE
    #   using Assessment as it was a db.Table, we have a reference to the list of students that have assessments
    #   for this course
    # WARNING: changes will be reflected only after the Session has ended
    #   info at: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

    students = db.relationship("Student", secondary="assessments", back_populates="courses", viewonly=True)


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()


@click.command("testgen")
@with_appcontext
def generate_test_data():
    s1 = Student(
        first_name='Draco',
        last_name='Malfoy',
        date_of_birth=datetime.date.fromisoformat('1980-06-05'),
        ssn='050680-4123'
    )

    s2 = Student(
        first_name='Harry',
        last_name='Potter',
        date_of_birth=datetime.date.fromisoformat('1980-07-31'),
        ssn='310780-8245'
    )

    s3 = Student(
        first_name='Hermione',
        last_name='Granger',
        date_of_birth=datetime.date.fromisoformat('1979-09-19'),
        ssn='190979-1095'
    )

    c1 = Course(
        title='Transfiguration',
        teacher='Minerva Mcgonagall',
        code='004723',
        ects=5
    )

    c2 = Course(
        title='Defence Against the Dark Arts',
        teacher='Professur Severus Snape',
        code='006031',
        ects=8
    )

    a_s1_c1 = Assessment(
        student=s1,
        course=c1,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s1_c2 = Assessment(
        student=s1,
        course=c2,
        grade=4,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    a_s2_c1 = Assessment(
        student=s2,
        course=c1,
        grade=3,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s2_c2 = Assessment(
        student=s2,
        course=c2,
        grade=4,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    a_s3_c1 = Assessment(
        student=s3,
        course=c1,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-08')
    )

    a_s3_c2 = Assessment(
        student=s3,
        course=c2,
        grade=5,
        date=datetime.date.fromisoformat('1993-02-17')
    )

    db.session.add(s1)
    db.session.add(s2)
    db.session.add(s3)

    db.session.add(c1)
    db.session.add(c2)

    db.session.add(a_s1_c2)
    db.session.add(a_s2_c1)
    db.session.add(a_s2_c2)
    db.session.add(a_s3_c1)
    db.session.add(a_s3_c2)

    db.session.commit()
