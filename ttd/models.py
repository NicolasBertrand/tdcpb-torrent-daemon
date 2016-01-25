# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy import Boolean
from sqlalchemy.orm import relationship
from ttd import db

class Client(db.Model):
    __tablename__ = u'client'
    id             = Column(Integer, primary_key=True)
    ipt            = Column(String(16), nullable=False)
    login          = Column(String(64), nullable=False)
    password       = Column(String(64), nullable=False)
    client_type    = Column(String(64), nullable=False)

class Torrent(db.Model):
    __tablename__ = u'torrent'
    id             = Column(Integer, primary_key=True)
    name           = Column(String(250) )
    hash           = Column(String(40))
    state          = Column(String(40))
    percent_done   = Column(Float)
    update         = Column(DateTime, nullable=False)
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

   
