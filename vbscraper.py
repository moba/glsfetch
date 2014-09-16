#!/usr/bin/env python
# encoding: utf-8

# This file is in the Public Domain as specified by
# http://creativecommons.org/publicdomain/zero/1.0/

import requests
import lxml.html
import getpass
import bs4


class VBSession(object):
    """
    Volksbank Online Banking Session
    """

    def __init__(self, base_url, bank_id, verbose=True):

        # Initialize HTTP session
        self.s = requests.Session()

        self.base_url = base_url
        self.bank_id = bank_id
        self.login_url = '/ptlweb/WebPortal?bankid={}'.format(self.bank_id)
        self.verbose = verbose

    def login(self, username):
        """
        Login to Volksbank Online Banking
        """

        if self.verbose:
            print('Login to Volksbank Online Banking')

        # Get Volksbank Banking login page
        r = self.s.get(self.base_url + self.login_url)
        login_page = lxml.html.fromstring(r.text)

        # Get Volksbank Banking login form
        login_form = login_page.forms[0]

        # Fill in username and password
        login_data = dict(login_form.fields)
        login_data['pruefenPIN_V01_VO.strVrKennungOderAlias'] = username
        login_data['pruefenPIN_V01_VO.txtKkdPwTrp'] = getpass.getpass()
        login_data['event___login'] = 'Login'

        # Post login
        r = self.s.post(
            self.base_url + login_form.action,
            data=login_data
        )

        # Parse returned page
        soup = bs4.BeautifulSoup(r.text)

        if not soup.find(text='Finanzstatus'):
            raise RuntimeError('Login to Volksbank Online Banking failed.')

        self.logout_url = soup.find('a', id='ummelden')['href']
        self.postbox_url = soup.find('a', text='Postkorb')['href']

        if self.verbose:
            print('Logged in to Volksbank Online Banking')

        return True

    def logout(self):
        """
        Logout from Volksbank Online Banking
        """

        if self.verbose:
            print('Log out from Volksbank Online Banking')

        r = self.s.get(self.base_url + self.logout_url)
        ret = r.status_code == 200
        self.s.close()

        return ret
