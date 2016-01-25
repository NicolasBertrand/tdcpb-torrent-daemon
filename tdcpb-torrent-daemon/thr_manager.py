#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
from time import sleep

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from app import db
from app.models import MonitoringRequest, MonitoringStatus
from app.BitTorrentClient import TorrentClient

class ThreadManager(object):

    def __init__(self):
        print "coucou"
        self.thread_dict = {}
        session_factory = sessionmaker(bind=db.engine)
        self.Session = scoped_session(session_factory)

    def prepare_action(self, ipt, request_type, mstatus):
        if request_type == MonitoringRequest.MRT_START:
            if mstatus.status != MonitoringStatus.MST_START:
                if ipt in self.thread_dict:
                    print u'hum, thread not supposed to be already started'
                    return "ERROR"
                mstatus.status = MonitoringRequest.MRT_START
                thr = TorrentClient(ipt)
                thr.start()
                print "Thread started for {}".format(ipt)
                self.thread_dict[ipt] = thr

        if request_type == MonitoringRequest.MRT_STOP:
            print "STOP thread"
            if ipt in self.thread_dict:
                print "STOP threa(really)"
                self.thread_dict[ipt].stop()
                self.thread_dict[ipt].join()
                del self.thread_dict[ipt]
                mstatus.status = MonitoringRequest.MRT_STOP
        return "OK"


    def start(self):
        try:
            while True:
                local_session = self.Session()
                new_requests = local_session.query(MonitoringRequest).\
                        filter_by(request_token = True).all()
                actions = []
                for request in new_requests:
                    print request.ipt, request.request_token
                    actions.append((request.ipt, request.request_type))
                    request.request_token = False
                    print request.request_token
                    local_session.commit()
                for ipt, request_type in actions:
                    print ipt, request_type
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
                local_session.commit()
                self.Session.remove()
                sleep(2)
        except KeyboardInterrupt:
            for _t in self.thread_dict.itervalues():
                _t.stop()
            for _t in self.thread_dict.itervalues():
                _t.join()
