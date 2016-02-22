#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4

import os
import logging
import sys
import json
import socket
from threading import Thread, Event
from time import sleep
from datetime import datetime
from datetime import timedelta

from transmissionrpc import HTTPHandlerError, TransmissionError
from transmissionrpc import Client as TClient


from ttd import db
from ttd import logger
from ttdmodel import Client, Torrent, TorrentRequest
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

TRANSMISSION_CLIENT = "transmission"
DELUGE_CLIENT       = "deluge"

CLIENT_TYPE = [
        TRANSMISSION_CLIENT,
        DELUGE_CLIENT]

class BTCexception(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BitTorrentClient(object):
    def __init__(self,client_type = TRANSMISSION_CLIENT):
        self.client_type= client_type
    def connect(self, address, port, user, password):
        pass
    def get_torrents(self):
        pass
    def add_torrent(self, torrent_path):
        pass
    def remove(self, torrent_name):
        pass

class TransmissionClient(BitTorrentClient):
    def __init__(self):
        BitTorrentClient.__init__(self, TRANSMISSION_CLIENT)
        self.dict_client={}

    def connect(self, address, port, user, password):
        try :
           self.client =TClient( address, port, user, password)
        except TransmissionError as err:
            raise BTCexception("TransmissionError {}".format(err))

        self.dict_client['name']= address

    def get_torrents(self):
        tr_torrents = self.client.get_torrents()
        self.dict_client['torrents']= []
        for _torrent in tr_torrents:
            _torrent_dict = {
            u'name'         : _torrent.name,
            u'hash'         : _torrent.hashString,
            u'progress'     : _torrent.progress,
            u'status'       : _torrent.status,
            u'date_active'  : _torrent.date_active,
            u'date_added'   : _torrent.date_added,
            u'date_started' : _torrent.date_started,
            u'date_done'    : _torrent.date_done,
            u'eta'          : -1,

            }
            #TODO: Warning eta can return exception ValuerError

            try:
               _torrent_dict[ u'eta']          = timedelta.total_seconds(_torrent.eta)
            except ValueError:
                pass
            self.dict_client['torrents'].append(_torrent_dict)
        return self.dict_client
    def add_torrent(self, torrent_path):
        pass
    def remove(self, torrent_hash):
        self.client.remove_torrent(torrent_hash)

    def verify(self, torrent_hash):
        self.client.verify_torrent(torrent_hash)

class TorrentClient(Thread):
    def __init__(self, ipt):
        Thread.__init__(self)
        self._stop = Event()
        self.daemon = True
        self.name = ipt
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        local_session = Session()
        self.client = local_session.query(Client).filter(Client.ipt == ipt).first()
        Session.remove()
        self.btc = TransmissionClient()
        try :
            self.btc.connect( address  = self.client.ipt,
                 port = 9091,
                 user = self.client.login,
                 password = self.client.password )
        except BTCexception:
            err = "failed to start {}".format(self.client.ipt)
            raise BTCexception(err)
    def run(self):
        while True:
            if self._stop.isSet():
                break
            try:
                torrents= self.btc.get_torrents()
            except HTTPHandlerError as err:
                logger.error(u'{} {}'.format(self.name, err))
                self.stop()
            except TransmissionError as err:
                logger.error(u'{} {}'.format(self.name, err))
                self.stop()
            except socket.timeout as err:
                logger.error(u'{} socket {}'.format(self.name, err))
                self.stop()
            else :
                self.update_torrent_table(torrents)
                self.search_deleted_torrents(torrents)
                self.torrent_requests()
            sleep(10)

    def torrent_requests(self):
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        local_session = Session()
        new_requests = local_session.query(TorrentRequest).\
                filter_by(request_token = True).all()
        for request in new_requests:
            logger.info("New request {}".format(request))
            if request.request_type == u'REMOVE':
                self.btc.remove(request.request_hash)
                request.request_token = False
                logger.info(u"Torrent {} deleted in {}".\
                        format(request.request_name, request.ipt)
                        )
            if request.request_type == u'VERIFY':
                self.btc.verify(request.request_hash)
                request.request_token = False
                logger.info(u"Torrent {} verification started in {}".\
                        format(request.request_name, request.ipt)
                        )


        Session.commit()
        Session.remove()

    def search_hash_in_db(self,torrent_hash, resq):
        for r in resq:
            if torrent_hash == r.hash:
                return r
        return None

    def search_hash_in_torrent_client(self,torrent_hash, torrents):
        for t in torrents['torrents']:
            if torrent_hash == t['hash']:
                return t
        return None


    def search_deleted_torrents(self,torrents):
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        local_session = Session()

        _client= local_session.query(Client).filter(Client.ipt == self.name).first()
        resq = local_session.query(Torrent).\
                filter(Torrent.client == _client, Torrent.state != u'deleted').all()

        for _r in resq:
            if self.search_hash_in_torrent_client(_r.hash, torrents) is None:
                # torrent deleted in client
                _r.state = u'deleted'
                local_session.commit()

        Session.remove()



    def update_torrent_fields(self):
        if self.resq.state != self._t[u'status']:
            self.resq.state = self._t[u'status']
        if self.resq.percent_done != self._t[u'progress']:
            self.resq.percent_done = self._t[u'progress']
        if self.resq.date_active != self._t[u'date_active']:
            self.resq.date_active = self._t[u'date_active']
        if self.resq.date_added != self._t[u'date_added']:
            self.resq.date_added = self._t[u'date_added']
        if self.resq.date_started != self._t[u'date_started']:
            self.resq.date_started = self._t[u'date_started']
        if self.resq.date_done != self._t[u'date_done']:
            self.resq.date_done = self._t[u'date_done']
        if self.resq.eta != self._t[u'eta']:
            self.resq.eta = self._t[u'eta']


    def update_torrent_table(self, torrents):

        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        local_session = Session()
        for _t in torrents['torrents']:
            _client= local_session.query(Client).filter(Client.ipt == self.name).first()
            self.resq = local_session.query(Torrent).\
                    filter(Torrent.client == _client, Torrent.hash == _t['hash']).first()
            if self.resq is not None:
                self._t = _t
                self.update_torrent_fields()
                local_session.commit()
            else:
                new_torrent = Torrent(
                    name         = _t[u'name'],
                    hash         = _t[u'hash'],
                    state        = _t[u'status'],
                    percent_done = _t[u'progress'],
                    date_active  = _t[u'date_active'],
                    date_added   = _t[u'date_added'],
                    date_started = _t[u'date_started'],
                    date_done    = _t[u'date_done'],
                    eta          = _t[u'eta'],
                    update       = datetime.now(),
                    client       = _client )
                local_session.add(new_torrent)
                local_session.commit()
        Session.remove()

    def stop(self):
        self._stop.set()
    def stopped(self):
        return self._stop.isSet()




def main(argv):
    pass
