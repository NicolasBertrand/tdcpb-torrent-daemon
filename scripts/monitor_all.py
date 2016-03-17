import sys
import os

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0,"/var/lib/tdcpb-torrents/tdcpb-torrent-daemon")

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]


from ttdmodel import db
from ttdmodel import MonitoringRequest, MonitoringStatus, Torrent, Client
from time import sleep
from pprint import pprint

db.init_app( os.environ.get('TTD_DATABASE_URL'))



print "Clients"
res = db.Session.query(Client)
for r in res:
    print "starting {}".format(r.ipt)
    MonitoringRequest.start_client(r.ipt)
    sleep(0.1)



