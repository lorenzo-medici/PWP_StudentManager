# PWP SPRING 2023

# StudentManager

# Group information

* Student 1. Pranav Bahulekar \<pranav.bahulekar@student.oulu.fi\>
* Student 2. Lorenzo Medici \<lorenzo.medici@student.oulu.fi\>
* Student 3. Alessandro Nardi \<alessandro.nardi@student.oulu.fi\>
* Student 4. Dániel Szabó \<daniel.szabo@student.oulu.fi\>


# Dependencies

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

These dependencies can be found in the file `requirements.txt` in the root directory of the project.

These dependencies can be installed by executing `pip install -r requirements.txt` from the project's root directory.
Alternatively, they can be installed by
executing `pip install <module>==<version>` for each module or adding all modules to the same command separated by spaces.


The database engine used is SQLite, version 3.40.1.

# Database Inizialization and population

The database can be initialized by executing `flask --app studentmanager init-db`.
After that, it can be populated with test data by executing `flask --app studentmanager testgen`.
The code for these functions is contained in the `model.py` file.

The populated `db` file can be found in the `instance/` subfolder. 
[IMPORTANT: EXCLUDE FROM .GITIGNORE, POPULATE DB, GENERATE ADMIN KEY BEFORE DELIVERING]

# Running the application

After the database has been initialized, the application can be started by executing `flask --app studentmanager run`.
This will start a running server on the local machine, which will then be available by typing `http://127.0.0.1:5000/` in the browser's address bar.

The root of the API will be available at `http://localhost:5000/api/` [TO EDIT, it should probably be /studentmanager/api/v1/]

# Testing

The dependencies for running the tests are:

|      Module      | Version |
|:----------------:|:-------:|
|      pytest      |  7.2.1  |

If `pip install -r requirements.txt` was executed, pytest is already installed. Otherwise, `pip install pytest==7.2.1` will need to be executed.

In the `tests/` subfolder, some files containing functional tests can be found, these will test the model classes and database, and the API.
To run the tests it is sufficient to execute `flask --app studentmanager testrun` from the project's root folder.

## Results

Implementing and running tests helped make the whole picture clear regarding all the implemented components and how they interact with each other.
Some doubts and wrong implementations were corrected in regard to JSON schemas and validation, for example the correct definition of `date-time` fields and their validation.

Tests were also important to make sure that the correct error code was returned for every possible error in the request, they also helped make the whole API coherent in this aspect.