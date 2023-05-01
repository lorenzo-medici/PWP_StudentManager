"""
Client script for the StudentManager API
"""
import sys

import requests

from api_error import APIError
from client_constants import API_URL, API_KEY
from client_utils import \
    process_controls, option_picker, prompt_from_schema, submit_data, do_get, \
    handle_student_id_option, handle_course_id_option, handle_assessment_option, \
    generate_student_id_card, last_get_control_mapper


def application_loop(session, root_body):
    """
    Main loop for the API client. Every iteration displays the option to the user, depending on
        the current resource node, makes the user pick, and executres the control
    :param session: a session object
    :param root_body: the body of the root node '/api/'
    """
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
            # - add option to insert value for student, course or assessment depending on
            #     current_href
            # - add studman:students-all, courses-all and assessments-all to current_controls,
            #     if not already present
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
                case "studman:assessments-all" | \
                     "studman:student-assessments" | \
                     "studman:course-assessments":
                    display_strings.append("Get an assessment")

            display_strings.append("Generate student's ID card")

            display_strings.append("Exit client")

            # 2. display list of controls to the user, and make them pick
            option = option_picker(f"Current node: {current_href}\n"
                                   f"Please, choose one of the following actions:",
                                   display_strings)

            if display_strings[option] == "Exit client":
                print("Exiting the client.")
                sys.exit(0)
            elif display_strings[option] == "Generate student's ID card":
                generate_student_id_card()
                continue

            elif display_strings[option] == "Get a student":
                picked_control = handle_student_id_option(current_body)

            elif display_strings[option] == "Get a course":
                picked_control = handle_course_id_option(current_body)

            elif display_strings[option] == "Get an assessment":
                picked_control = handle_assessment_option(current_body, last_get_control)

            else:
                picked_control = display_controls[option]

            # 3. execute chosen control and handle result

            match picked_control[1]:

                case "GET":

                    get_body = do_get(session, API_URL + picked_control[3])

                    if picked_control[0] == 'collection':
                        last_get_control = last_get_control_mapper(last_get_control)

                    if get_body:
                        current_body = get_body
                        current_controls = current_body.get("@controls")
                        if display_strings[option] not in ["collection", "profile"]:
                            last_get_control = picked_control[0]
                            current_href = picked_control[3]
                        elif display_strings[option] == "collection":
                            current_href = picked_control[3]

                case "POST":
                    req_body = prompt_from_schema(session, current_controls[picked_control[0]])
                    resp_body = submit_data(session, current_controls[picked_control[0]], req_body)

                    if resp_body.status_code == 201:
                        decision = option_picker(
                            f"Added new resource at URL {resp_body.headers['Location']}. "
                            f"Do you want to follow the link?",
                            ["yes", "no"]
                        )
                        if decision == 0:
                            current_href = resp_body.headers['Location']
                            current_body = do_get(session, API_URL + current_href)
                            current_controls = current_body.get("@controls")
                            last_get_control = current_body.get("@controls")["self"]
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
                    resp_body = session.delete(API_URL + picked_control[3],
                                               headers={'Studentmanager-Api-Key': API_KEY})

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
