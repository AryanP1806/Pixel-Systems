import time
import math
import threading
import multiprocessing
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import sys

sys.set_int_max_str_digits(1000000)

def fact(n):
    print("Computing...")
    result = math.factorial(n)
    return result

if __name__ == "__main__":
    no = [10,20,30]
    # no = [10, 20]
    start = time.time()
    with multiprocessing.Pool() as pool:
        result = pool.map(fact,no)
    end = time.time()

    print(result)
    print(end - start)

    start = time.time()
    for n in no:
        print(math.factorial(n))
    print(time.time()- start)