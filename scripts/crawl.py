"""crawl arxiv papers daily and upload to b2 cloud"""

import re
import os, os.path as op
import datetime
import json
import time
import logging
from dotenv import load_dotenv

import arxiv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

CATEGORIES = [
    "astro-ph.CO"
]

def arxiv_ingest_metadata(
    category: str = "astro-ph.CO",
    max_results: int = 50,
    output_dir: str = "data",
    b2: "B2Resource" = None
):
    # get output path setup
    catname = category.replace(".", "_")
    odir = op.join(output_dir, "metadata", catname)
    if not op.exists(odir): 
        logging.info(f"Creating directory {odir}")
        os.makedirs(odir)

    # get current metadata file which is the most recent sunday
    curr = get_past_sunday(1)
    past = get_past_sunday(2)
    curr_uri = f"metadata/{catname}/{curr.strftime('%Y-%m-%d')}.json"
    past_uri = f"metadata/{catname}/{past.strftime('%Y-%m-%d')}.json"     
    curr_file = op.join(output_dir, curr_uri)
    past_file = op.join(output_dir, past_uri)
    # download these files from b2
    logging.info(f"Downloading {curr_uri} from remote")
    b2.download(curr_uri, curr_file)
    logging.info(f"Downloading {past_uri} from remote")
    b2.download(past_uri, past_file)

    # load all entries from curr and past files
    old_entries = []
    for fname in [curr_file, past_file]:
        if op.exists(fname):
            with open(fname, "r") as f:
                old_entries += json.load(f)
    logging.info("Loaded {} old entries from past two weeks".format(len(old_entries)))

    # only keep ids
    old_entries_ids = [entry['id'] for entry in old_entries]
    del old_entries

    # parse arxiv metadata
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    articles = arxiv.Client().results(search)
    entries = []
    for result in articles:
        arxiv_id, ver = arxiv_url_to_id_and_ver(result.entry_id)
        if arxiv_id in old_entries_ids: continue
        entry = {
            'id': arxiv_id,
            'version': ver,
            'title': result.title,
            'abstract': result.summary,
            'authors': [author.name for author in result.authors],
            'category': category,
            'published': result.published.strftime('%Y-%m-%d-%H-%M-%S'),
        }
        entries.append(entry)

    logging.info(f"Found {len(entries)} new entries for category {category} from arxiv")
    logging.info(f"arxiv ids: {[entry['id'] for entry in entries]}")

    if len(entries) == 0:
        logging.info("No new entries found, nothing to do")
        return

    logging.info(f"Writing to {curr_file}")
    with open(curr_file, "a") as f:
        json.dump(entries, f)

    # upload to b2
    logging.info(f"Uploading {curr_file} to remote")
    b2.upload(curr_file, curr_uri)

    # also write to a local file for subsequent processing
    latest_file = op.join(odir, "latest.json")
    logging.info(f"Writing to {latest_file}")
    with open(latest_file, "w") as f:
        json.dump(entries, f)

    logging.info("Done")

# ----------------------------
# data service wrapper
# ----------------------------

class B2Resource:
    def __init__(self):
        endpoint = os.getenv("ENDPOINT")
        key_id = os.getenv("KEY_ID")
        application_key = os.getenv("APPLICATION_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.b2 = boto3.resource(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key,
            config=Config(signature_version='s3v4')
        )

    def upload(self, local_path, remote_path):
        try:
            self.b2.Bucket(self.bucket_name).upload_file(local_path, remote_path)
        except ClientError as ce:
            logging.error(ce)
    
    def download(self, remote_path, local_path):
        try:
            self.b2.Bucket(self.bucket_name).download_file(remote_path, local_path)
        except ClientError as ce:
            logging.error(ce)

# ----------------------------
# utility functions
# ----------------------------

def arxiv_url_to_id_and_ver(url):
    match = re.search(r'arxiv\.org/abs/(\d+\.\d+)(v\d+)?', url)
    if match:
        arxiv_id = match.group(1)
        version = match.group(2) or 'v1'
        return arxiv_id, version
    else:
        raise ValueError('Invalid arXiv URL')

def get_past_sunday(n=1):
    curr = datetime.datetime.now()
    while n > 0:
        sunday = curr - datetime.timedelta(days=curr.weekday()+1)
        curr = sunday 
        n -= 1
    return sunday

if __name__ == "__main__":
    load_dotenv()
    b2 = B2Resource()
    for cat in CATEGORIES:
        arxiv_ingest_metadata(category=cat, b2=b2)
        time.sleep(5)