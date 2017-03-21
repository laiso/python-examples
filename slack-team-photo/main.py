import os
import logging
import urllib.request
import concurrent.futures
import hashlib
import io
from urllib.error import HTTPError

from PIL import Image
from slackclient import SlackClient

ICON_SIZE = 192

def get_image_urls(token):
    client = SlackClient(token)
    users = client.api_call("users.list")
    urls = []
    for member in users.get('members'):
        profile = member.get('profile')
        image = profile.get('image_192')
        urls.append(image)
    return urls


def get_images_from_urls(urls):
    images = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = { executor.submit(_get_image, url): url for url in urls  }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                image = future.result()
            except HTTPError as error:
                logging.error(error, url, future)
            images.append(image)
        return images


def _get_image(url):
    if os.path.exists(_cache_path_for(url)):
        print("Cache: ", url)
        return Image.open(_cache_path_for(url))

    print("Download: ", url)
    with urllib.request.urlopen(url) as conn:
        buffer = conn.read()
        _save_to_cache(url, buffer)
        byteio = io.BytesIO(buffer)
        return Image.open(byteio)

def _save_to_cache(url, buffer):
    with open(_cache_path_for(url), 'wb') as f:
        f.write(buffer)

def _cache_path_for(url):
    digest = hashlib.md5(url.encode('utf-8')).hexdigest()
    return "data/{}.png".format(digest)

def calc_rect(num, x=1, y=1):
    if x * y > num:
        return (x-1, y)
    return calc_rect(num, x + 1, y + 1)

def save_images(images, path):
    i, h, v = 1, 0, 0
    x, y = calc_rect(len(images))
    canvas = Image.new('RGB', (ICON_SIZE * x, ICON_SIZE * y))
    for image in images:
        canvas.paste(image, (h, v))
        h += ICON_SIZE
        if i % x == 0:
            h = 0
            v += ICON_SIZE
        i += 1
    canvas.save(path)

if __name__ == '__main__':
    token = os.environ['SLACK_TOKEN']
    urls = get_image_urls(token)
    images = get_images_from_urls(urls)
    save_images(images, 'out.png')
    print("done")
