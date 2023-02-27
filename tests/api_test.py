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


class TestCourseCollection(object):
    RESOURCE_URL = "/api/courses/"

    def test_get(self, client):
        """Successfully gets all courses"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 2
        for item in body:
            assert "title" in item
            assert "teacher" in item
            assert "code" in item
            assert "ects" in item

    def test_post_valid_request(self, client):
        """Successfully adds a new course"""
        valid = _get_course_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["code"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["title"] == valid["title"]
        assert body["teacher"] == valid["teacher"]
        assert body["code"] == valid["code"]
        assert body["ects"] == valid["ects"]

    def test_post_missing_field(self, client):
        """Tries to post a course with a missing field"""
        valid = _get_course_json()
        valid.pop("title")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_non_integer_ects(self, client):
        """Tries to post a course with a non-integer ects value"""
        valid = _get_course_json()
        valid["ects"] = 8.5
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_conflict(self, client):
        """Posts a course with a conflict on an existing code"""
        valid = _get_existing_course_json()
        valid["title"] = "Potions"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409


class TestCourseItem(object):
    RESOURCE_URL = "/api/courses/006031/"
    INVALID_URL = "/api/courses/XXXXXX-XXXX/"

    def test_get(self, client):
        """Successfully gets an existing course"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["title"] == 'Defence Against the Dark Arts'
        assert body["teacher"] == 'Professur Severus Snape'
        assert body["code"] == '006031'
        assert body["ects"] == 8

    def test_get_invalid_url(self, client):
        """Tries to get a non existent course"""
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """Successfully modifies an existing course"""
        valid = _get_existing_course_json()

        valid["title"] = "Potions"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

    def test_put_wrong_content_type(self, client):
        """Tries to put a request with wrong content type"""
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

    def test_put_invalid_url(self, client):
        """Tries to edit a non existent course"""
        valid = _get_existing_course_json()

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

    def test_put_conflict_code(self, client):
        """Tries to change an existing course's code into an already existing one"""
        valid = _get_existing_course_json()
        # test with different code that conflicts with already present
        valid["code"] = "004723"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

    def test_put_invalid_schema(self, client):
        """Tries to put a couse with an invalid schema"""
        valid = _get_existing_course_json()
        # remove field for 400
        valid.pop("title")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_put_non_integer_ects(self, client):
        """Tries to put a course with a non-integer ects value"""
        valid = _get_existing_course_json()
        valid["ects"] = 8.5
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client):
        """Successfully deletes an existing course"""
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_invalid_url(self, client):
        """Tries to delete a non existent course"""
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


def _get_course_json():
    return {
        "title": "course1",
        "teacher": "teacher1",
        "code": "12345",
        "ects": 5,
    }


def _get_existing_course_json():
    return {
        "title": 'Defence Against the Dark Arts',
        "teacher": 'Professur Severus Snape',
        "code": '006031',
        "ects": 8
    }
