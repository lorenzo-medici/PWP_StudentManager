import json

from flask import url_for, request, Response

from studentmanager.constants import ERROR_PROFILE, MASON
from studentmanager.models import Student, Course, Assessment


# Provided in Exercise 3 material on Lovelace

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.

    Note that child classes should set the *DELETE_RELATION* to the application
    specific relation name from the application namespace. The IANA standard
    does not define a link relation for deleting something.
    """

    DELETE_RELATION = ""

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, name_space, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str name_space: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][name_space] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding DELETE type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        self.add_control(
            "studman:delete",
            href,
            method="DELETE",
            title=title,
        )


class StudentManagerBuilder(MasonBuilder):
    """
    Extends MasonBuilder to expose utility control functions specific to our project.
    """

    def add_control_all_students(self):
        """
        Adds a control that points to the collection of all students with GET method.
        """
        self.add_control(
            "studman:students-all",
            url_for('api.studentcollection'),
            method="GET",
            title="The collection of all students"
        )

    def add_control_all_courses(self):
        """
        Adds a control that points to the collection of all courses with GET method.
        """
        self.add_control(
            "studman:courses-all",
            url_for("api.coursecollection"),
            method="GET",
            title="The collection of all courses"
        )

    def add_control_all_assessments(self):
        """
        Adds a control that points to the collection of all assessments with GET method.
        """
        self.add_control(
            "studman:assessments-all",
            url_for('api.assessmentcollection'),
            method="GET",
            title="The collection of all assessments"
        )

    def add_control_add_student(self):
        """
        Adds a control that allows to add a student, points to StudentCollection with POST method.
        Contains the schema for a valid POST request of a student.
        """
        self.add_control_post(
            "studman:add-student",
            "Add a new student",
            url_for('api.studentcollection'),
            Student.json_schema()
        )

    def add_control_add_course(self):
        """
        Adds a control that allows to add a course, points to CourseCollection with POST method.
        Contains the schema for a valid POST request of a course.
        """
        self.add_control_post(
            "studman:add-course",
            "Add a new course",
            url_for('api.coursecollection'),
            Course.json_schema()
        )

    def add_control_add_assessment(self):
        """
        Adds a control that allows to add an assessment, points to AssessmentCollection
            with POST method.
        Contains the schema for a valid POST request of an assessment.
        """
        self.add_control_post(
            "studman:add-assessment",
            "Add a new assessment",
            url_for('api.assessmentcollection'),
            Assessment.json_schema()
        )

    def add_control_get_student(self, student):
        """
        Adds a control to retrieve one student with GET method.
        :param student: database instance of the student for which to generate the URL.
        """
        self.add_control(
            "studman:student",
            url_for('api.studentitem', student=student),
            method="GET",
            title="Get the student this assessment is assigned to"
        )

    def add_control_get_course(self, course):
        """
        Adds a control to retrieve one course with GET method.
        :param course: database instance of the course for which to generate the URL.
        """
        self.add_control(
            "studman:course",
            url_for('api.courseitem', course=course),
            method="GET",
            title="Get the course this assessment is assigned to"
        )

    def add_control_student_assessments(self, student):
        """
        Adds a control that points to the collection of a student's assessments with GET method.
        :param student: database instance of the student for which to get the assessments.
        """
        self.add_control(
            "studman:student-assessments",
            url_for('api.studentassessmentcollection', student=student),
            method="GET",
            title="Get all the assessments of a student"
        )

    def add_control_course_assessments(self, course):
        """
        Adds a control that points to the collection of a course's assessments with GET method.
        :param course: database instance of the course for which to get the assessments.
        """
        self.add_control(
            "studman:course-assessments",
            url_for('api.courseassessmentcollection', course=course),
            method="GET",
            title="Get all the assessments of a course"
        )


# From Exercise 3 material on Lovelace
def create_error_response(status_code, title, message=None):
    """
    Utility function that creates a Mason error response
    :param status_code: integer that represents a valid HTTP status code
    :param title: The title of the error (e.g. `Bad Request', 'Conflict')
    :param message: Longer message explaining what caused the error
    :return: A populated Response object
    """
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)
