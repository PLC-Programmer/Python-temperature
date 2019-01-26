#!/usr/bin/env python
"""This module cyclically polls a web page for temperature
measurement data.
It uses primitive web scraping.
It stores polling result on disk."""
# Polling_Munich_temperature.py
#
# RSa, 21.01.2019, 22.01.2019, 24.01.2019, 26.01.2019
#
# to-do:
#
#
#
#
# cyclically read every 15 min temperature data from:
#   Meteorologisches Institut München
#   location:  Theresienstr.37,
#
# time stamped data published at: URL1
# --> pushed data for each minute
#
#
# developmet env.: Win7 64 Bit, Spyder 3.2.3
# --> test: OK
#
#
# --> moved to "online" env. at:
#  - server ubuntu-FTP with Ubuntu 18.04.1 LTS, 64 Bit:
#    - IP = 192.168.0.110
#    - auto start with via entry in: /etc/init.de/my.script
#  --> test:
#
#
# PEP8 check: http://pep8online.com:
# static code analysis with Pylint: 10.00/10
#

from urllib.request import urlopen
from urllib.error import HTTPError
import re  # regular expressions
import datetime  # date and time functions
import time  # sleep function


# Beautiful Soup: HTML parser
# https://en.wikipedia.org/wiki/Beautiful_Soup_(HTML_parser)
from bs4 import BeautifulSoup


############################################
# user input data:
#
# https://www.meteo.physik.uni-muenchen.de/mesomikro/stadt/messung.php
URL1 = "https://www.meteo.physik.uni-muenchen.de/mesomikro/stadt/messung.php"

MEAS_DATA_FILE = "temp_log_Munich.txt"  # current dir is working dir
WAIT_OUT = 15  # sleep NN minutes between reading last measurement
#
# end of user input data  ##################


############################################
#
# customer functions:

# custome function to get html content of target page at url:
def get_meas_html(url):
    """This function reads the content of a web page."""

    try:
        html_obj = urlopen(url)
    except HTTPError:
        return None
    try:
        # specify parser type as html:
        bs_obj = BeautifulSoup(html_obj, "html.parser")
    except AttributeError:
        return None
    return bs_obj


# customer function for date and time handling:
# - get date and time from time stamp: "Messwerte vom 21.1.2019 00:14"
def get_time_stamp(bs_obj):
    """This function reads time stamp data from a
    beautiful soup object."""
    # - use raw strings:
    time_stamp_re = re.compile(r"Messwerte vom ")

    # time_stamp is of type: bs4.element.NavigableString
    # --> convert to string type:
    time_stamp = str(bs_obj.find(text=time_stamp_re))

    time_re = re.compile(r"\d+\.\d+\.20\d{2} \d+\:\d+")
    try:
        # this command can crash: AttributeError:
        # - 'NoneType' object has no attribute 'group'
        time_str = re.search(time_re, time_stamp).group()
    except AttributeError:
        return None
    return time_str

#
# end of custome functions #################


############################################
# main program body:
#
while True:

    # type of MEAS_PAGE1BS is bs4.BeautifulSoup:
    MEAS_PAGE1BS = get_meas_html(URL1)

    if MEAS_PAGE1BS is None:
        print("Web page with measurement data could not be found!")
    else:
        TIME1 = get_time_stamp(MEAS_PAGE1BS)

        if TIME1 is None:
            print("Cannot get any time stamp data from web page!")

        else:
            # get time stamp of measurement into format:
            #   2018/12/15<TAB>23:42:56
            # reason: to be compatible with UDP Perl script
            TIME1A = datetime.datetime.strptime(TIME1, "%d.%m.%Y %H:%M")

            DATE_MEAS = TIME1A.date().strftime("%Y/%m/%d")
            TIME_MEAS = TIME1A.time().strftime("%H:%M:%S")

            # get all HTML <td> tags, i.e. standard cells in an HTML table:
            # - type of soup is bs4.element.ResultSet
            SOUP = MEAS_PAGE1BS.findAll("td")

            # use raw strings:
            TEMPS_RE = re.compile(r"\-*\d+\.\d+ °C")  # find all temperatures

            # go through soup:
            MEAS_TEMPS = []
            # see here:
            #   https://stackoverflow.com/questions/36076052/
            #   beautifulsoup-find-all-on-bs4-element-resultset-object-or-list
            for td in SOUP:
                MEAS_TEMPS.extend(td.find_all(text=TEMPS_RE))

            # get only the second measurement for
            # the "Lufttemperatur" at "30.0 m":
            # types here are: bs4.element.NavigableString
            # --> convert so string type (str):
            TEMP_1_RAW = str(MEAS_TEMPS[1])  # ' -2.6 °C'

            ##########################################
            # measurement data handling:
            #
            # get a float number here..
            MEAS_RE = re.compile(r"\-*\d+\.\d+")
            TEMP_RE = re.search(MEAS_RE, TEMP_1_RAW)
            TEMP_FL = float(TEMP_RE.group())
            # ..and convert it to a string:
            TEMP_STR = "{:.2f}".format(TEMP_FL)
            # print(TEMP_STR)
            #
            # end of measurement data handling
            ##########################################

            # build a line to bring all data together:
            LINE = "\n" + TEMP_STR + "\t" + DATE_MEAS + "\t" + TIME_MEAS

            ##########################################
            # write to disk: append file MEAS_DATA_FILE
            #
            F = open(MEAS_DATA_FILE, "a")
            F.write(LINE)
            F.close()

    time.sleep(WAIT_OUT * 60)  # sleeping NN seconds


# end of main program body  ################


# target result file has to look like this:
# 23.79	2018/12/15	23:42:56
# 23.84	2018/12/15	23:57:58
# 23.82	2018/12/16	00:13:00


# end of Polling_Munich_temperature.py
