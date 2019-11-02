"""
Title: teamtrees
Description: Extract donated tree amount from teamtrees.org and make a graph that shows the progress

TODO:
    - [x] fix queue
    - [x] don't overwrite older data when new gets added
        - [ ] read `i` from file if necessery
    - [ ] correctly stop threads on `KeyboardInterrupt` ???
    - [ ] graph
"""

import requests
import time
import sys
import os
from multiprocessing import Process, Lock, Queue
from datetime import datetime
from bs4 import BeautifulSoup

# remove unnecessary information
def strip_string(data):

    ending = "\" id=\"totalTrees\">0</div>"
    beginning = "<div class=\"counter\" data-count=\""

    if data.endswith(ending):
        data = data[:-len(ending)]
    if data.startswith(beginning):
        data = data[len(beginning):]

    return data

# retrieve data from website
def retrieve_data(data_flag, queue):
    url = 'https://teamtrees.org'
    data_file = open("teamtrees.txt", 'a')  # open file in append mode
    i = 0

    try:
        while (True):
            # get web response
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # extract data
            data = str(soup.find("div", {"id": "totalTrees"}))
            data = strip_string(data)

            # generate data entry with id and timestamp
            output = "{}\t{}\t{}\n".format(i, datetime.now(), data)
            print(output, end = "")
            
            # write data to file
            data_flag.acquire()
            data_file.write(output)
            i += 1
            data_flag.release()

            # check if exit flag is set
            if(not queue.empty() and not queue.get()):
                print("thread stopping...")
                break

            time.sleep(5)
    finally:
        data_file.close()


if __name__ == '__main__':
    # init multiprocessing lock and queue
    data_flag = Lock()
    queue = Queue()

    # start thread
    process = Process(target = retrieve_data, args = (data_flag, queue))
    process.start()

    data_flag.acquire()
    print("press \'q\' to quit\n")
    data_flag.release()

    while(True):
        exit_char = input()

        if(exit_char.lower() == 'q'):
            print("Stopping...")
            queue.put(False)    # set exit flag
            process.join()      # wait for thread to exit
            data_flag.acquire()
            print("stopping...")
            data_flag.release()
            break
