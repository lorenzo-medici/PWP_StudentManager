# SOURCE: Project Layout on Lovelace

import os

from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cache = Cache()


# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "StudentManager.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

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
    from studentmanager.models import generate_test_data, run_tests, init_db_command, generate_master_key

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
    app.register_blueprint(api_bp)

    app.url_map.converters["student"] = StudentConverter
    app.register_blueprint(api_bp)

    # CACHE initialization
    app.config["CACHE_TYPE"] = "FileSystemCache"
    app.config["CACHE_DIR"] = "cache"

    cache.init_app(app)

    return app
