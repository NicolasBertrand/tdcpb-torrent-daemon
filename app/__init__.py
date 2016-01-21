
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class SqlAchmemy(object):
    def __init__(self):
        self.engine = create_engine('mysql://tdcpb:tdcpb@localhost/tdcpbtorrentsdb')
        self.Model = declarative_base()
        self.Model.metadata.bind = self.engine
        DBSession = sessionmaker()
        DBSession.bind = self.engine
        self.Session = DBSession()

db=SqlAchmemy()
