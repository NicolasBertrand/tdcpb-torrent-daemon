#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4

import os
import logging
import sys
import json
from threading import Thread, Event
from time import sleep

from transmissionrpc import HTTPHandlerError, TransmissionError
from transmissionrpc import Client as TClient

from ttd import db
from ttd.models import Client, Torrent
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
    def del_torrent(self, torrent_name):
        pass

class TransmissionClient(BitTorrentClient):
    def __init__(self):
        BitTorrentClient.__init__(self, TRANSMISSION_CLIENT)
        self.dict_client={}

    def connect(self, address, port, user, password):
        try :
           self.client =TClient( address, port, user, password)
        except TransmissionError as err:
            raise BTCException("TransmissionError {}".format(err))

        self.dict_client['name']= address

    def get_torrents(self):
        tr_torrents = self.client.get_torrents()
        self.dict_client['torrents']= []
        for _torrent in tr_torrents:
            _torrent = {
            u'dcpname'    : _torrent.name,
            u'hash'    : _torrent.hashString,
            u'progress': _torrent.progress,
            u'status'  : _torrent.status
            }
            self.dict_client['torrents'].append(_torrent)
        return self.dict_client
    def add_torrent(self, torrent_path):
        pass
    def del_torrent(self, torrent_name):
        pass

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
        self.btc.connect( address  = self.client.ipt,
                 port = 9091,
                 user = self.client.login,
                 password = self.client.password )

    def run(self):
        while True:
            if self._stop.isSet():
                break
            torrents= self.btc.get_torrents()
            self.update_torrent_table(torrents)
            self.search_deleted_torrents(torrents)
            sleep(5)

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

    def update_torrent_table(self, torrents):
        session_factory = sessionmaker(bind=db.engine)
        Session = scoped_session(session_factory)
        local_session = Session()
        for _t in torrents['torrents']:
            _client= local_session.query(Client).filter(Client.ipt == self.name).first()
            resq = local_session.query(Torrent).\
                    filter(Torrent.client == _client).all()
            titem = self.search_hash_in_db(_t['hash'], resq)
            if titem is not None:
                if titem.percent_done != _t[u'progress']:
                    titem.percent_done = _t[u'progress']
                    print "progressionn updated {} {}  ".\
                            format(titem.percent_done, _t[u'progress'])
                if titem.state != _t[u'status']:
                    titem.state = _t[u'status']
                    print "progressionn updated {} {}  ".\
                            format(titem.state, _t[u'status'])
                local_session.commit()
            else:
                new_torrent = Torrent(
                    name         = _t[u'dcpname'],
                    hash         = _t[u'hash'],
                    state        = _t[u'status'],
                    percent_done = _t[u'progress'],
                    client       = _client )
                local_session.add(new_torrent)
                local_session.commit()
        Session.remove()

    def stop(self):
        self._stop.set()
    def stoppped(self):
        return self._stop.isSet()




def main(argv):
    pass
