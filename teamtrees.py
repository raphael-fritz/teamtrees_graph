""" Extract donated tree amount from teamtrees.org and make a graph that shows the progress """

import requests
import time
from multiprocessing import Process, Lock, Queue
from datetime import datetime
from bs4 import BeautifulSoup

# removing unnecessary information
def strip_string(data):

    ending = "\" id=\"totalTrees\">0</div>"
    beginning = "<div class=\"counter\" data-count=\""

    if data.endswith(ending):
        data = data[:-len(ending)]
    if data.startswith(beginning):
        data = data[len(beginning):]

    return data

# retrieving data from website
def retrieve_data(dataflag, q):
    url = 'https://teamtrees.org'
    save_file = open("teamtrees.txt", 'w')
    i = 0

    try:
        while (True):
            #getting website
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            #extracting data
            data = str(soup.find("div", {"id": "totalTrees"}))
            data = strip_string(data)

            #saving data to file with timestamp
            output = str(i) + "    " + str(datetime.now()) + "    " + data + "\n"
            dataflag.acquire()
            print(output)
            dataflag.release()

            save_file.write(output)
            i += 1

            if(q.get()==False):
                print("thread stopping")

            time.sleep(2)
    finally:
        save_file.close()


if __name__ == '__main__':

    # initializing multiprocessing Lock and Queue
    dataflag = Lock()
    q = Queue()
    
    #starting thread
    p = Process(target=retrieve_data, args=(dataflag,q,))
    p.start()

    dataflag.acquire()
    print("press \'e\' to exit\n")
    dataflag.release()

    #collect data until interrupted
    while(True):
        exit_char = input()    

        if(exit_char.lower() == 'e'):
            q.put(False)
            dataflag.acquire()
            print("stopping...")
            dataflag.release()

            p.join()
            break
        time.sleep(1)
