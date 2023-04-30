"""
This file contains the auxiliary service for our project.
It declares one route 'studentCard/<student_id>', initializes and starts the server.
"""
import base64
import os
import sys
from io import BytesIO

import requests
from PIL import Image, ImageFont, ImageDraw
from flask import Flask, Response

app = Flask(__name__)
SERVER_URL = ''
STUDENT_COLLECTION_HREF = ''

GET_TIMEOUT = 30


@app.route('/studentCard/<int:student_id>/')
def student_card_generator(student_id):
    """
    This function responds to GET requests on the '/studentCard/<student_id>' endpoint.
    It requests data from the StudentManager API about the student whose student_id is passed as
        parameter, and generates and returns the image of their student card, complete with their
        profile picture, full name, date of birth and student id.
    The student_id provided has to exist in the StudentManager API, otherwise error code 404
        will be returned.
    :param student_id: An integer representing an existing student_id in the API
    :return: 404 if the student_id doesn't exist
    :return: 503 if the StudentManager API answers with stuatus code different than 200
    :return: 200 and the image of the student card, if no error happens
    """
    student_collection = requests.get(SERVER_URL + STUDENT_COLLECTION_HREF, timeout=GET_TIMEOUT)

    if student_collection.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    student_href = ''

    for student in student_collection.json()["items"]:
        if str(student["student_id"]) == str(student_id):
            student_href = student["@controls"]["self"]["href"]
            break

    if student_href == '':
        return Response(f"Given student id {student_id} not found on the API server", 404)

    student_page = requests.get(SERVER_URL + student_href, timeout=GET_TIMEOUT)

    if student_page.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    student_body = student_page.json()

    name = student_body["first_name"]
    surname = student_body["last_name"]
    date_of_birth = student_body["date_of_birth"]

    picture_page = requests.get(SERVER_URL + student_body["@controls"]["studman:propic"]["href"],
                                timeout=GET_TIMEOUT)

    if picture_page.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    # propic_data contains exactly the same data you would read from a file
    # You can use it to compose the student card (probably encapsulate in an Image class
    #   or something similar)
    propic_bytes = BytesIO(base64.b64decode(picture_page.json()["picture"]))

    # Compose student card
    final_image = Image.open('static/Background.png')

    final_image.paste(Image.open(propic_bytes), (50, 50))

    drawer = ImageDraw.Draw(final_image)
    my_font = ImageFont.truetype("static/Helvetica.ttf", size=40)

    drawer.text((600, 150), 'Full name:', font=my_font, fill=(0, 0, 0))
    drawer.text((630, 200), f'{name} {surname}', font=my_font, fill=(0, 0, 0))

    drawer.text((600, 275), 'Date of birth:', font=my_font, fill=(0, 0, 0))
    drawer.text((630, 325), f'{date_of_birth}', font=my_font, fill=(0, 0, 0))

    drawer.text((600, 400), 'Student ID:', font=my_font, fill=(0, 0, 0))
    drawer.text((630, 450), f'{student_id}', font=my_font, fill=(0, 0, 0))

    # for returning, export the student card image as jpeg into the payload variable
    #   (it must contain the data you would directly write to a file), then simply return
    payload = BytesIO()
    final_image.save(payload, 'JPEG', quality=100)
    payload.seek(0)

    return Response(payload, 200, mimetype='image/jpeg')

    # then on the client side, you simply need to do
    # resp = requests.get(f'{auxiliary_server_url}/studentCard/{student_id}/', timeout=GET_TIMEOUT)
    # student_card_image = Image.open(BytesIO(resp.content))
    #
    # Then you can do student_card_image.show() to open a window with the picture in it
    #   or student_card_image.save(<path>, 'JPEG', quality=100) to save it to a file

    # You can do the same thing for the profile picture image that you get from the API
    # The only thing that you need to change is
    # picture_body = picture_page.json()
    # and use base64.b64decode(picture_body["picture"]) instead of resp.content
    # If you need help ask Lorenzo


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print(f"Invalid number of arguments. \
        Usage: python {os.path.basename(__file__)} <port> <apiUrl>")
        sys.exit(-1)

    try:
        PORT = int(sys.argv[1])
        if PORT < 1024 or PORT > 49151:
            print("Local PORT not in valid range [1024, 49151]!")
            sys.exit(-1)

        SERVER_URL = sys.argv[2]
        api_entrypoint = requests.get(SERVER_URL + '/api/', timeout=GET_TIMEOUT)

        if api_entrypoint.status_code != 200:
            print(f"Error {api_entrypoint.status_code} on remote server")
            sys.exit(-3)

        STUDENT_COLLECTION_HREF = api_entrypoint.json()["@controls"]["studman:students-all"]["href"]

        app.run(host="localhost", port=PORT)

    except ValueError as e:
        print(f"Invaid PORT parameter: not an integer!{e}")
        sys.exit(-1)

    except requests.ConnectionError:
        print(f'URL does not point to the StudentManager API: {SERVER_URL}')
        sys.exit(-2)
