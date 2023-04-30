import sys
from io import BytesIO

import matplotlib.pyplot as plt
import requests
from PIL import Image

from client.APIError import APIError
from client.client_constants import API_URL, AUXILIARY_SERVICE_URL, CLIENT_GET_TIMEOUT
from client.client_utils import process_controls, option_picker, prompt_from_schema, submit_data, do_get


def application_loop(session, root_body):
    current_href = '/api/'
    current_body = root_body
    current_controls = root_body["@controls"]
    last_get_control = ''

    collection_controls = {
        "studman:students-all":
            ("studman:students-all",
             root_body["@controls"]["studman:students-all"]["method"],
             root_body["@controls"]["studman:students-all"]["title"],
             root_body["@controls"]["studman:students-all"]["href"]),
        "studman:courses-all":
            ("studman:courses-all",
             root_body["@controls"]["studman:courses-all"]["method"],
             root_body["@controls"]["studman:courses-all"]["title"],
             root_body["@controls"]["studman:courses-all"]["href"]),
        "studman:assessments-all":
            ("studman:assessments-all",
             root_body["@controls"]["studman:assessments-all"]["method"],
             root_body["@controls"]["studman:assessments-all"]["title"],
             root_body["@controls"]["studman:assessments-all"]["href"])
    }

    while True:
        try:
            # - add option to insert value for student, course or assessment depending on current_href
            # - add studman:students-all, courses-all and assessments-all to current_controls, if not
            #     already present
            # - add option to generate ID card
            # - add option to exit the client
            display_controls = process_controls(current_controls)

            for new_c in ["studman:students-all", "studman:courses-all", "studman:assessments-all"]:
                if new_c not in [i[0] for i in display_controls]:
                    display_controls.append(collection_controls[new_c])

            display_strings = [c[2] for c in display_controls]

            match last_get_control:
                case "studman:students-all":
                    display_strings.append("Get a student")
                case "studman:courses-all":
                    display_strings.append("Get a course")
                case "studman:assessments-all" | "studman:student-assessments" | "studman:course-assessments":
                    display_strings.append("Get an assessment")

            display_strings.append("Generate student's ID card")

            display_strings.append("Exit client")

            # 2. display list of controls to the user, and make them pick
            option = option_picker(f"Current node: {current_href}\n"
                                   f"Please, choose one of the following actions:",
                                   display_strings)

            picked_control = ()

            if display_strings[option] == "Exit client":
                print("Exiting the client.")
                sys.exit(0)
            elif display_strings[option] == "Generate student's ID card":
                student_id = input("Please input the student ID: ")

                image_resp = requests.get(f'{AUXILIARY_SERVICE_URL}/studentCard/{student_id}/',
                                          timeout=CLIENT_GET_TIMEOUT, stream=True)
                image_bytes = BytesIO(image_resp.content)
                image_bytes.seek(0)
                student_card_image = Image.open(image_bytes)

                plt.imshow(student_card_image)
                plt.show()  # Default is a blocking call
                student_card_image.save(f'{student_id}.jpeg', 'JPEG', quality=100)

                print(f"Student ID card saved as {student_id}.jpeg")
                continue

            elif display_strings[option] == "Get a student":
                found = False
                while not found:
                    id_str = input("Please input the student ID: ")
                    try:
                        student_id = int(id_str)

                        for s_dict in current_body["items"]:
                            if s_dict["student_id"] == student_id:
                                picked_control = ("studman:student",
                                                  "GET",
                                                  "Get a student",
                                                  s_dict["@controls"]["self"]["href"])
                                found = True
                                break
                        if not found:
                            print("The inserted course ID doesn't exist!\n")
                    except ValueError:
                        print("Not an integer!\n")

            elif display_strings[option] == "Get a course":
                found = False
                while not found:
                    id_str = input("Please input the course ID: ")
                    try:
                        course_id = int(id_str)

                        for c_dict in current_body["items"]:
                            if c_dict["course_id"] == course_id:
                                picked_control = ("studman:course",
                                                  "GET",
                                                  "Get a course",
                                                  c_dict["@controls"]["self"]["href"])
                                found = True
                                break
                        if not found:
                            print("The inserted course ID doesn't exist!\n")
                    except ValueError:
                        print("Not an integer!\n")

            elif display_strings[option] == "Get an assessment":

                found = False
                while not found:
                    id_str = input("Please input the course ID and student ID separated by a space: ")
                    try:
                        ids = id_str.split(' ')
                        if len(ids) != 2:
                            print("Input format not valid!\n")
                            break

                        c_id = int(ids[0])
                        s_id = int(ids[1])
                        for a_dict in current_body["items"]:
                            if a_dict["course_id"] == c_id and a_dict["student_id"] == s_id:
                                match last_get_control:
                                    case "studman:course-assessments":
                                        picked_control = ("studman:course-assessment",
                                                          "GET",
                                                          "Get a course's assessment",
                                                          a_dict["@controls"]["self"]["href"])
                                    case "studman:student-assessments":
                                        picked_control = ("studman:student-assessment",
                                                          "GET",
                                                          "Get a student's assessment",
                                                          a_dict["@controls"]["self"]["href"])
                                    case "studman:assessments-all":
                                        picked_control = ("studman:assessment",
                                                          "GET",
                                                          "Get an assessment",
                                                          a_dict["@controls"]["self"]["href"])
                                found = True
                                break
                        if not found:
                            print("The inserted pair of course ID and student ID doesn't exist!\n")
                    except ValueError:
                        print("Not an integer!\n")
            else:
                picked_control = display_controls[option]

            # 3. execute chosen control and handle result

            match picked_control[1]:

                case "GET":
                    current_href = picked_control[3]
                    get_body = do_get(session, API_URL + current_href)

                    if picked_control[0] == "collection":
                        if last_get_control == "studman:course":
                            last_get_control = "studman:courses-all"
                        elif last_get_control == "studman:student":
                            last_get_control = "studman:students-all"
                        elif last_get_control == "studman:assessment":
                            last_get_control = "studman:assessments-all"
                        elif last_get_control == "studman:course-assessment":
                            last_get_control = "studman:course-assessments"
                        elif last_get_control == "studman:student-assessment":
                            last_get_control = "studman:student-assessments"
                        else:
                            last_get_control = ""

                    if get_body != {}:
                        current_body = get_body
                        current_controls = current_body["@controls"]
                        if picked_control[0] != "collection":
                            last_get_control = picked_control[0]
                            current_href = picked_control[3]

                case "POST":
                    req_body = prompt_from_schema(session, current_controls[picked_control[0]])
                    resp_body = submit_data(session, current_controls[picked_control[0]], req_body)

                    if resp_body.status_code == 201:
                        decision = option_picker(f"Added new resource at URL {resp_body.headers['Location']}. "
                                                 f"Do you want to follow the link?",
                                                 ["yes", "no"])
                        if decision == 0:
                            current_href = resp_body.headers['Location']
                            get_body = do_get(session, API_URL + current_href)
                            current_body = get_body
                            current_controls = current_body["@controls"]
                            last_get_control = get_body["@controls"]["self"]
                    else:
                        raise APIError(resp_body.status_code, resp_body.content, current_href)

                case "PUT":
                    req_body = prompt_from_schema(session, current_controls[picked_control[0]])
                    resp_body = submit_data(session, current_controls[picked_control[0]], req_body)

                    if resp_body.status_code == 204:
                        print(f"Resource at URL {picked_control[3]} successfully updated")
                    else:
                        raise APIError(resp_body.status_code, resp_body.content, current_href)

                case "DELETE":
                    resp_body = session.delete(API_URL + picked_control[3])

                    if resp_body.status_code == 204:
                        print(f"Resource at URL {picked_control[3]} successfully deleted")
                    else:
                        raise APIError(resp_body.status_code, resp_body.content, current_href)
        except APIError as exc:
            print(exc)
        finally:
            print('')


if __name__ == "__main__":

    with requests.Session() as s:
        s.headers.update({"Accept": "application/vnd.mason+json, */*"})
        resp = s.get(API_URL + "/api/")
        if resp.status_code != 200:
            print("Unable to access API.")
        else:
            body = resp.json()
            application_loop(s, body)
