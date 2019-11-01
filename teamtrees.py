"""
Title: teamtrees
Description: Extract donated tree amount from teamtrees.org and make a graph that shows the progress

TODO:
    - graph
    - fix queue
    - don't overwrite older data when new gets added
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
def retrieve_data(dataflag, queue):
    url = 'https://teamtrees.org'
    data_file = open("teamtrees.txt", 'w')
    i = 0

    try:
        while (True):
            # get web response
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # extract data
            data = str(soup.find("div", {"id": "totalTrees"}))
            data = strip_string(data)

            # write data to file with id and timestamp
            output = "{}\t{}\t{}\n".format(i, datetime.now(), data)
            dataflag.acquire()
            print(output)
            dataflag.release()

            data_file.write(output)
            i += 1

            if(queue.get() == False):
                print("thread stopping...")
                break

            time.sleep(5)
    finally:
        data_file.close()


if __name__ == '__main__':
    try:
        # init multiprocessing lock and queue
        dataflag = Lock()
        queue = Queue()

        # start thread
        process = Process(target = retrieve_data, args = (dataflag, queue))
        process.start()

    except KeyboardInterrupt:
        print("Stopping...")
        queue.put(False)    # set exit flag
        process.join()      # wait for thread to exit
        dataflag.acquire()
        print("stopping...")
        dataflag.release()