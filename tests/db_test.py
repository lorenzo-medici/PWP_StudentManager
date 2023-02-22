import datetime
import os
import tempfile

import pytest
from sqlalchemy import event, Engine
from sqlalchemy.exc import IntegrityError

from studentmanager import create_app, db
from studentmanager.models import Student, Course, Assessment


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app(config)

    app.app_context().push()

    db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_fname)


def test_create_student(app):
    """Tests successful creation of a student entry in the database"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )

    db.session.add(student)
    db.session.commit()
    assert Student.query.count() == 1


def test_unique_ssn(app):
    """Tests the uniqueness contraint for Social Security Numbers"""
    student1 = Student(
        first_name='name1',
        last_name='surname1',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    student2 = Student(
        first_name='name2',
        last_name='surname2',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )

    db.session.add(student1)
    db.session.add(student2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_future_date_of_birth(app):
    """Tests the constraint for a date_of_birth in the past"""
    with pytest.raises(AssertionError):
        student = Student(
            first_name='name',
            last_name='surname',
            date_of_birth=datetime.date.today() + datetime.timedelta(days=1),
            ssn='280223X0000'
        )


def test_create_course(app):
    """Tests successful creation of a course entry in the database"""
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )

    db.session.add(course)
    db.session.commit()
    assert Course.query.count() == 1


def test_invalid_ects(app):
    """Tests the constraint for a number of ects greater than 0"""
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=0
    )

    db.session.add(course)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_unique_course_code(app):
    """Tests for the uniqueness constraint for course codes"""
    course1 = Course(
        title='course1',
        teacher='teacher1',
        code='123456',
        ects=1
    )
    course2 = Course(
        title='course2',
        teacher='teacher2',
        code='123456',
        ects=1
    )

    db.session.add(course1)
    db.session.add(course2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_create_assessment(app):
    """Tests successful creation of an assessment entry in the database"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )
    assessment = Assessment(
        student=student,
        course=course,
        grade=5,
        date=datetime.date.fromisoformat('2023-02-08')
    )

    db.session.add(assessment)
    db.session.commit()

    assert Assessment.query.count() == 1


def test_valid_grade(app):
    """Tests the constraint for a valid grade"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )
    assessment = Assessment(
        student=student,
        course=course,
        grade=-1,
        date=datetime.date.fromisoformat('2023-02-08')
    )

    db.session.add(assessment)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_future_assessment_date(app):
    """Tests the constraint for an assessment date not in the future"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )

    with pytest.raises(AssertionError):
        assessment = Assessment(
            student=student,
            course=course,
            grade=-1,
            date=datetime.date.today() + datetime.timedelta(days=1),
        )


def test_unique_assessment(app):
    """Tests the uniqueness constraint for a pair of student_it and course_id in Assessment"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )
    assessment1 = Assessment(
        student=student,
        course=course,
        grade=5,
        date=datetime.date.fromisoformat('2023-02-08')
    )
    assessment2 = Assessment(
        student=student,
        course=course,
        grade=4,
        date=datetime.date.fromisoformat('2023-02-07')
    )

    db.session.add(assessment1)
    db.session.add(assessment2)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_relationships(app):
    """Tests whether queries can be made on Assessment from its student and course, and the direct relationship between Student and Course"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )
    assessment = Assessment(
        student=student,
        course=course,
        grade=5,
        date=datetime.date.fromisoformat('2023-02-08')
    )

    db.session.add(assessment)
    db.session.commit()

    assert Assessment.query.filter_by(student=student).count() == 1
    assert Assessment.query.filter_by(course=course).count() == 1

    assert len(student.courses) == 1
    assert len(course.students) == 1


def test_foreign_key_on_delete(app):
    """Tests successful deletion of assessment entry when either the student or the course are deleted"""
    student = Student(
        first_name='name',
        last_name='surname',
        date_of_birth=datetime.date.fromisoformat('2023-02-01'),
        ssn='010223X0000'
    )
    course = Course(
        title='course',
        teacher='teacher',
        code='123456',
        ects=1
    )
    assessment = Assessment(
        student=student,
        course=course,
        grade=5,
        date=datetime.date.fromisoformat('2023-02-08')
    )

    db.session.add(assessment)
    db.session.commit()

    Student.query.filter_by(student_id=student.student_id).delete()
    db.session.commit()

    assert Assessment.query.count() == 0

    db.session.add(assessment)
    db.session.commit()

    Course.query.filter_by(course_id=course.course_id).delete()
    db.session.commit()

    assert Assessment.query.count() == 0
