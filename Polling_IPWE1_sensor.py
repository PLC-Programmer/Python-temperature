#!/usr/bin/env python
# Polling_IPWE1_sensor.py
#
# RSa, 11.01.2019, 13.01.2019, 15.01.2019, 21.1.2019
#
# to-do:
#   -
#
#
#
# cyclically read every 15 min outside temperature measurement data from:
#   IP-Wetterdatenempfänger IPWE 1, V1.1
#   ELV Elektronik AG
#   sensor type: T/F on address 1
#   location: Berg-am-Laim condo balcony
#
# time stamped data published at: http://192.168.0.146/ipwe.cgi
# ATTENTION: presence of measurement data NOT RELIABLE!?!
#            => measurement data goes on and off sporadically!
#            --> challenge for this program:
#              --> at the moment: just skip this cycle of reading
#                                 for another 15 minutes
#
# uses primitive web scraping
# stores polling result on disk
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
# PEP8 check: http://pep8online.com: OK
#

from urllib.request import urlopen
from urllib.error import HTTPError

# Beautiful Soup: HTML parser
# https://en.wikipedia.org/wiki/Beautiful_Soup_(HTML_parser)
from bs4 import BeautifulSoup

import re  # regular expressions
import datetime  # date and time functions
import time  # sleep function
import os.path  # to check for existing file

############################################
# user input data:
#
ip_addr = "192.168.0.146"
meas_data_file = "temp_log_IPWE1.txt"  # current dir is working dir
WAIT_OUT = 15  # sleep NN minutes between reading last measurement
#
# end of user input data  ##################


url1 = "http://" + ip_addr + "/history1.cgi"


############################################
#
# custome function to get html content of target page at url:
def get_meas_html(url):
    try:
        html_obj = urlopen(url)
    except HTTPError as e:
        return None
    try:
        # specify parser type:
        bs_obj = BeautifulSoup(html_obj, "html.parser")
    except AttributeError as e:
        return None
    return bs_obj
# end of custome functions #################


############################################
# main program body:
#
while True:

    # type of meas_page1bs is bs4.BeautifulSoup:
    meas_page1bs = get_meas_html(url1)

    if meas_page1bs is None:
        print("Web page with measurement data could not be found!")
    else:
        # get all HTML <td> tags, i.e. standard cells in an HTML table:
        # - type of soup is bs4.element.ResultSet
        soup = meas_page1bs.findAll("td")

        # use raw strings:
        times_re = re.compile(r"\d+ min \d+ sek")  # find all times
        temps_re = re.compile(r"\-*\d+\.\d+ °C")  # find all temperatures

        # go through soup:
        meas_times = []
        meas_temps = []
        # see here:
        #   https://stackoverflow.com/questions/36076052/
        #   beautifulsoup-find-all-on-bs4-element-resultset-object-or-list
        for td in soup:
            meas_times.extend(td.find_all(text=times_re))
            meas_temps.extend(td.find_all(text=temps_re))

        # get only the last measurement:
        # types here are: bs4.element.NavigableString
        # --> convert so string type (str):

        time_diff1_raw = str(meas_times[0])  # '3 min 1 sek'
        # ATTENTION: delay can be more than 60 min!!

        time_diff1_list = time_diff1_raw.split(" ")
        time_diff1_raw_min = int(time_diff1_list[0])
        time_diff1_raw_sec = int(time_diff1_list[2])

        temp_1_raw = str(meas_temps[0])  # ' -2.6 °C'

        ##########################################
        # date and time handling:
        #
        # seconds since last time stamp as int type:
        time_diff1_sec = time_diff1_raw_min * 60 + time_diff1_raw_sec

        # get current date and time as datetime.datetime..
        # ..and make the time of the time stamp:
        now = datetime.datetime.now()
        then = now - datetime.timedelta(seconds=time_diff1_sec)

        # get time stamp of measurement into format: 2018/12/15<TAB>23:42:56
        # reason: to be compatible with UDP Perl script
        # types: str
        date_meas = then.date().strftime("%Y/%m/%d")
        time_meas = then.time().strftime("%H:%M:%S")

        ##########################################
        # measurement data handling:
        #
        # get a float number here..
        meas_re = re.compile(r"\-*\d+\.\d+")
        temp_re = re.search(meas_re, temp_1_raw)
        temp_fl = float(temp_re.group())
        # ..and convert it to a string:
        temp_str = "{:.2f}".format(temp_fl)
        print(temp_str)

        ##########################################
        # build a line to bring all data together:
        line = "\n" + temp_str + "\t" + date_meas + "\t" + time_meas

        ##########################################
        # check for an existing log file:
        if os.path.exists(meas_data_file):

            ##########################################
            # check the last existing time stamp:
            # --> don't save an older measurement
            #
            # get last measurement:
            f1 = open(meas_data_file, "r")
            for line1 in f1.readlines():
                meas1 = line1
            f1.close

            # get date and time from last measurment:
            # e.g.: 23.79	2018/12/15	23:42:56
            meas1a = meas1.split("\t")
            meas1_stamp_str = meas1a[1] + " " + meas1a[2]

            # convert to datetime.datetime:
            meas1_stamp = \
                datetime.datetime.strptime(meas1_stamp_str,
                                           "%Y/%m/%d %H:%M:%S")

            # older time < newer time is True:
            if meas1_stamp >= then:
                print("Last polled measurement has no later timestamp \
and thus won't be saved to disk!")
            # timestamp of last measurement is OK:
            else:
                # write to disk: append file meas_data_file
                f1 = open(meas_data_file, "a")
                f1.write(line)
                f1.close

        else:
            # create a new log file:
            f1 = open(meas_data_file, "w")
            f1.write("temperature\tdate\ttime")
            # ..and save the first measurement:
            f1.write(line)
            f1.close

    time.sleep(WAIT_OUT * 60)  # sleeping NN seconds


# end of main program body  ################


# target result file has to look like this:
# temperature	date	time
# 23.79	2018/12/15	23:42:56
# 23.84	2018/12/15	23:57:58
# 23.82	2018/12/16	00:13:00


# end of Polling_IPWE1_sensor.py
