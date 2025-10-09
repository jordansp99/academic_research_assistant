import time
import requests
import random
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def can_fetch(url, user_agent='*'):
    # it is important to respect robots.txt to be a good citizen of the web
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"error reading robots.txt: {e}")
        return False

def make_request(url, headers):
    if not can_fetch(url, headers['User-Agent']):
        print(f"crawling disallowed for {url} by robots.txt")
        return None

    # exponential backoff is used to avoid overwhelming the server with requests
    retries = 5
    delay = 1
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"rate limited. retrying in {delay} seconds...")
                time.sleep(delay + random.uniform(0, 1))
                delay *= 2
            else:
                raise e
        except requests.exceptions.RequestException as e:
            print(f"an error occurred: {e}")
            break
    return None
