"""
This module is used to retrieve a working Flask application complete with all the needed components
"""
# SOURCE: Project Layout on Lovelace

import os

from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

db = SQLAlchemy()
cache = Cache()


# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    """
    This function instantiates a Flask app and initializes all necessary components
        (Cache, SQLAlchemy database, API), adds the click functions and assigns
        the URL converters.
    :param test_config: A dictionary containing the app configuration parameters to use for Tests
    :return: a Flask app object
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" +
                                os.path.join(app.instance_path,
                                             "StudentManager.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    app.config["SWAGGER"] = {
        "title": "PWP Student Manager API",
        "openapi": "3.0.3",
        "uiversion": 3,
        "doc_dir": "./doc",
    }

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    # MODELS and CLICK functions
    # import not at the top of the file to avoid circular imports
    from studentmanager.models import \
        generate_test_data, run_tests, init_db_command, generate_master_key

    app.cli.add_command(init_db_command)
    app.cli.add_command(generate_test_data)
    app.cli.add_command(run_tests)
    app.cli.add_command(generate_master_key)

    # API and BLUEPRINT
    # import not at the top of the file to avoid circular imports

    from studentmanager.api import api_bp
    from studentmanager.resources.course import CourseConverter
    from studentmanager.resources.student import StudentConverter

    app.url_map.converters["course"] = CourseConverter
    app.url_map.converters["student"] = StudentConverter

    app.register_blueprint(api_bp)

    # CACHE initialization
    app.config["CACHE_TYPE"] = "FileSystemCache"
    if test_config is None or "CACHE_DIR" not in test_config:
        app.config["CACHE_DIR"] = os.path.join(app.instance_path, "cache")
    else:
        app.config["CACHE_DIR"] = test_config["CACHE_DIR"]

    cache.init_app(app)

    Swagger(app, template_file="doc/doc.yml")

    return app
