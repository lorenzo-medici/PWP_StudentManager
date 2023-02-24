# SOURCE: Project Layout on Lovelace

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
    from . import models

    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.generate_test_data)
    app.cli.add_command(models.run_tests)

    # API and BLUEPRINT
    # import not at the top of the file to avoid circular imports

    from . import api
    app.register_blueprint(api.api_bp)

    return app
