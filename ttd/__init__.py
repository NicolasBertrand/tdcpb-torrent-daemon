
import logging
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app import ttd
from config import config as ttdconfig


class SqlAchmemy(object):

    def __init__(self):
        self.Model = declarative_base()

    def init_app(self, app):
        self.engine = create_engine(app.config['DATABASE_URI'])
        self.Model.metadata.bind = self.engine
        DBSession = sessionmaker()
        DBSession.bind = self.engine
        self.Session = DBSession()


db=SqlAchmemy()

logger = logging.getLogger('ttd')
file_handler = TimedRotatingFileHandler('/var/log/ttd/ttd.log', when='D')
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
