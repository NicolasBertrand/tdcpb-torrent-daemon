#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
import socket
from time import sleep
from datetime import datetime, timedelta

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from ttd import db
from ttd import logger
from ttdmodel import MonitoringRequest, MonitoringStatus, TorrentRequest, Client
from ttd.BitTorrentClient import TorrentClient, BTCexception

MAX_FAIL = 6
TRY_RESTART_DELAY= 5*60
MAIN_LOOP_SLEEP = 10

def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print ex.message
    return False

class ThreadManager(object):

    def __init__(self):
        self.thread_dict = {}
        self.retry_date = {}
        self.db = db
        self.db.Session.bind = db.engine

    def prepare_action(self, ipt, request_type, mstatus):
        if request_type == MonitoringRequest.MRT_START:
            if ipt in self.thread_dict:
                logger.warning(u'hum, thread not supposed to be already started')
                return "ERROR"
            try :
                thr = TorrentClient(ipt)
            except BTCexception as err:
                logger.warning('Failed start for {}: {}'.format(ipt,err))
                if mstatus.status != MonitoringStatus.MST_FAIL:
                    mstatus.status = MonitoringStatus.MST_FAIL
                if not mstatus.fail_count:
                    mstatus.fail_count = 0
                if mstatus.fail_count < MAX_FAIL:
                    mstatus.fail_count +=1
                    mstatus.fail_date = datetime.now()
                return "ERROR"
            else:
                mstatus.status = MonitoringStatus.MST_START
                mstatus.fail_count = 0
                mstatus.start_date = datetime.now()
                thr.start()
                sleep(.5)
                logger.info("Thread started for {}".format(ipt))
                self.thread_dict[ipt] = thr

        if request_type == MonitoringRequest.MRT_STOP:
            if ipt in self.thread_dict:
                logger.info("STOP thread for {}".format(ipt))
                self.thread_dict[ipt].stop()
                self.thread_dict[ipt].join()
                del self.thread_dict[ipt]
                mstatus.status = MonitoringStatus.MST_STOP
                mstatus.fail_count = 0
        return "OK"

    def is_thread_stopped(self, local_session):
        ipt_to_del=[]
        for ipt,thr in self.thread_dict.iteritems():
            if thr.stopped():
                logger.warning(u'{} thread stopped'.format(ipt))
                thr.join()
                ipt_to_del.append(ipt)
                mstatus = local_session.query(MonitoringStatus).\
                        filter_by(ipt = ipt).first()
                if mstatus.status != MonitoringStatus.MST_FAIL:
                    mstatus.status = MonitoringStatus.MST_FAIL
                if not mstatus.fail_count:
                    mstatus.fail_count = 0
                if mstatus.fail_count < MAX_FAIL:
                    mstatus.fail_count +=1
                    mstatus.fail_date = datetime.now()
        for ipt in ipt_to_del:
            del self.thread_dict[ipt]

    def torrent_requests(self, local_session):
        new_requests = local_session.query(TorrentRequest).\
                filter_by(request_token = True).all()
        for request in new_requests:
            #logger.info("New request {}".format(request))
            pass

    def clear_fail_count(self, ipt=None):
        if ipt is None:
            mstatuses = self.db.Session.query(MonitoringStatus).all()
        else:
            mstatuses =  self.db.Session.query(MonitoringStatus).filter_by(ipt=ipt).all()

            if mstatuses == []:
                logger.warning(u'No status entry for {}'.format(ipt))
                return
        for mstatus in mstatuses:
            mstatus.fail_count = 0
            mstatus.fail_date = None
            mstatus.status = MonitoringStatus.MST_FAIL
        self.db.Session.commit()

    def start(self):
        logger.info("Starting thread moniroring")
        self.clear_fail_count()
        try:
            while True:
                sleep(MAIN_LOOP_SLEEP)
                delay = datetime.now()
                clients = self.db.Session.query(Client).all()
                #clients= [ self.db.Session.query(Client).filter_by(ipt='10.10.10.48').first()]
                clients_to_start = []
                for client in clients:
                    ipt = client.ipt
                    mstatus = self.db.Session.query(MonitoringStatus).\
                            filter_by(ipt = ipt).first()

                    if mstatus is None:
                        #TODO: New client detected add it start it
                        logger.info(u'{} new client'.format(ipt))
                        new_status = MonitoringStatus(ipt=ipt, status = MonitoringStatus.MST_FAIL)
                        self.db.Session.add(new_status)
                    else:
                        if mstatus.status == MonitoringStatus.MST_FAIL:
                            #TODO: client is in failed state: try_restart
                            if mstatus.fail_count >= MAX_FAIL :
                                logger.error("{}: trying start stopped too much fails".format(ipt))
                                mstatus.status = MonitoringStatus.MST_FAIL_STOP
                            else:
                                clients_to_start.append(ipt)
                        elif mstatus.status == MonitoringStatus.MST_FAIL_STOP:
                            if ipt in self.retry_date:
                                if datetime.now() > self.retry_date[ipt]:
                                    # try a new restart
                                    logger.warning("{}: Tryning a restart in case of client is back".format(ipt))
                                    self.clear_fail_count(ipt)
                                    self.retry_date.pop(ipt)
                            else:
                                # set retry date
                                self.retry_date[ipt] = datetime.now() + timedelta(seconds = TRY_RESTART_DELAY)
                        elif mstatus.status == MonitoringStatus.MST_START:
                            # nothing to do already started
                            if not ipt in self.thread_dict:
                                clients_to_start.append(ipt)
                            else:
                                logger.debug(u'{} alredy started'.format(ipt))
                        else:
                            # TODO: un expected state or STOP
                            pass
                self.db.Session.commit()

                for ipt in clients_to_start:

                    mstatus = self.db.Session.query(MonitoringStatus).\
                            filter_by(ipt = ipt).first()
                    self.prepare_action(ipt, MonitoringRequest.MRT_START, mstatus)
                    self.db.Session.commit()

                self.torrent_requests(self.db.Session)
                self.db.Session.commit()

                delay = datetime.now() - delay
                logger.info('Duration main loop = {}'.format(delay))
        except KeyboardInterrupt:
            for _t in self.thread_dict.itervalues():
                _t.stop()
            for _t in self.thread_dict.itervalues():
                _t.join()
