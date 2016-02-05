
import logging
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app import ttd
from config import config as ttdconfig
from ttdmodel import TtdModel


db=TtdModel()

logger = logging.getLogger('ttd')
file_handler = TimedRotatingFileHandler('/var/log/tuco/ttd.log', when='D')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[TTD] %(asctime)s %(levelname)s %(message)s (%(filename)s %(funcName)s l %(lineno)d)')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.setLevel(logging.INFO)
logger.info("Starting")


def create_app(basedir):
    app = ttd(basedir)
    app.config.from_object(ttdconfig['default'])
    db.init_app(app)

    return app
