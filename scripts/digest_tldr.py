"""

"""
import os, os.path as op
import json
import logging
import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

from dotenv import load_dotenv
from crawl import get_past_sunday
from llm_utils import ArxivAgent
from data_utils import B2Resource

CATEGORIES = [
    "astro-ph.CO"
]

def digest_tldr(
    category: str = "astro-ph.CO",
    output_dir: str = "data",
    b2: "B2Resource" = None,
    agent: "ArxivAgent" = None
):
    catname = category.replace(".", "_")

    # get latest metadata
    latest_meta_uri = f"metadata/{catname}/latest.json"
    logging.info(f"downloading latest metadata file from remote: {latest_meta_uri}")
    latest_meta_file = op.join(output_dir, latest_meta_uri)
    if not op.exists(op.dirname(latest_meta_file)):
        os.makedirs(op.dirname(latest_meta_file))
    b2.download(latest_meta_uri, latest_meta_file)

    with open(latest_meta_file, "r") as f:
        articles = json.load(f)
    logging.info(f"loaded {len(articles)} articles from {latest_meta_file}")

    # get current tldr file
    curr = get_past_sunday(1)
    curr_uri = f"tldr/{catname}/{curr.strftime('%Y-%m-%d')}.json"
    curr_file = op.join(output_dir, curr_uri)
    if not op.exists(op.dirname(curr_file)):
        os.makedirs(op.dirname(curr_file))
    logging.info(f"downloading current tldr file from remote: {curr_uri}")
    b2.download(curr_uri, curr_file)
    
    if op.exists(curr_file):
        with open(curr_file, "r") as f:
            tldrs = json.load(f)
        logging.info(f"loaded {len(tldrs)} tldrs from {curr_file}")
    else:
        logging.info(f"no tldr file found")
        tldrs = []

    tldr_ids = [tldr['id'] for tldr in tldrs]
    new_tldrs = []
    for article in articles:
        if article['id'] in tldr_ids: continue
        logging.info(f"generating tl;dr for {article['id']}")
        abstract = article['abstract'].replace("\n", " ")
        tldr = agent.tldr(abstract)
        
        new_tldrs.append({
            'id': article['id'],
            'tldr': tldr
        })

    logging.info(f"adding {len(new_tldrs)} tldrs to {curr_file}")
    with open(curr_file, "w") as f:
        json.dump(tldrs + new_tldrs, f) 

    logging.info(f"uploading {curr_file} to remote")
    b2.upload(curr_file, curr_uri)

    # also store the latest for further processing
    latest_uri = f"tldr/{catname}/latest.json"
    latest_file = op.join(output_dir, latest_uri)
    with open(latest_file, "w") as f:
        json.dump(new_tldrs, f)
    logging.info(f"uploading {latest_file} to remote")
    b2.upload(latest_file, latest_uri)

    logging.info("Done")

if __name__ == "__main__":
    load_dotenv()

    agent = ArxivAgent()
    b2 = B2Resource()

    for cat in CATEGORIES:
        digest_tldr(cat, b2=b2, agent=agent)
        time.sleep(1)
    