#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
from time import sleep

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from ttd import db
from ttd import logger
from ttdmodel import MonitoringRequest, MonitoringStatus
from ttd.BitTorrentClient import TorrentClient, BTCexception

class ThreadManager(object):

    def __init__(self):
        self.thread_dict = {}
        session_factory = sessionmaker(bind=db.engine)
        self.Session = scoped_session(session_factory)

    def prepare_action(self, ipt, request_type, mstatus):
        if request_type == MonitoringRequest.MRT_START:
            if ipt in self.thread_dict:
                logger.warning(u'hum, thread not supposed to be already started')
                return "ERROR"
            try :
                thr = TorrentClient(ipt)
            except BTCexception as err:
                logger.warning('Failed start for {}: {}'.format(ipt,err))
                mstatus.status = MonitoringStatus.MST_FAIL
                return "ERROR"
            else:
                mstatus.status = MonitoringStatus.MST_START
                thr.start()
                logger.info("Thread started for {}".format(ipt))
                self.thread_dict[ipt] = thr

        if request_type == MonitoringRequest.MRT_STOP:
            if ipt in self.thread_dict:
                logger.info("STOP thread for {}".format(ipt))
                self.thread_dict[ipt].stop()
                self.thread_dict[ipt].join()
                del self.thread_dict[ipt]
                mstatus.status = MonitoringStatus.STOP
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
                mstatus.status = MonitoringStatus.MST_FAIL
        for ipt in ipt_to_del:
            del self.thread_dict[ipt]


    def start(self):
        logger.info("Starting thread moniroring")
        try:
            while True:
                local_session = self.Session()
                new_requests = local_session.query(MonitoringRequest).\
                        filter_by(request_token = True).all()
                actions = []
                for request in new_requests:
                    actions.append((request.ipt, request.request_type))
                    request.request_token = False
                    local_session.commit()
                for ipt, request_type in actions:
                    mstatus = local_session.query(MonitoringStatus).\
                            filter_by(ipt = ipt).first()
                    if mstatus is not None:
                        _ret = self.prepare_action(ipt, request_type, mstatus)
                        if _ret == "ERROR":
                            continue
                    else:
                        new_status = MonitoringStatus(
                                ipt= ipt)
                        self.prepare_action(ipt, request_type, new_status)
                        local_session.add(new_status)
                self.is_thread_stopped(local_session)
                local_session.commit()
                self.Session.remove()
                sleep(2)
        except KeyboardInterrupt:
            for _t in self.thread_dict.itervalues():
                _t.stop()
            for _t in self.thread_dict.itervalues():
                _t.join()
