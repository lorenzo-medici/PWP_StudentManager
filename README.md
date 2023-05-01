# PWP SPRING 2023

# StudentManager

# Group information

* Student 1. Pranav Bahulekar \<pranav.bahulekar@student.oulu.fi\>
* Student 2. Lorenzo Medici \<lorenzo.medici@student.oulu.fi\>
* Student 3. Alessandro Nardi \<alessandro.nardi@student.oulu.fi\>
* Student 4. Dániel Szabó \<daniel.szabo@student.oulu.fi\>

# StudentManager API Server

## Dependencies

The dependencies for this project are:

|      Module      | Version |
|:----------------:|:-------:|
|      Flask       |  2.2.2  |
| flask_sqlalchemy |  3.0.3  |
|    SQLAlchemy    |  2.0.2  |
|      click       |  8.1.3  |
|  Flask_RESTful   |  0.3.9  |
|  Flask_Caching   |  2.0.2  |
|    jsonschema    | 4.17.3  |
|     Werkzeug     |  2.2.2  |
|    setuptools    | 65.5.1  |
|     flasgger     |  0.9.5  |
|      PyYAML      |   6.0   |

These dependencies can be found in the file `studentmanager/requirements.txt` from the root directory of the project.

These dependencies can be installed by executing `pip install -r studentmanager/requirements.txt` from the project's
root directory.
Alternatively, they can be installed by executing `pip install <module>==<version>` for each module or adding all
modules to the same command separated by spaces.

The database engine used is SQLite, version 3.40.1.

## Database Initialisation and population

The database can be initialized by executing `flask --app studentmanager init-db`.
After that, it can be populated with test data by executing `flask --app studentmanager testgen`.
Finally, the master key can be generated with `flask --app studentmanager masterkey`. Save the printed keys in some way,
since they will be crucial for using clients. The admin key can add, modify or delete any resource, the assessment key
is limited to assessment resources.

The code for these functions is contained in the `model.py` file.
The populated `db` file can be found in the `studentamanager/instance/` subfolder.

## Running the application

After the database has been initialized, the application can be started by executing `flask --app studentmanager run`.
This will start a running server on the local machine, which will then be available by typing `http://127.0.0.1:5000/`
in the browser's address bar.

The root of the API will be available at `http://localhost:5000/api/`.
The API documentation, generated with the flasgger module, will be available at the `/apidocs/` endpoint.
Profiles for the relevant resources will be available at `/profiles/student/`, `/profiles/course/`
and `/profiles/assessment/`.
The documentation about Hypermedia links will be available at `/studentmanager/link-relations/`.

## Testing

The dependencies for running the tests are:

|   Module   | Version |
|:----------:|:-------:|
|   pytest   |  7.2.1  |
| pytest-cov |  4.0.0  |
|   Flask    |  2.2.2  |
| jsonschema | 4.17.3  |
| SQLAlchemy |  2.0.2  |
|  Werkzeug  |  2.2.2  |

If `pip install -r tests/requirements.txt` was executed, only `pytest`  and `pytest-cov` will need to be
installed.

In the `tests/` subfolder, files containing functional tests can be found, these will test the model classes and
database, and the API.
To run the tests it is sufficient to execute `flask --app studentmanager testrun` from the project's root folder.

### Test results

Running `pytest --cov=studentmanager --cov-report term-missing` returns the following table:

|                     Name                     | Stmts | Miss | Cover |               Missing               |
|:--------------------------------------------:|:-----:|:----:|:-----:|:-----------------------------------:|
|          studentmanager/__init__.py          |  57   |  1   |  98%  |                 48                  |
|            studentmanager/api.py             |  18   |  0   | 100%  |                                     |
|          studentmanager/builder.py           |  50   |  0   | 100%  |                                     |
|         studentmanager/constants.py          |  10   |  0   | 100%  |                                     |
|           studentmanager/models.py           |  185  |  39  |  79%  | 446, 456-555, 565, 576-593, 601-603 |
|     studentmanager/resources/__init__.py     |   0   |  0   | 100%  |                                     |
|    studentmanager/resources/assessment.py    |  170  |  0   | 100%  |                                     |
|      studentmanager/resources/course.py      |  103  |  0   | 100%  |                                     |
| studentmanager/resources/profile_pictures.py |  22   |  0   | 100%  |                                     |
|     studentmanager/resources/student.py      |  103  |  0   | 100%  |                                     |
|           studentmanager/utils.py            |  23   |  0   | 100%  |                                     |
|                    TOTAL                     |  741  |  40  |  95%  |                                     |

The non-tested lines are:

- `__init__.py`: the line that initializes an app when no test_config is provided, only hit on a normal launch of the
  server
- `models.py`: the click functions responsible for initializing and populating the database, executing the tests and
  generating the admin key

Implementing and running tests helped make the whole picture clear regarding all the implemented components and how they
interact with each other.
Some doubts and wrong implementations were corrected in regard to JSON schemas and validation, for example the correct
definition of `date` fields and their validation.

Tests were also important to make sure that the correct error code was returned for every possible error in the request,
they also helped make the whole API coherent in this aspect.

## Code quality

To check for compliance with python's idiomatic rules, `pylint studentmanager` was executed,
ignoring `no-member, import-outside-toplevel, no-self-use`.

The resulting score is 9.63/10.00.

The remaining warnings are:

- `studentmanager/__init__.py`
    - Various imports outside toplevel, related to all the modules imported inside the `create_app` function. These
      cannot be solved, since their aim is to avoid circular imports.
- `studentmanager/utils.py`
    - arguments `*args` and `*kwargs` unused in function `request_path_cache_key`. This function only
      returns `request.path` so any argument is ignored.
- `studentmanager/models.py`
    - argument `key` in the validation functions (with the `@validates` decorator). The argument is not used because it
      represents the name of the field being validated. Since each function is responsible for one specific field, the
      parameter is ignored.
    - argument `connection_record` in the `set_sqlite_pragma` function. The argument represents
      a `sqlalchemy.pool._ConnectionRecord` object, that represents a single connection.
    - too few public methods for the ApiKey class. This is ignored since the only needed method for the class is the one
      that generates a digest of the API key.
- `studentmanager/resources/student.py`
    - similar lines in files `student.py`, `course.py` and `assessment.py`. These lines are related to IntegrityErrors
      for different resources, which will be handled in bery similar ways.
    - various cyclic import warnings related to the `create_app` function in `studentmanager/__init__.py`. These cannot
      be solved, but don't constitute an issue since they are inside the body of the function.

# Auxiliary Service: Student ID Card generator

The implemented auxiliary service that was implemented is responsible for generating a student's ID Card from their
profile picture and personal data store in the StudentManager API.

The auxiliary service is a single file Flask application, with a single endpoint `studentCard/<student_id>/` that
implements the GET method. When this endpoint is queried, it will navigate the StudentManager API and retrieve
information based on the student_id. If it doesn't exist, it will return error code 503, including the error code
received from the API in the message.
The Content-Type of the response is `image/jpeg`.

## Dependencies

|  Module  | Version |
|:--------:|:-------:|
|  Flask   |  2.2.2  |
|  Pillow  |  9.5.0  |
| requests | 2.28.2  |

These dependencies can be found in the file `auxiliary_service/requirements.txt` from the root directory of the project.

These dependencies can be installed by executing `pip install -r auxiliary_service/requirements.txt` from the project's
root directory.
Alternatively, they can be installed by executing `pip install <module>==<version>` for each module or adding all
modules to the same command separated by spaces.

## Auxiliary Service execution

The service is launched as `python auxiliary_service.py <localPort> <apiUrl>`. It has to be launched from
the `auxiliary_service/` subfolder.
This will instantiate a Flask application on the specified port. This parameter is necessary to avoid conflict between
the API and the auxiliary service, if launched on the same machine.
The service will contact the StudentManager API at the specified URL, and return appropriate error messages if the URL
is not valid, or the API is not responding.

## Code quality

To check for compliance with python's idiomatic rules, `pylint auxiliary_service/auxiliary_service.py` was executed,
ignoring `no-member, import-outside-toplevel, no-self-use`.

The resulting score is 10.00/10.00.

# API Client

The implemented client is a CLI application, based on a never ending applicaiton loop. This loop will prompt the user
for the operation they want to perform, and will execute it.

The client implements the functionalities that allow the user to interact with any of the API endpoints, following any
control and performing the appropriate requests.
In addition, it always exposes:

- the controls to return to the three main endpoints `/api/students/`, `/api/courses/` and `/api/assessments/`
- the option to query the auxiliary service to generate a student's ID Card
- the option to exit the client

## Dependencies

|   Module   | Version |
|:----------:|:-------:|
| matplotlib |  3.7.1  |
|   Pillow   |  9.5.0  |
|  requests  | 2.28.2  |

These dependencies can be found in the file `client/requirements.txt` from the root directory of the project.

These dependencies can be installed by executing `pip install -r client/requirements.txt` from the project's root
directory.
Alternatively, they can be installed by executing `pip install <module>==<version>` for each module or adding all
modules to the same command separated by spaces.

## Configuration and execution

Before launching the clients, some configuration is required. The parameters in the file `client/client_constants.py`
will need to be filled in.

|       Parameter       |                                                            Description                                                             |
|:---------------------:|:----------------------------------------------------------------------------------------------------------------------------------:|
|        API_URL        |                                        The URL at which the StudentManager API can be found                                        |
|        API_KEY        | The API key to use for this client, either an admin or an assessment key. Please, be aware of the limitations of an assessment key |
| AUXILIARY_SERVICE_URL |                                        The URL at which the auxiliary service can be found                                         |

Then, the client can be launched with the command `python client/client.py`

## Code quality

To check for compliance with python's idiomatic rules, `pylint client/*.py` was executed,
ignoring `no-member, import-outside-toplevel, no-self-use`.

The resulting score is 9.88/10.

The remaining warnings are:

- `client/client.py`
    - Too many local variables (17/15)
    - Too many branches (23/12)
    - too many statements (71/50)

Given the complex structure of the client, it is not simple to create cleaner code, as it would require deep
restructuring of the whole script. 
 