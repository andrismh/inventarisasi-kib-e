from flask import Flask
from config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401  (register models with SQLAlchemy)

    from .blueprints.main import bp as main_bp
    from .blueprints.entry import bp as entry_bp
    from .blueprints.master_table import bp as master_bp
    from .api.inventory import bp as api_inventory_bp
    from .api.search import bp as api_search_bp
    from .api.masters import bp as api_masters_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(entry_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(api_inventory_bp)
    app.register_blueprint(api_search_bp)
    app.register_blueprint(api_masters_bp)

    from .services.excel_import import register_cli
    register_cli(app)

    return app
