#! /usr/bin python3.5
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import threading
import time
import getopt
import sys


threadnums = 2
coroutinenums = 50
last_succ_count = 0
last_fail_count = 0
succ_count = 0
fail_count = 0
local_count = threading.local()
lock = threading.Lock()
url_lists = None
glb_url = "http://www.baidu.com"
glb_time = 100
start_flag = False

async def get_page(urls):
    global succ_count
    global fail_count
    global glb_time

    header = {'User-Agent': 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'}


    if len(urls) > 1:
        for url in urls:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    lock.acquire()	
                    if resp.status == 200:
                        local_count.succ_count += 1
                    else:
                        local_count.fail_count += 1
                    lock.release()
    else:
        i = glb_time
        while i > 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(urls[0]) as resp:
                    lock.acquire()
                    if resp.status == 200:
                        local_count.succ_count += 1
                    else:
                        local_count.fail_count += 1
                    i -= 1
                    lock.release()

@asyncio.coroutine
def monitor():
    global succ_count
    global fail_count
    global last_succ_count
    global lock

    while True:
        lock.acquire()
        succ_count += local_count.succ_count
        fail_count += local_count.fail_count
        local_count.succ_count = 0
        local_count.fail_count = 0
        lock.release()
        r = yield from asyncio.sleep(1)

def threadfunc1(loop):
    global coroutinenums
    global url_lists
    global glb_url

    asyncio.set_event_loop(loop)
    tasks = []
    tasks.append(monitor())

    local_count.succ_count = 0
    local_count.fail_count = 0

    if url_lists:
        length = len(url_lists)
        urlspercoroutine = length / coroutinenums
        if urlspercoroutine > 1:
            urlspercoroutine = int(urlspercoroutine)
            i = 0
            while i < length:
                if i + urlspercoroutine < length:
                    temp_list = url_lists[i : i + urlspercoroutine]
                else:
                    temp_list = url_lists[i : ]
                tasks.append(get_page(temp_list))
                i += urlspercoroutine
        else:
            for url in url_lists:
                tasks.append(get_page([url]))
    else:
        for i in range(coroutinenums):
            tasks.append(get_page([glb_url]))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

def threadfunc2():
    global succ_count
    global fail_count
    global last_succ_count
    global last_fail_count
    global lock
    global start_flag
    i = 0
    while True:
        lock.acquire()
        if start_flag == False and succ_count != 0:
            start_flag = True
        if start_flag == True:
            i += 1
            print("{0} second : {1} times succ, {2} times fail, {3} total times".format(i, succ_count - last_succ_count, fail_count - last_fail_count, succ_count))
            print("Average process time : %.4f second" %(i / succ_count))
        last_succ_count = succ_count
        last_fail_count = fail_count
        
        lock.release()
        time.sleep(1)

def main():
    global threadnums
    global coroutinenums
    global glb_url
    global glb_time
    file_name = None

    try:
        options, args = getopt.getopt(sys.argv[1:], "ht:c:f:u:t:n:", ["help", "thread=", "coroutine=", "file=", "url=", "numbers="])
    except getopt.GetoptError:
        sys.exit()

    for name, value in options:
        if name in ("-h", "--help"):
            usage()
            exit()
        if name in ("-t", "--thread"):
            threadnums = int(value)
        if name in ("-c", "--coroutine"):
            coroutinenums = int(value)
        if name in ("-f", "--file"):
            file_name = value
        if name in ("-u", "--url"):
            glb_url = value
        if name in ("-n", "--numbers"):
            glb_time = int(value)

    if file_name:
        global url_lists
        url_lists = []
        for line in open(file_name, "r"):
            if line.strip() != "":
                url_lists.append(line)

    event_loop_list = []
    for i in range(threadnums):
        temp_loop = asyncio.new_event_loop()
        event_loop_list.append(temp_loop)

    threads = []
    threads.append(threading.Thread(target=threadfunc2))
    for i in range(threadnums):
        t = threading.Thread(target=threadfunc1, args=(event_loop_list[i],))
        threads.append(t)
    
    for t in threads:
        t.setDaemon(True)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("stop")
        exit()
def usage():
    print(u"""
    -h / --help:
    -t / --thread: thread number
    -c / --coroutine: coroutine number
    -f / --file: filename

    sample:
    # fts.py -t 3 -c 100 -n 100 -u http://www.baidu.com
    // create 3 threads, every thread create 100 coroutines, every coroutine request Baidu 100 times
    // sum : 3 * 100 * 100 = 10000 
    # fts.py -t 3 -c 100 -f url_list.txt
    //create 3 threads, every thread create 100 coroutines, every thread divided the file equally to every coroutines
    // sum: 3 * len(url_list.txt)
    """)

if __name__ == "__main__":  
    main()
