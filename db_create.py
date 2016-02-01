import os
import sys

from ttd import db
from ttd.models import Client, Torrent

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
db.Model.metadata.create_all(db.engine)
