"""
Title: teamtrees
Description: Extract donated tree amount from teamtrees.org and make a graph that shows the progress

TODO:
    - [x] fix queue
    - [x] don't overwrite older data when new gets added
        - [x] read `data_id` from file if necessary
    - [x] correctly stop threads on `KeyboardInterrupt`
    - [ ] graph
    - [ ] file handler for safe reading and writing
"""

import requests
import time
from multiprocessing import Process, Lock, Queue, Event
from datetime import datetime
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
from matplotlib import animation, ticker

filename = "teamtrees.txt"

# remove unnecessary information
def strip_string(data):

    ending = "\" id=\"totalTrees\">0</div>"
    beginning = "<div class=\"counter\" data-count=\""

    if data.endswith(ending):
        data = data[:-len(ending)]
    if data.startswith(beginning):
        data = data[len(beginning):]

    return data

def get_next_id():
    try:
        data_file = open(filename, 'r')
        lines = data_file.readlines()
        data_file.close()
        return int(lines[len(lines)-1].split("\t")[0]) + 1
    except(IndexError):
        return 0

def thread_file_handler(filename, writequeue, readqueue):
    data_file = open(filename, 'a+')

def graph(parameter_list):
    figure = plt.figure()
    ax1 = figure.add_subplot(1, 1, 1)


    def animate(i):
        data = open(filename, 'r').readlines()
        time_array = []
        trees_array = []

        for line in data:
            if len(line) > 1:
                line = line.strip('\n')
                line = line.split('\t')
                time_array.append(datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S.%f'))
                trees_array.append(int(line[2]))

        ax1.clear()
        figure.autofmt_xdate()

        ax1.ticklabel_format(style='plain')
        ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax1.plot(time_array, trees_array)


    ani = animation.FuncAnimation(figure, animate, interval=1000)

    plt.subplots_adjust(left=0.16)
    plt.show()

# retrieve data from website
def retrieve_data(io_lock, run_event):
    url = 'https://teamtrees.org'
    data_id = get_next_id()
    data_file = open(filename, 'a')  # open file in append mode

    try:
        while (True):
            # get web response
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # extract data
            data = str(soup.find("div", {"id": "totalTrees"}))
            data = strip_string(data)

            # generate data entry with id and timestamp
            output = "{}\t{}\t{}\n".format(data_id, datetime.now(), data)
            io_lock.acquire()
            print(output, end="")
            io_lock.release()

            # write data to file
            data_file.write(output)
            data_id += 1

            # check if exit flag is set
            if(not run_event.is_set()):
                io_lock.acquire()
                print("data collection stopping...")
                io_lock.release()
                break

            time.sleep(10)

    except(KeyboardInterrupt):
        data_file.close()
        io_lock.acquire()
        print("data collection stopping...")
        io_lock.release()

    finally:
        data_file.close()


if __name__ == '__main__':
    try:
        # init multiprocessing lock and queue
        io_lock = Lock()
        queue = Queue()
        run_event = Event()
        run_event.set()

        # start thread
        data_process = Process(target=retrieve_data, args=(io_lock, run_event))
        data_process.start()


        io_lock.acquire()
        print("press \'q\' to quit\n")
        io_lock.release()

        while(True):
            exit_char = input()

            if(exit_char.lower() == 'q'):
                io_lock.acquire()
                print("stopping...")
                io_lock.release()

                run_event.clear()    # set exit flag
                data_process.join()      # wait for thread to exit
                break

    except(KeyboardInterrupt):
        io_lock.acquire()
        print("stopping...")
        io_lock.release()
        run_event.clear()            # set exit flag
        data_process.join(timeout=2)     # wait for thread to exit
        if data_process.is_alive():
            data_process.terminate()
