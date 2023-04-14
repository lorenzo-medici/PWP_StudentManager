# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
import datetime
import json
import os
import shutil
import tempfile

import pytest
from flask.testing import FlaskClient
from jsonschema.validators import validate
from werkzeug.datastructures import Headers

from studentmanager import create_app, db
from studentmanager.constants import NAMESPACE
from studentmanager.models import Assessment, Student, Course, ApiKey

TEST_KEY = "verysafetestkey"


# From Lovelace material on Testing applications and Sensorhub example
def _check_namespace(client, response):
    """
    Checks that the "studman" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"][f"{NAMESPACE}"]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 200


# From Lovelace material on Testing applications and Sensorhub example

def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """
    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200


# From Lovelace material on Testing applications and Sensorhub example

def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


# From Lovelace material on Testing applications and Sensorhub example

def _check_control_put_method(ctrl, client, obj, obj_to_put, prop_name):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = obj_to_put
    body[prop_name] = obj[prop_name]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204


# From Lovelace material on Testing applications and Sensorhub example

def _check_control_post_method(ctrl, client, obj, obj_to_post):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = obj_to_post
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201


# https://stackoverflow.com/questions/16416001/set-http-headers-for-all-requests-in-a-flask-test
class AuthHeaderClient(FlaskClient):

    def open(self, *args, **kwargs):
        api_key_headers = Headers({
            'Studentmanager-Api-Key': TEST_KEY
        })
        headers = kwargs.pop('headers', Headers())
        headers.extend(api_key_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


# from example project
# based on http://flask.pocoo.org/docs/1.0/testing/
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    cache_dir_name = tempfile.mkdtemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True,
        "CACHE_DIR": cache_dir_name
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_db()

    app.test_client_class = AuthHeaderClient
    yield app.test_client()

    with app.app_context():
        db.session.remove()

    os.close(db_fd)
    os.unlink(db_fname)

    shutil.rmtree(cache_dir_name)


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

    c3 = Course(
        title='Advanced Defence Against the Dark Arts',
        teacher='Professur Severus Snape',
        code='006032',
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

    db_key = ApiKey(
        key=ApiKey.key_hash(TEST_KEY),
        admin=True
    )

    db.session.add(s1)
    db.session.add(s2)
    db.session.add(s3)

    db.session.add(c1)
    db.session.add(c2)
    db.session.add(c3)

    db.session.add(a_s1_c1)
    db.session.add(a_s1_c2)
    db.session.add(a_s2_c1)
    db.session.add(a_s2_c2)
    db.session.add(a_s3_c1)
    db.session.add(a_s3_c2)

    db.session.add(db_key)

    db.session.commit()


class TestEntrypoint(object):
    ENTRYPOINT_URL = '/api/'

    def test_get_entrypoint(self, client):
        """Gets the netrypoint will all necessary hypermedia controls"""
        resp = client.get(self.ENTRYPOINT_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method(f"{NAMESPACE}:students-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:courses-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)


class TestCourseCollection(object):
    RESOURCE_URL = "/api/courses/"

    def test_get(self, client):
        """Successfully gets all courses"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(f"{NAMESPACE}:add-course", client, body, _get_course_json())
        _check_control_get_method(f"{NAMESPACE}:students-all", client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "title" in item
            assert "teacher" in item
            assert "code" in item
            assert "ects" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post_valid_request(self, client):
        """Successfully adds a new course"""
        valid = _get_course_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert "Location" in resp.headers
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert "course_id" in body
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

    def test_post_invalid_admin_key(self, client):
        """Tries to post a course without valid admin key"""
        valid = _get_course_json()
        resp = client.post(self.RESOURCE_URL, json=valid, headers=Headers({'Studentmanager-Api-Key': "Invalid"}))
        assert resp.status_code == 403


class TestCourseItem(object):
    RESOURCE_URL = "/api/courses/1/"
    INVALID_URL = "/api/courses/X/"

    def test_get(self, client):
        """Successfully gets an existing course"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method(f"{NAMESPACE}:course-assessments", client, body)
        _check_control_put_method("edit", client, body, _get_existing_course_json(), "code")
        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        assert "course_id" in body
        assert body["title"] == 'Transfiguration'
        assert body["teacher"] == 'Minerva Mcgonagall'
        assert body["code"] == '004723'
        assert body["ects"] == 5

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
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
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
        valid["code"] = "006031"
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
        "title": 'Transfiguration',
        "teacher": 'Minerva Mcgonagall',
        "code": '004723',
        "ects": 5
    }


class TestStudentCollection(object):
    RESOURCE_URL = "/api/students/"

    def test_get(self, client):
        """Succesfully gets all students"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(f"{NAMESPACE}:add-student", client, body, _get_student_json())
        _check_control_get_method(f"{NAMESPACE}:courses-all", client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "student_id" in item
            assert "first_name" in item
            assert "last_name" in item
            assert "date_of_birth" in item
            assert "ssn" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post_valid_request(self, client):
        """Succesfully adds a new student"""
        valid = _get_student_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"] is not None
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert "student_id" in body
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
    RESOURCE_URL = "/api/students/1/"
    INVALID_URL = "/api/students/X/"

    def test_get(self, client):
        """Succesfully gets an existing student"""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method(f"{NAMESPACE}:student-assessments", client, body)
        _check_control_put_method("edit", client, body, _get_existing_student_json(), "student_id")
        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
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
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
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


class TestAssessmentCollection(object):
    ASSESSMENT_RESOURCE_URL = "/api/assessments/"

    COURSE_RESOURCE_URL_PREFIX = "/api/courses/"
    STUDENT_RESOURCE_URL_PREFIX = "/api/students/"
    ASSESSMENT_RESOURCE_URL_POSTFIX = "/assessments/"

    TEST_COURSE_ID = 1
    TEST_STUDENT_ID = 1

    def test_assessment_get(self, client):
        """Successfully gets all assessments from the assessment collection"""
        resp = client.get(self.ASSESSMENT_RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method(f"{NAMESPACE}:add-assessment", client, body, _get_assessment_json(client))
        _check_control_get_method(f"{NAMESPACE}:students-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:courses-all", client, body)
        assert len(body["items"]) == 6
        for item in body["items"]:
            assert "course_id" in item
            assert "student_id" in item
            assert "grade" in item
            assert "date" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_course_get(self, client):
        """Succesfully gets all assessments from course assessment collection"""
        resp = client.get(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX)

        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:course", client, body)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "course_id" in item
            assert "student_id" in item
            assert "grade" in item
            assert "date" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_student_get(self, client):
        """Succesfully gets all assessments from student assessment collection"""
        resp = client.get(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_STUDENT_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX)

        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:student", client, body)
        assert len(body["items"]) == 2
        for item in body["items"]:
            assert "course_id" in item
            assert "student_id" in item
            assert "grade" in item
            assert "date" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post_valid_request(self, client):
        """Succesfully adds a new assessment"""
        valid = _get_assessment_json(client)

        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"] is not None
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert "course_id" in body
        assert "student_id" in body
        assert "grade" in body
        assert "date" in body
        assert body["course_id"] == valid["course_id"]
        assert body["student_id"] == valid["student_id"]
        assert body["grade"] == valid["grade"]
        assert body["date"] == valid["date"]

    def test_post_missing_field(self, client):
        """Tries to post an assessment with a missing field"""
        valid = _get_assessment_json(client)
        valid.pop("course_id")
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_conflict(self, client):
        """Tries to post an assessment with a conflict on existing value and value combination"""
        valid = _get_existing_assessment_json()
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid)
        assert resp.status_code == 409

    def test_post_invalid_date(self, client):
        """Tries to post an assessment with an invalid date"""
        valid = _get_assessment_json(client)
        valid["date"] = 'XXXXXX'
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_invalid_grade(self, client):
        """Tries to post an assessment with an invalid date"""
        valid = _get_assessment_json(client)
        valid["grade"] = 2.5
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_course_post_wrong_content_type(self, client):
        """Tries to put a request with wrong content type"""
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, data="notjson",
                           headers=Headers({"Content-Type": "text"}))
        assert resp.status_code == 400

    def test_post_invalid_assessment_key(self, client):
        """Tries to post an assessment without a valid assessment key"""
        valid = _get_course_json()
        resp = client.post(self.ASSESSMENT_RESOURCE_URL, json=valid,
                           headers=Headers({'Studentmanager-Api-Key': "Invalid"}))
        assert resp.status_code == 403


class TestAssessmentItem(object):
    COURSE_RESOURCE_URL_PREFIX = "/api/courses/"
    STUDENT_RESOURCE_URL_PREFIX = "/api/students/"
    ASSESSMENT_RESOURCE_URL_POSTFIX = "/assessments/"

    TEST_COURSE_ID = 1
    TEST_STUDENT_ID = 1

    NONEXISTENT_COURSE_ID = 123
    NONEXISTENT_STUDENT_ID = 321

    def test_course_get(self, client):
        """Succesfully gets an existing assessment"""
        resp = client.get(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, _get_existing_assessment_json(), "course_id")
        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        _check_control_get_method(f"{NAMESPACE}:student", client, body)
        _check_control_get_method(f"{NAMESPACE}:course", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        assert body["course_id"] == 1
        assert body["student_id"] == 1
        assert body["grade"] == 5
        assert body["date"] == "1993-02-08"

    def test_student_get(self, client):
        """Succesfully gets an existing assessment"""
        resp = client.get(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, _get_existing_assessment_json(), "course_id")
        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        _check_control_get_method(f"{NAMESPACE}:student", client, body)
        _check_control_get_method(f"{NAMESPACE}:course", client, body)
        _check_control_get_method(f"{NAMESPACE}:assessments-all", client, body)
        assert body["course_id"] == 1
        assert body["student_id"] == 1
        assert body["grade"] == 5
        assert body["date"] == "1993-02-08"

    def test_get_course_invalid_url(self, client):
        """Tries to get a non existent assessment"""
        resp = client.get(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.NONEXISTENT_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.NONEXISTENT_STUDENT_ID) + "/")
        assert resp.status_code == 404

    def test_get_student_invalid_url(self, client):
        """Tries to get a non existent assessment"""
        resp = client.get(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.NONEXISTENT_STUDENT_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.NONEXISTENT_COURSE_ID) + "/")
        assert resp.status_code == 404

    def test_course_put(self, client):
        """Successfully modifies an existing assessment"""
        valid = _get_existing_assessment_json()
        valid["grade"] = 1
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 204

    def test_student_put(self, client):
        """Successfully modifies an existing assessment"""
        valid = _get_existing_assessment_json()
        valid["grade"] = 1
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 204

    def test_course_put_invalid_grade(self, client):
        """Successfully modifies an existing assessment"""
        valid = _get_existing_assessment_json()
        valid["grade"] = 2.5
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_student_put_invalid_grade(self, client):
        """Successfully modifies an existing assessment"""
        valid = _get_existing_assessment_json()
        valid["grade"] = 2.5
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_course_put_wrong_content_type(self, client):
        """Tries to put a request with wrong content type"""
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

    def test_student_put_wrong_content_type(self, client):
        """Tries to put a request with wrong content type"""
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

    def test_course_put_invalid_url(self, client):
        """Tries to edit a non existent assessment"""
        valid = _get_existing_assessment_json()
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.NONEXISTENT_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.NONEXISTENT_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 404

    def test_student_ut_invalid_url(self, client):
        """Tries to edit a non existent assessment"""
        valid = _get_existing_assessment_json()
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.NONEXISTENT_STUDENT_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.NONEXISTENT_COURSE_ID) + "/", json=valid)
        assert resp.status_code == 404

    def test_course_put_conflict_course_id_and_student_id(self, client):
        """Tries to change an existing assessment's value and value into an already existing one"""
        valid = _get_existing_assessment_json()
        valid['course_id'] = 2
        valid["student_id"] = 2
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 409

    def test_student_put_conflict_course_id_and_student_id(self, client):
        """Tries to change an existing assessment's value and value into an already existing one"""
        valid = _get_existing_assessment_json()
        valid['course_id'] = 2
        valid["student_id"] = 2
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 409

    def test_course_put_invalid_schema(self, client):
        """Tries to put a assessment with an invalid schema"""
        valid = _get_existing_assessment_json()
        valid.pop("grade")
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_student_put_invalid_schema(self, client):
        """Tries to put a assessment with an invalid schema"""
        valid = _get_existing_assessment_json()
        valid.pop("grade")
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_course_put_invalid_date(self, client):
        """Tries to put a assessment with an invalid date_of_birth"""
        valid = _get_existing_assessment_json()
        valid["date"] = 'XXXXXX'
        resp = client.put(self.COURSE_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_student_put_invalid_date(self, client):
        """Tries to put a assessment with an invalid date_of_birth"""
        valid = _get_existing_assessment_json()
        valid["date"] = 'XXXXXX'
        resp = client.put(self.STUDENT_RESOURCE_URL_PREFIX +
                          str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                          str(self.TEST_STUDENT_ID) + "/", json=valid)
        assert resp.status_code == 400

    def test_course_delete(self, client):
        """Successfully deletes an existing assessment"""
        resp = client.delete(self.COURSE_RESOURCE_URL_PREFIX +
                             str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                             str(self.TEST_STUDENT_ID) + "/")
        assert resp.status_code == 204

    def test_student_delete(self, client):
        """Successfully deletes an existing assessment"""
        resp = client.delete(self.STUDENT_RESOURCE_URL_PREFIX +
                             str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                             str(self.TEST_STUDENT_ID) + "/")
        assert resp.status_code == 204

    def test_course_delete_invalid_url(self, client):
        """Tries to delete a non existent course"""
        resp = client.delete(self.COURSE_RESOURCE_URL_PREFIX +
                             str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                             str(self.NONEXISTENT_STUDENT_ID) + "/")
        assert resp.status_code == 404

    def test_student_delete_invalid_url(self, client):
        """Tries to delete a non existent course"""
        resp = client.delete(self.STUDENT_RESOURCE_URL_PREFIX +
                             str(self.TEST_COURSE_ID) + self.ASSESSMENT_RESOURCE_URL_POSTFIX +
                             str(self.NONEXISTENT_STUDENT_ID) + "/")
        assert resp.status_code == 404


def _get_assessment_json(client):
    _remove_test_assessment_json(client)

    return {
        "course_id": 3,
        "student_id": 1,
        "grade": 4,
        "date": '1993-02-06'
    }


def _remove_test_assessment_json(client):
    client.delete("/courses/3/assessments/1/")


def _get_existing_assessment_json():
    return {
        "course_id": 1,
        "student_id": 1,
        "grade": 5,
        "date": '1993-02-08'
    }
