
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import logging
from logging.handlers import TimedRotatingFileHandler

class SqlAchmemy(object):
    def __init__(self):
        self.engine = create_engine('mysql://tdcpb:tdcpb@localhost/tdcpbtorrentsdb')
        self.Model = declarative_base()
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
 
