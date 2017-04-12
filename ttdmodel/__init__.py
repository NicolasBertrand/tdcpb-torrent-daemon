# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base



from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy import Boolean, BigInteger
from sqlalchemy.orm import relationship


class TtdModel(object):

    def __init__(self, database_uri = None):
        self.Model = declarative_base()

    def init_app(self, app):
        if isinstance(app, basestring):
            self.engine = create_engine(app)
        else:
            self.engine = create_engine(app.config['TTD_DATABASE_URL'])
        self.Model.metadata.bind = self.engine
        DBSession = sessionmaker()
        DBSession.bind = self.engine
        self.Session = DBSession()

db = TtdModel()

class Client(db.Model):
    __tablename__ = u'client'
    id             = Column(Integer, primary_key=True)
    ipt            = Column(String(16), nullable=False)
    login          = Column(String(64), nullable=False)
    password       = Column(String(64), nullable=False)
    client_type    = Column(String(64), nullable=False)
    free_space     = Column(BigInteger)

    def __repr__(self):
        return u'{}'.format(self.ipt)


class Torrent(db.Model):
    __tablename__ = u'torrent'
    id             = Column(Integer, primary_key=True)
    name           = Column(String(250) )
    hash           = Column(String(40))
    state          = Column(String(40))
    percent_done   = Column(Float)
    update         = Column(DateTime, nullable=False)
    date_active    = Column(DateTime)
    date_added     = Column(DateTime)
    date_started   = Column(DateTime)
    date_done      = Column(DateTime)
    eta            = Column(BigInteger)
    error          = Column(Integer)
    errorString    = Column(String(250))
    client_id      = Column(Integer, ForeignKey(u'client.id'))
    client         = relationship(Client)

    def __repr__(self):
        return u'{:<16} {:<30} {:<10} {:<10} {}'.format(\
                self.client.ipt,
                self.name[:30],
                self.state,
                self.percent_done,
                self.update)

class MonitoringRequest(db.Model):
    __tablename__ = u'monitoringrequest'
    MRT_START = u'START'
    MRT_STOP  = u'STOP'

    id             = Column(Integer, primary_key=True)
    ipt            = Column(String(16), nullable=False, unique = True)
    # Requet type:
    #    START
    #    STOP
    request_type    = Column(String(64), nullable=False)
    request_date    = Column(DateTime, nullable=False)
    request_token   = Column(Boolean)

    def __repr__(self):
        return u'{} {:<16} {} ({})'.format(\
                self.request_date,
                self.ipt,
                self.request_type,
                self.request_token)

    @classmethod
    def start_client(cls, ipt):
        qres = db.Session.query(cls).\
                filter_by( ipt = ipt).first()
        if qres is not None:
            qres.request_type = cls.MRT_START
            qres.request_date = datetime.now()
            qres.request_token = True
        else:
            new_mr = cls(
                    ipt=ipt,
                    request_type = cls.MRT_START,
                    request_date = datetime.now(),
                    request_token = True )
            db.Session.add(new_mr)
        db.Session.commit()


    @classmethod
    def stop_client(cls, ipt):
        qres = db.Session.query(cls).\
                filter_by( ipt = ipt).first()
        if qres is not None:
            qres.request_type = cls.MRT_STOP
            qres.request_date = datetime.now()
            qres.request_token = True
        else:
            new_mr = cls(
                    ipt          = ipt,
                    request_type = cls.MRT_STOP,
                    request_date = datetime.now(),
                    request_token = True )
            db.Session.add(new_mr)
        db.Session.commit()




class MonitoringStatus(db.Model):
    MST_START = u'STARTED'
    MST_STOP  = u'STOPPPED'
    MST_FAIL  = u'FAILED'

    __tablename__ = u'monitoringstatus'
    id            = Column(Integer, primary_key=True)
    ipt           = Column(String(16), nullable=False,)
    status        = Column(String(64), nullable=False, default=u'STOP')

    def __repr__(self):
        return u'{:<16} {}'.format(\
                self.ipt,
                self.status)

class TorrentRequest(db.Model):
    __tablename__ = u'torrentrequest'

    id             = Column(Integer, primary_key=True)
    ipt            = Column(String(16), nullable=False)
    request_type   = Column(String(64), nullable=False)
    request_hash   = Column(String(40))
    request_name   = Column(String(250))
    request_date   = Column(DateTime, nullable=False)
    request_token  = Column(Boolean)

    def __repr__(self):
        return u'{} {:<16} {} ({})'.format(\
                self.request_date,
                self.ipt,
                self.request_type,
                self.request_token)

    @classmethod
    def delete_torrent_by_hash(cls, p_ipt, p_hash):
        qres = db.Session.query(Torrent,Client).filter(Torrent.hash==p_hash, Client.ipt==p_ipt).first()
        if qres is None:
            print "No torrent found"
            return
        print "Torrent {} found in {}".format(qres.Torrent.name, qres.Client)
        new_tr= cls(
                ipt           = p_ipt,
                request_hash  = p_hash,
                request_type  = u'REMOVE',
                request_name  = qres.Torrent.name,
                request_date  = datetime.now(),
                request_token = True )
        db.Session.add(new_tr)
        db.Session.commit()

    @classmethod
    def delete_torrent_by_name(cls, p_ipt, p_name):
        qres = db.Session.query(Torrent,Client).\
            filter(Torrent.name==p_name, Client.ipt==p_ipt).first()
        if qres is None:
            print "No torrent found"
            return
        print "Torrent {} found in {}".format(qres.Torrent.name, qres.Client)
        new_tr= cls(
                ipt           = p_ipt,
                request_hash  = qres.Torrent.hash,
                request_name  = p_name,
                request_type  = u'REMOVE',
                request_date  = datetime.now(),
                request_token = True )
        db.Session.add(new_tr)
        db.Session.commit()

    @classmethod
    def verify_torrent_by_hash(cls, p_ipt, p_hash):
        qres = db.Session.query(Torrent,Client).\
                filter(Torrent.hash==p_hash, Client.ipt==p_ipt).first()
        if qres is None:
            print "No torrent found"
            return
        print "Torrent {} found in {}".format(qres.Torrent.name, qres.Client)
        new_tr= cls(
                ipt           = p_ipt,
                request_hash  = p_hash,
                request_type  = u'VERIFY',
                request_name  = qres.Torrent.name,
                request_date  = datetime.now(),
                request_token = True )
        db.Session.add(new_tr)
        db.Session.commit()
