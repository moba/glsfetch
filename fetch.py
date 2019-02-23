#!/usr/bin/env python
# encoding: utf-8

# SPDX-License-Identifier: CC0-1.0
# This file is in the Public Domain as specified by
# http://creativecommons.org/publicdomain/zero/1.0/

import vbscraper
import configparser
import getpass
from appdirs import *

appname = "glsfetch"
appauthor = "glsfetch"
configfile = user_data_dir(appname, appauthor, roaming=False)+".ini"

config = configparser.ConfigParser()
config.read(configfile)

if not config['bank']:
    print(configfile + " not found. Please read instructions (copy and edit example.ini).")
    sys.exit(1)

base_url = config['bank']['base_url']
bank_id = config['bank']['bank_id']
username = config['account']['username']
if 'password' in config['account']:
    password = config['account']['password']
else:
    password = getpass.getpass()

scraper = vbscraper.VBSession(base_url=base_url, bank_id=bank_id)
scraper.login(username=username, password=password)

documents = list(scraper.postbox_items())

for document in documents:
    # comment next line if you want to fetch all documents, not only new ones
    if not document.is_new: continue
    # unused in this example: put documents in another directory
    directory = ""
    scraper.download_document(document, [directory])

scraper.logout()