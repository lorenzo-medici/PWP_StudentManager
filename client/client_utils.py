"""
Utility functions specific to the API client
"""
import base64
import builtins
import json
import tempfile
import webbrowser
from io import BytesIO

from PIL import Image

from client.APIError import APIError
from client.client_constants import API_URL, API_KEY


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
            else:
                print(f"Value entered not in range [1-{len(options)}]!\n")
        except ValueError:
            print("Value entered is not an integer!\n")
            continue
        except (EOFError, KeyboardInterrupt):
            return -1


def submit_data(s, ctrl, data):
    """
    Note: This class is taken from the example MusicMeta API client, shown in the exercise 4 material
        on Lovelace.
    It is contained in the script downloadable at
    https://lovelace.oulu.fi/file-download/embedded/ohjelmoitava-web/ohjelmoitava-web/pwp-musicmeta-submit-script-py/

    submit_data(s, ctrl, data) -> requests.Response

    Sends *data* provided as a JSON compatible Python data structure to the API
    using URI and HTTP method defined in the *ctrl* dictionary (a Mason @control).
    The data is serialized by this function and sent to the API. Returns the
    response object provided by requests.
    """

    resp = s.request(
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
    for c in json_controls:
        try:
            control_tuple = (c, json_controls[c]["method"], json_controls[c]["title"], json_controls[c]["href"])
        except KeyError:
            control_tuple = (c, "GET", c, json_controls[c]["href"])

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

    for k, v in resp_body.items():
        if k not in ["@namespaces", "@controls"]:
            match type(v):

                case builtins.list:
                    for idx, elem in enumerate(v):
                        print(f'{indent}{idx + 1}:')
                        display_get_body(elem, indent=indent + '  ')

                case builtins.dict:
                    display_get_body(v, indent=indent + '  ')

                case builtins.str | builtins.int:
                    print(f"{indent}{k}: {v}")


def do_get(s, url):
    """
    This function executes a GET request to the specified URL, and displays the resulting response.
    Returns the json response if successful, otherwise raises APIError.
    :param s: a session object
    :param url: the url to request from the API
    :return: the json response if successful
    :raises APIError: if the status code of the request is not 200
    """
    resp_body = s.get(url)

    if resp_body.status_code == 200:
        match resp_body.headers['Content-Type']:

            # most pages
            case 'application/vnd.mason+json':
                json_body = resp_body.json()
                display_get_body(json_body)
                return json_body

            # static pages (profiles and link-relations)
            case 'text/html':
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
                    url = 'file://' + f.name
                    f.write(resp_body.content.decode('utf-8'))
                webbrowser.open(url)

                return {}

            # profile picture pages
            case 'application/vnd.mason+jpeg':
                json_body = resp_body.json()
                image_bytes = BytesIO(base64.b64decode(json_body["picture"]))
                image_bytes.seek(0)
                propic_image = Image.open(image_bytes)

                propic_image.show()

                return json_body

    else:
        raise APIError(resp_body.status_code, resp_body.content, url)
