"""
Title: teamtrees
Description: Extract donated tree amount from teamtrees.org and make a graph that shows the progress

TODO:
    - [x] fix queue
    - [x] don't overwrite older data when new gets added
        - [ ] read `i` from file if necessary
    - [x] correctly stop threads on `KeyboardInterrupt`
    - [ ] graph
"""

import requests
import time
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
def retrieve_data(io_lock, queue):
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
            io_lock.acquire()
            print(output, end="")
            io_lock.release()

            # write data to file
            data_file.write(output)
            i += 1

            # check if exit flag is set
            if(not queue.empty() and not queue.get()):
                io_lock.acquire()
                print("thread stopping...")
                io_lock.release()
                break

            time.sleep(10)

    except(KeyboardInterrupt):
        data_file.close()
        io_lock.acquire()
        print("thread stopping...")
        io_lock.release()

    finally:
        data_file.close()


if __name__ == '__main__':
    try:
        # init multiprocessing lock and queue
        io_lock = Lock()
        queue = Queue()

        # start thread
        process = Process(target=retrieve_data, args=(io_lock, queue))
        process.start()

        io_lock.acquire()
        print("press \'q\' to quit\n")
        io_lock.release()

        while(True):
            exit_char = input()

            if(exit_char.lower() == 'q'):
                io_lock.acquire()
                print("stopping...")
                io_lock.release()

                queue.put(False)    # set exit flag
                process.join()      # wait for thread to exit
                break

    except(KeyboardInterrupt):
        io_lock.acquire()
        print("stopping...")
        io_lock.release()
        queue.put(False)            # set exit flag
        process.join(timeout=2)     # wait for thread to exit
        if process.is_alive():
            process.terminate()
