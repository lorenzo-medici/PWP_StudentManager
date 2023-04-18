"""
This module contains the ProfilePicutreItem class, responsible for returning
a student's profile picture.
NOTE: this is a protoype used only in our project's auxiliary service. For this reason,
it returns the same picture for all students, reading it directly from a file, and doesn't
implement PUT or DELETE methods
"""
import base64
import json
import os

from flasgger import swag_from
from flask import request, Response, url_for
from flask_restful import Resource

from studentmanager import DOC_FOLDER, NAMESPACE, LINK_RELATIONS_URL
from studentmanager.builder import StudentManagerBuilder
from studentmanager.constants import STUDENT_PROFILE, PROFILE_PICTURE_MIMETYPE, PICTURE_FOLDER


class ProfilePictureItem(Resource):
    """
    Class that represents the profile picture of a single student, reachable at
        '/api/students/<student_id>/profilePicture'
    The only available method is GET

    NOTE: this is a protoype used only in our project's auxiliary service. For this reason,
        it returns the same picture for all students, reading it directly from a file, and doesn't
        implement PUT or DELETE methods
    """

    # must explicitly specify current working directory because otherwise
    # it will look in in cache dir
    @swag_from(os.getcwd() + f"{DOC_FOLDER}picture_item/get.yml")
    def get(self, student):
        """
        Returns the profile picture of the student
        :param student: takes a student object containing the information about the student
        """

        # To change with the student's id for full implementation
        picture_filename = 'sample.jpeg'
        with open(os.getcwd() + f"{PICTURE_FOLDER}{picture_filename}", "rb") as img_file:
            picture_data = img_file.read()
            payload = base64.b64encode(picture_data).decode("utf-8")

        body = StudentManagerBuilder({'picture': payload})

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", request.path)
        body.add_control("profile", STUDENT_PROFILE)
        body.add_control("studman:student", url_for('api.studentitem', student=student))

        return Response(json.dumps(body), 200, mimetype=PROFILE_PICTURE_MIMETYPE)

        # on the auxiliary service:
        #  resp = requests.get(...)
        #  body = json.loads(resp.decode('utf-8'))
        #  image_data = base64.b64decode(body["picture"])
        #       You can now open a file in "wb" or "xb" mode and write image_data in there
        #       (preferably temp file) or use directly for composing the student picture
