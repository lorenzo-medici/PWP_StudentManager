# PWP SPRING 2023
# StudentManager
# Group information
* Student 1. Pranav Bahulekar \<pranav.bahulekar@student.oulu.fi\>
* Student 2. Lorenzo Medici \<lorenzo.medici@student.oulu.fi\>
* Student 3. Alessandro Nardi \<alessandro.nardi@student.oulu.fi\>
* Student 4. Dániel Szabó \<daniel.szabo@student.oulu.fi\>

# Database

## Models
The `model.py` file containing the classes can be found in the `model/` subfolder.

## Dependencies
The dependencies for this project are:

|Module|Version|
|:---:|:---:|
|Flask|2.2.2|
|flask_sqlalchemy|3.0.3|
|SQLAlchemy|2.0.2|
|click|8.1.3|

These dependencies can be found in the file `requirements.txt` in the root directory of the project.

These dependencies can be installed by executing `pip install -r requirements.txt` from the project's root directory.
Alternatively, they can be installed by executing `pip install Flask==2.2.2 flask_sqlalchemy==3.0.3 SQLAlchemy==2.0.2 click==8.1.3`.

If you want to execute the tests, you can append `pytest==7.2.1` to the last command, or to the `requirements.txt` file before executing `pip install -r requirements.txt`. Finally, `pytest` can be executed to run the tests.

The database engine used is SQLite, version 3.40.1.

## Inizialization and population

The database can be initialized by executing `flask --app app init-db`.
After that, it can be populated with test data by executing `flask --app app testgen`.
The code for these functions is contained in the `model.py` file.

A populated `db` file can be found in the `instance/` subfolder.
