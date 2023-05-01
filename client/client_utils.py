"""
Utility functions specific to the API client
"""
import base64
import builtins
import json
import webbrowser
from io import BytesIO

import matplotlib.pyplot as plt
import requests
from PIL import Image

from api_error import APIError
from client_constants import API_URL, API_KEY, AUXILIARY_SERVICE_URL, CLIENT_GET_TIMEOUT


def option_picker(prompt, options):
    """
    This function takes a list of options to be displayed to the user, and returns the index of the
        selected one
    :param prompt: String containing the question to ask to the user
    :param options: list of options, their type must have a valid string representation
    :return: the index (starting from 0) of the selected option
    :return: -1 if the user inputs EOF
    """
    while True:
        print(prompt)
        for idx, element in enumerate(options):
            print(f"[{idx + 1}] {element}")
        try:
            i = input(f"Enter number in range [1-{len(options)}]: ")
            pick = int(i)
            if 1 <= pick <= len(options):
                return pick - 1
            print(f"Value entered not in range [1-{len(options)}]!\n")
        except ValueError:
            print("Value entered is not an integer!\n")
            continue
        except (EOFError, KeyboardInterrupt):
            return -1


def submit_data(session, ctrl, data):
    """
    Note: This class is taken from the example MusicMeta API client, shown in the exercise 4
        material on Lovelace.
    It is contained in the script downloadable at
    https://lovelace.oulu.fi/file-download/embedded/ohjelmoitava-web/ohjelmoitava-web/pwp-musicmeta-submit-script-py/

    submit_data(s, ctrl, data) -> requests.Response

    Sends *data* provided as a JSON compatible Python data structure to the API
    using URI and HTTP method defined in the *ctrl* dictionary (a Mason @control).
    The data is serialized by this function and sent to the API. Returns the
    response object provided by requests.
    """

    resp = session.request(
        ctrl["method"],
        API_URL + ctrl["href"],
        data=json.dumps(data),
        headers={"Content-type": "application/json",
                 "Studentmanager-Api-Key": API_KEY}
    )
    return resp


def process_controls(json_controls):
    """
    Converts the "@controls" dictionary received from the API into a list of tuples storing
        (control_name, method, title, href)
    This allows easier access and searching to individual controls than a nested dictionary
        structure
    :param json_controls: body["@controls"] dictionary received from the API
    :return: list of tuples containing (control_name, method, title, href)
    """
    result = []
    for ctrl in json_controls:
        try:
            control_tuple = (ctrl,
                             json_controls[ctrl]["method"],
                             json_controls[ctrl]["title"],
                             json_controls[ctrl]["href"])
        except KeyError:
            control_tuple = (ctrl, "GET", ctrl, json_controls[ctrl]["href"])

        result.append(control_tuple)

    return result


def convert_value(value, schema_props):
    """
    This function is a modified version of the one showcased in the Exercise 4 material
        on Lovelace

    Converts string into correct object type
    :param value: string
    :param schema_props: dictionary object containing the field's properties
    :return: the converted object
    """
    if schema_props["type"] == "integer":
        value = int(value)
    return value


def prompt_from_schema(session, ctrl):
    """
    This function is a slightly modified version of the one developed for the
        "The Schemanator - Terminal Edition" task in Exercise 4
    Changes including returning the request body, and prompting the user for optional
        parameters as well

    Function that prompts the user to input all required data from
        given schema
    :param session: session object used to make the request if needed
    :param ctrl: control containing the schema object or the schemaUrl to retrieve it
    :return: the request body built according to the schema
    """
    try:
        schema = ctrl["schema"]
    except KeyError:
        schema = session.get(API_URL + ctrl["schemaUrl"]).json()

    request_body = {}

    for name in schema["required"]:
        props = schema["properties"][name]

        string_value = input(f'{props["description"]}: ')
        conv_value = convert_value(string_value, props)
        print(f'{conv_value} {type(conv_value)}')

        request_body[name] = conv_value

    for opt_name in schema["properties"]:
        if opt_name not in schema["required"]:
            props = schema["properties"][opt_name]

            string_value = input(f'{props["description"]} [Optional, leave blank if not needed]: ')

            if len(string_value) != 0:
                conv_value = convert_value(string_value, props)
                request_body[opt_name] = conv_value

    return request_body


def display_get_body(resp_body, indent=''):
    """
    This function prints the content of the dictionary passed as argument. It discards the
        elements labeled as @controls and @namespaces, to only display the meaningful data
    :param indent: optional indent for nested objects such as lists or dicts
    :param resp_body: a dictionary object to display
    """

    print('')
    for key, val in resp_body.items():
        if key not in ["@namespaces", "@controls"]:
            match type(val):

                case builtins.list:
                    print(f'{key}:')
                    for idx, elem in enumerate(val):
                        print(f'{indent}  {idx + 1}:')
                        display_get_body(elem, indent=indent + '    ')

                case builtins.dict:
                    display_get_body(val, indent=indent + '  ')

                case builtins.str | builtins.int:
                    print(f"{indent}{key}: {val}")


def do_get(session, url):
    """
    This function executes a GET request to the specified URL, and displays the resulting response.
    Returns the json response if successful, otherwise raises APIError.
    :param session: a session object
    :param url: the url to request from the API
    :return: the json response if successful
    :raises APIError: if the status code of the request is not 200
    """
    resp_body = session.get(url)

    if resp_body.status_code == 200:
        match resp_body.headers['Content-Type']:

            # most pages
            case 'application/vnd.mason+json':
                json_body = resp_body.json()
                display_get_body(json_body)
                return json_body

            # static pages (profiles and link-relations)
            case 'text/html; charset=utf-8':
                print(f"Opened static page at {url} in webbrowser")
                webbrowser.open(url, new=1, autoraise=True)

                return {}

            # profile picture pages
            case 'application/vnd.mason+jpeg':
                json_body = resp_body.json()
                image_bytes = BytesIO(base64.b64decode(json_body["picture"]))
                image_bytes.seek(0)
                propic_image = Image.open(image_bytes)

                plt.imshow(propic_image)
                plt.axis('off')

                plt.show()  # Default is a blocking call

                return json_body

    else:
        raise APIError(resp_body.status_code, resp_body.content, url)


def handle_student_id_option(body):
    """
    This function handles the selection of an existing student ID when the relevan option
        is picked by the user
    :param body: the body of the student collection, in which the ID will be searched
    :return: a tuple containing the control name, method, title and href
    """
    while True:
        id_str = input("Please input the student ID: ")
        try:
            student_id = int(id_str)

            for s_dict in body["items"]:
                if s_dict["student_id"] == student_id:
                    return ("studman:student",
                            "GET",
                            "Get a student",
                            s_dict["@controls"]["self"]["href"])
            print("The inserted course ID doesn't exist!\n")
        except ValueError:
            print("Not an integer!\n")


def handle_course_id_option(body):
    """
    This function handles the selection of an existing course ID when the relevan option
        is picked by the user
    :param body: the body of the course collection, in which the ID will be searched
    :return: a tuple containing the control name, method, title and href
    """
    while True:
        id_str = input("Please input the course ID: ")
        try:
            course_id = int(id_str)

            for c_dict in body["items"]:
                if c_dict["course_id"] == course_id:
                    return ("studman:course",
                            "GET",
                            "Get a course",
                            c_dict["@controls"]["self"]["href"])
            print("The inserted course ID doesn't exist!\n")
        except ValueError:
            print("Not an integer!\n")


def handle_assessment_option(body, last_control):
    """
    This function handles the selection of an existing assessment, based on the pair of
        course ID and student ID
    :param body: the body of the assessment collection, in which the assessment will be searched,
        it could be a StudentAssessmentCollection, CourseAssessmentCollection or a simple
        AssessmentCollection
    :param last_control: the last control followed by the client, distinguishes between the three
        collections of assessments
    :return: a tuple containing the control name, method, title and href
    """
    while True:
        id_str = input(
            "Please input the course ID and student ID separated by a space: "
        )
        try:
            ids = id_str.split(' ')
            if len(ids) != 2:
                print("Input format not valid!\n")
                break

            c_id = int(ids[0])
            s_id = int(ids[1])
            for a_dict in body["items"]:
                if a_dict["course_id"] == c_id and a_dict["student_id"] == s_id:
                    match last_control:
                        case "studman:course-assessments":
                            return ("studman:course-assessment",
                                    "GET",
                                    "Get a course's assessment",
                                    a_dict["@controls"]["self"]["href"])
                        case "studman:student-assessments":
                            return ("studman:student-assessment",
                                    "GET",
                                    "Get a student's assessment",
                                    a_dict["@controls"]["self"]["href"])
                        case "studman:assessments-all":
                            return ("studman:assessment",
                                    "GET",
                                    "Get an assessment",
                                    a_dict["@controls"]["self"]["href"])
            print("The inserted pair of course ID and student ID doesn't exist!\n")
        except ValueError:
            print("Not an integer!\n")


def generate_student_id_card():
    """
    This function requests the student ID card from the auxiliary service, displays it to the user,
        and saves it to a file <student_id>.jpeg
    """
    student_id = input("Please input the student ID: ")

    image_resp = requests.get(f'{AUXILIARY_SERVICE_URL}/studentCard/{student_id}/',
                              timeout=CLIENT_GET_TIMEOUT, stream=True)
    image_bytes = BytesIO(image_resp.content)
    image_bytes.seek(0)
    student_card_image = Image.open(image_bytes)

    plt.imshow(student_card_image)
    plt.axis('off')
    plt.show()  # Default is a blocking call
    student_card_image.save(f'{student_id}.jpeg', 'JPEG', quality=100)

    print(f"Student ID card saved as {student_id}.jpeg")


def last_get_control_mapper(last_get_control):
    """
    Maps the last control to the current control when following a "collection" hypermedia
        link. This is important to display the correct options in the next iteration
    :param last_get_control: the last picked control
    :return: the current hypermedia control
    """
    mappings = {
        "studman:course":
            "studman:courses-all",
        "studman:student":
            "studman:students-all",
        "studman:assessment":
            "studman:assessments-all",
        "studman:course-assessment":
            "studman:course-assessments",
        "studman:student-assessment":
            "studman:student-assessments"
    }

    return mappings[last_get_control]
