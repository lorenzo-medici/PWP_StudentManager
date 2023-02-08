from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.future import Engine

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Assessment(db.Model):
    # needed for optional stuff defined later
    __tablename__ = 'assessments'

    student_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
                          primary_key=True)  # arguably ondelete="SET NULL"

    grade = db.Column(db.Integer, nullable=False)

    student = db.relationship("Student", back_populates="assessments", uselist=False)
    course = db.relationship("Course", back_populates="assessments", uselist=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    assessments = db.relationship("Assessment", back_populates="student")

    # optional to give direct connection between student and course
    # WARNING: inconsistent during a session
    courses = db.relationship("Course", secondary="assessments", back_populates="students", viewonly=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(64), nullable=False)

    assessments = db.relationship("Assessment", back_populates="course")

    # optional to give direct connection between student and course
    # WARNING: inconsistent during a session
    students = db.relationship("Student", secondary="assessments", back_populates="courses", viewonly=True)
