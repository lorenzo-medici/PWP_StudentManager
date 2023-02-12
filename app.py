import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "StudentManager.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    from model import model

    app.cli.add_command(model.init_db)
    app.cli.add_command(model.generate_test_data)

    return app
