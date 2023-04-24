import base64
import os
import sys

import requests
from flask import Flask, Response

app = Flask(__name__)
server_url = ''
student_collection_href = ''


@app.route('/studentCard/<student_id>/')
def student_card_generator(student_id):
    student_collection = requests.get(server_url + student_collection_href)

    if student_collection.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    student_href = ''

    collection_body = student_collection.json()

    for student in student_collection.json()["items"]:
        if str(student["student_id"]) == student_id:
            student_href = student["@controls"]["self"]["href"]
            break

    if student_href == '':
        return Response(f"Given student id {student_id} not found on the API server", 404)

    student_page = requests.get(server_url + student_href)

    if student_page.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    student_body = student_page.json()

    name = student_body["first_name"]
    surname = student_body["last_name"]
    date_of_birth = student_body["date_of_birth"]

    picture_href = student_body["@controls"]["studman:propic"]["href"]

    picture_page = requests.get(server_url + picture_href)

    if picture_page.status_code != 200:
        return Response(f"API server responded with code {student_collection.status_code}", 503)

    picture_body = picture_page.json()

    # image_data contains exactly the same data you would read from a file
    # You can use it to compose the student card (probably encapsulate in an Image class
    #   or something similar)
    image_data = base64.b64decode(picture_body["picture"])

    # Compose student card

    student_card = ''

    # for returning, export the student card image as jpeg into the student_card variable
    #   (it must contain the data you would directly write to a file), then simply return
    return Response(image_data, 200, mimetype='image/jpeg')

    # then on the client side, you simply need to do
    # resp = requests.get(f'{auxiliary_server_url}/studentCard/{student_id}/')
    # with open(f'StudentCard_{student_id}.jpeg', 'wb') as f:
    #     f.write(resp.content)
    #
    # Now the file contains the student card image


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print(f"Invalid number of arguments. \
        Usage: python {os.path.basename(__file__)} <port> <apiUrl>")
        exit(-1)

    try:
        port = int(sys.argv[1])
        if port < 1024 or port > 49151:
            print("Local port not in valid range [1024, 49151]!")
            exit(-1)

        server_url = sys.argv[2]
        api_entrypoint = requests.get(server_url + '/api/')

        if api_entrypoint.status_code != 200:
            print(f"Error {api_entrypoint.status_code} on remote server")
            exit(-3)

        student_collection_href = api_entrypoint.json()["@controls"]["studman:students-all"]["href"]

        app.run(host="localhost", port=port)

    except ValueError as e:
        print(f"Invaid port paramter: not an integer!{e.with_traceback()}")
        exit(-1)

    except requests.ConnectionError:
        print(f'URL does not point to the StudentManager API: {server_url}')
        exit(-2)
