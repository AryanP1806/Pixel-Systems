import threading
import requests
from bs4 import BeautifulSoup

url = ['https://www.pixelitsolution.com/','https://www.pixelitsolution.com/pixel-privacy.html']

def fetch(url):
    response =requests.get(url)
    soup = BeautifulSoup(response.content,'html.parser')
    print(len(soup.text))

threads = []

for u in url:
    thread= threading.Thread(target=fetch, args=(u,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()