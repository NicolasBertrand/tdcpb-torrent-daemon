#!/usr/bin/env python

import os
basedir = os.path.abspath(os.path.dirname(__file__))
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]



from ttdmodel import db
db.init_app( os.environ.get('TTD_DATABASE_URL'))
print db.engine
db.Model.metadata.create_all(db.engine)

