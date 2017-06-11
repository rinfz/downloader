import aiohttp
import argparse
import asyncio
import json
import math
import os
import os.path
import requests

# TODO
# error checking
# adapt chunk size based on file size

CHUNK_SIZE = 1024 ** 2
AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '\
        'Chrome/41.0.2228.0 Safari/537.36'

async def _download(session, url, size, ref):
    start = ref * CHUNK_SIZE
    stop = start + CHUNK_SIZE -1
    if stop > size:
        stop = size
    async with session.get(url, headers={'User-Agent': AGENT, 'range': f'bytes={start}-{stop}'}) as response:
        return await response.read()

async def download(session, url):
    size = int(requests.head(url).headers['content-length'])
    chunks = math.ceil(size / float(CHUNK_SIZE))
    return await asyncio.gather(
        *(_download(session, url, size, x) for x in range(chunks))
    )

async def save(session, title, url):
    filename = os.path.join(args.dir, title.replace(' ', '_') + os.path.splitext(url)[1])
    if os.path.isfile(filename):
        print(f'Skipping {title}')
    else:
        content = await download(session, url)
        with open(filename, 'wb') as handle:
            for chunk in content:
                handle.write(chunk)
        print(f'Downloaded {title}!')
        await asyncio.sleep(10)

async def main(loop):
    if args.file:
        data = {}
        for file_ in args.resource:
            with open(file_, 'r') as handle:
                data.update(json.load(handle))
    else:
        data = {url.split('/')[-1]: url for url in args.resource}

    async with aiohttp.ClientSession(loop=loop) as session:
        for title, url in data.items():
            print(f'Downloading {title}...')
            await save(session, title, url)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', '-d', default='',
        help='Directory to save the files to')
    parser.add_argument('--file', '-f', action='store_true',
        help='Load resources from a json file, structured as: {filename: url}')
    parser.add_argument('resource', nargs='+',
        help='Resource(s) to download. Url by default. Pass the -f flag if the\n'
        'resource is a json file.')
    args = parser.parse_args()

    if args.dir and not os.path.exists(args.dir):
        os.makedirs(args.dir)

    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main(event_loop))
    finally:
        event_loop.close()
