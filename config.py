# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    TTD_DATABASE_URL=os.environ.get('TTD_DATABASE_URL')

config={
    'default':Config
        }
