#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
from distutils.core import setup

setup(
    name         = "tdcpb-torrent-daemon",
    description  = "Monitor tdcpb torrents ",
    author       = "Nicolas Bertrand",
    author_email = "nicolas.bertrand@tdcpb.org",
    version      = "0.1",
    scripts      = ["run-ttd"],
    packages     = ["ttd"],
)
