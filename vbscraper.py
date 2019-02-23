#!/usr/bin/env python
# encoding: utf-8

# SPDX-License-Identifier: CC0-1.0
# This file is in the Public Domain as specified by
# http://creativecommons.org/publicdomain/zero/1.0/

# grabbed from https://github.com/andsor/VB-Scraper (Andreas Sorge)
# and slightly modified

import requests
import lxml.html
import bs4
import collections
import datetime
import tempfile
import shutil
import os
import os.path

html_parser = "html.parser" # let BeautifulSoup choose html parser

PostboxDocument = collections.namedtuple(
    'PostboxDocument',
    [
        'msg_date',
        'msg_type',
        'is_new',
        'url',
        'subject',
        'postbox_page',
    ]
)


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

    def login(self, username, password):
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
        login_data['pruefenPIN_V01_VO.txtKkdPwTrp'] = password
        login_data['event___login'] = 'Login'

        # Post login
        r = self.s.post(
            self.base_url + login_form.action,
            data=login_data
        )

        # Parse returned page
        soup = bs4.BeautifulSoup(r.text, html_parser)

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

    def postbox_items(self):
        """
        Iterate through the postbox items
        """

        if self.verbose:
            print("Access postbox")

        # Get Postbox page
        r = self.s.get(self.base_url + self.postbox_url)

        # Parse Postbox page
        soup = bs4.BeautifulSoup(r.text, html_parser)

        # Get number of pages
        li = soup.find('li', attrs={'class': 'gad-paginationActivePageNumber'})

        if not li.text.strip() == '1':
            raise RuntimeError('Postbox does not start with page 1')

        # loop through postbox pages
        ret = []

        while True:

            # Get current page number
            li = soup.find(
                'li', attrs={'class': 'gad-paginationActivePageNumber'}
            )

            page_number = li.text.strip()

            if self.verbose:
                print("Postbox page {}".format(page_number))

            # loop through documents on the current page
            for tr in soup.table.tbody.findChildren('tr'):

                is_new = 'gad-tableEntryHighlighted' in tr['class']

                msg_date = datetime.datetime.strptime(
                    tr.find(
                        'td', attrs={'class': 'gad-dateColumn'}
                    ).text.strip(),
                    "%d.%m.%Y %H:%M"
                )

                a = tr.find(
                    'td', attrs={'class': 'gad-textColumn'}
                ).a

                url = a['href']

                subject = ' '.join([
                    str2 for str2 in [
                        str.strip() for str in a.text.split('\n')
                    ] if str2
                ])

                msg_type = tr.find(
                    'td', attrs={'class': 'gad-textColumn'}
                ).a.span.text

                ret.append(PostboxDocument(
                    msg_date=msg_date,
                    msg_type=msg_type,
                    url=url,
                    is_new=is_new,
                    subject=subject,
                    postbox_page=page_number,
                ))

            # terminate loop if this was the last page of the postbox
            a_next_page = soup.find('a', title='nächste Seite')

            if a_next_page.get('disabled'):
                break

            # get next page
            r = self.s.get(self.base_url + a_next_page['href'])

            # Parse Postbox page
            soup = bs4.BeautifulSoup(r.text, html_parser)

        return ret

    def download_document(self, document, destinations):
        """
        Download a document
        """

        if self.verbose:
            print("Access postbox")

        # Get Postbox page
        r = self.s.get(self.base_url + self.postbox_url)

        # Parse Postbox page
        soup = bs4.BeautifulSoup(r.text, html_parser)

        # Get current page number
        li = soup.find(
            'li', attrs={'class': 'gad-paginationActivePageNumber'}
        )
        page_number = li.text.strip()

        if not page_number:
            raise RuntimeError('Postbox current page number not found')

        if not document.postbox_page == page_number:
            # get postbox page
            if self.verbose:
                print("Access postbox page {}".format(document.postbox_page))

            while not li.text.strip() == document.postbox_page:
                if li.find_next_sibling():
                    li = li.find_next_sibling()
                else: # page not in current scope, move on to last found page and look again
                    self.postbox_url = li.a['href']
                    self.download_document(document, destinations)
                    return


            page_url = li.a['href']
            r = self.s.get(self.base_url + page_url)
            assert r.status_code == 200

        # get message page
        if self.verbose:
            print(u"Download document {}".format(document.subject))

        r = self.s.get(self.base_url + document.url)

        # parse message page
        soup = bs4.BeautifulSoup(r.text, html_parser)

        #subject = msg_soup.find(
        #    'label', attrs={'for': 'messageSenderSubject'}
        #).parent.find_next_sibling().span.text

        attachment_a = soup.find(
            'a', title='Anhang öffnen'
        )

        if not attachment_a: # message in postbox has no attachment to download
            return

        attachment_url = attachment_a['href']

        filename = attachment_a.text

        # download document
        r = self.s.get(self.base_url + attachment_url, stream=True)

        if not r.status_code == 200:
            raise RuntimeError('Download failed.')

        r.raw.decode_content = True

        # copy http data to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            shutil.copyfileobj(r.raw, fp)
            tmp_filename = fp.name

        # copy file to destinations
        for dest in destinations:

            dest_filename = os.path.join(dest, filename)

            if self.verbose:
                print("Copy to {}".format(dest_filename))

            if os.path.exists(dest_filename):
                print('"{}" already exists'.format(dest_filename))
                continue

            shutil.copyfile(tmp_filename, dest_filename)

        # delete temporary file
        os.unlink(tmp_filename)

        return True
