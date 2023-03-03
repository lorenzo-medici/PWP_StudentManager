# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
import datetime
import json
import os
import tempfile

import pytest
from werkzeug.datastructures import Headers

from studentmanager import create_app, db
from studentmanager.models import Assessment, Student, Course


@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_db()

    yield app.test_client()

    with app.app_context():
        db.session.remove()

    os.close(db_fd)
    os.unlink(db_fname)



def _populate_db():
    s1 = Student(
        first_name='Draco',
        last_name='Malfoy',
        date_of_birth=datetime.date.fromisoformat('1980-06-05'),
        ssn='050680-6367'
    )

    s2 = Student(
        first_name='Harry',
        last_name='Potter',
        date_of_birth=datetime.date.fromisoformat('1980-07-31'),
        ssn='310780-6176'
    )

    s3 = Student(
        first_name='Hermione',
        last_name='Granger',
        date_of_birth=datetime.date.fromisoformat('1979-09-19'),
        ssn='190979-8400'
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


class TestStudentCollection(object):
    RESOURCE_URL = "/api/students/"

    def test_get(self, client):
        """Succesfully gets all students"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        print(resp.data)
        body = json.loads(resp.data)
        assert len(body) == 3
        for item in body:
            assert "first_name" in item
            assert "last_name" in item
            assert "date_of_birth" in item
            assert "ssn" in item

    def test_post_valid_request(self, client):
        """Succesfully adds a new student"""
        valid = _get_student_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["ssn"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["first_name"] == valid["first_name"]
        assert body["last_name"] == valid["last_name"]
        assert body["date_of_birth"] == valid["date_of_birth"]
        assert body["ssn"] == valid["ssn"]

    def test_post_missing_field(self, client):
        """Tries to post a student with a missing field"""
        valid = _get_student_json()
        valid.pop("first_name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_conflict(self, client):
        """Tries to post a student with a conflict on existing ssn"""
        valid = _get_existing_student_json()
        valid["name"] = "name2"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

    def test_post_invalid_date(self, client):
        """Tries to post a student with an invalid date_of_birth"""
        valid = _get_student_json()
        valid["date_of_birth"] = 'XXXXXX'
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestStudentItem(object):
    RESOURCE_URL = "/api/students/050680-6367/"
    INVALID_URL = "/api/students/XXXXXX-XXXX/"

    def test_get(self, client):
        """Succesfully gets an existing student"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["first_name"] == 'Draco'
        assert body["last_name"] == 'Malfoy'
        assert body["date_of_birth"] == '1980-06-05'
        assert body["ssn"] == '050680-6367'

    def test_get_invalid_url(self, client):
        """Tries to get a non existent student"""
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """Successfully modifies an existing student"""
        valid = _get_existing_student_json()

        valid["first_name"] = "Harry"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

    def test_put_wrong_content_type(self, client):
        """Tries to put a request with wrong content type"""
        resp = client.put(self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

    def test_put_invalid_url(self, client):
        """Tries to edit a non existent student"""
        valid = _get_existing_student_json()
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

    def test_put_conflict_ssn(self, client):
        """Tries to change an existing student's ssn into an already existing one"""
        valid = _get_existing_student_json()

        valid['date_of_birth'] = '1980-07-31'
        valid["ssn"] = "310780-6176"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

    def test_put_invalid_schema(self, client):
        """Tries to put a student with an invalid schema"""
        valid = _get_existing_student_json()
        valid.pop("first_name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_put_invalid_date(self, client):
        """Tries to put a student with an invalid date_of_birth"""
        valid = _get_existing_student_json()
        valid["date_of_birth"] = 'XXXXXX'
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client):
        """Successfully deletes an existing student"""
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_invalid_url(self, client):
        """Tries to delete a non existent course"""
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


def _get_student_json():
    return {"first_name": "name",
            "last_name": "surname",
            "date_of_birth": '1979-09-19',
            "ssn": '190979-520N'}


def _get_existing_student_json():
    return {"first_name": "Draco",
            "last_name": "Malfoy",
            "date_of_birth": '1980-06-05',
            "ssn": '050680-6367',
            "student_id": 1
            }
