# PWP SPRING 2023

# StudentManager

# Group information

* Student 1. Pranav Bahulekar \<pranav.bahulekar@student.oulu.fi\>
* Student 2. Lorenzo Medici \<lorenzo.medici@student.oulu.fi\>
* Student 3. Alessandro Nardi \<alessandro.nardi@student.oulu.fi\>
* Student 4. Dániel Szabó \<daniel.szabo@student.oulu.fi\>


# Dependencies

The dependencies for this project are:

### UPDATE SECTION
|      Module      | Version |
|:----------------:|:-------:|
|      Flask       |  2.2.2  |
| flask_sqlalchemy |  3.0.3  |
|    SQLAlchemy    |  2.0.2  |
|      click       |  8.1.3  |

These dependencies can be found in the file `requirements.txt` in the root directory of the project.

These dependencies can be installed by executing `pip install -r requirements.txt` from the project's root directory.
Alternatively, they can be installed by
executing `pip install Flask==2.2.2 flask_sqlalchemy==3.0.3 SQLAlchemy==2.0.2 click==8.1.3`.


The database engine used is SQLite, version 3.40.1.

# Database Inizialization and population

The database can be initialized by executing `flask --app studentmanager init-db`.
After that, it can be populated with test data by executing `flask --app studentmanager testgen`.
The code for these functions is contained in the `model.py` file.

The populated `db` file can be found in the `instance/` subfolder.

# Running the application

After the database has been initialized (check if it is necessary???), the application can be started by executing `flask --app studentmanager run`.
This will start a running server on the local machine, which will then be available by typing `http://127.0.0.1:5000/` in the browser's address bar.

The root of the API will be available at `http://localhost:5000/api/` [TO EDIT, it should probably be /studentmanager/api/v1/]

# Testing

### ADD TEST DEPENDENCY TABLE
In the `tests/` subfolder, some files containing functional tests can be found, these will test the model classes and database, and the API.
To run the tests it is sufficient to execute `flask --app studentmanager testrun` from the project's root folder.