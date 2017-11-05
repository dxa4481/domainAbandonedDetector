import socket
import requests
import time
import Queue
import json
from bs4 import BeautifulSoup
from urlparse import urlparse
from threading import Thread
from time import sleep

def main():
    q = Queue.Queue()
    with open("domains") as domain_file:
        hosts_list = domain_file.readlines()
    for host in hosts_list:
        q.put(host.strip())
    for i in range(30):
        t = Thread(target=make_check_url, args=(q,))
        t.start()

def print_results(results, domain, q):
    if not results:
        print "nothing in {} hosts remaining: {}".format(domain, q.qsize())
    else:
        print "Found results on {}".format(domain)
        print json.dumps(results, sort_keys=True, indent=4)


def make_check_url(q):
    while True:
        try:
            domain = q.get(block=False)
        except Queue.Empty:
            return True
        if domain.startswith("http://") or domain.startswith("https://"):
            results = get_links(domain)
            print_results(results, domain, q)
        else:
            results = get_links("http://" + domain)
            print_results(results, domain, q)
            results = get_links("https://" + domain)
            print_results(results, domain, q)



def hostname_resolves(hostname):
    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False

def get_links(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        stop = time.time()
        #print("initial request {}".format(stop-start))
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.InvalidURL) as e:
        return {}
    html = r.text
    start = time.time()
    soup = BeautifulSoup(html, "html.parser")
    stop = time.time()
    #print("Loading html into soup {}".format(stop-start))
    found_domains = {}
    link_tags = ['a', 'link', 'script', 'form,', 'img', 'object', 'iframe']
    link_attributes = ['href', 'src', 'data', 'action']
    start_ittr = time.time()
    for link_tag in link_tags:
        found_tags = soup.find_all(link_tag)
        for found_tag in found_tags:
            for link_attribute in link_attributes:
                try:
                    found_link = found_tag[link_attribute]
                except KeyError:
                    continue
                domain = urlparse(found_link).netloc
                if domain:
                    start = time.time()
                    resolves = hostname_resolves(domain)
                    stop = time.time()
                    #print("dns resolution {}".format(stop-start))
                    if not resolves:
                        if domain in found_domains:
                            found_domains[domain].append(link_tag)
                        else:
                            found_domains[domain] = [link_tag]
    stop_ittr = time.time()
    #print("Doing all the parsing {}".format(stop_ittr-start_ittr))
    return found_domains

main()
