"""Create a markdown summary of an article"""
import json
import os, os.path as op

from crawl import get_past_sunday

def article_md(article, keywords="", tldr=""):
    return "\n".join([
        '<details>',
        f'<summary><b>{article["title"]}</b></summary>',
        '',
        f'**Authors**: {", ".join(article["authors"])}',
        '',
    ] 
    + ([] if not keywords else [f'**Keywords**: {keywords}',''])
    + ([] if not tldr else [f'**TL;DR**: {tldr}', ''])
    + [f'**Link**: [arXiv](https://arxiv.org/abs/{article["id"]})','']
    + [
        '#### Abstract:',
        f'{article["abstract"]}',
        '',
        '</details>'
    ])

def make_summary(
    category="astro-ph.CO",
    output_dir="data"
):
    catname = category.replace(".", "_")
    latest_file = f"{output_dir}/metadata/{catname}/latest.json"
    with open(latest_file, "r") as f:
        articles = json.load(f)
    curr = get_past_sunday(1)
    past = get_past_sunday(2)
    curr_uri = f"tldr/{catname}/{curr.strftime('%Y-%m-%d')}.json"
    past_uri = f"tldr/{catname}/{past.strftime('%Y-%m-%d')}.json"
    curr_file = f"{output_dir}/{curr_uri}"
    past_file = f"{output_dir}/{past_uri}"
    tldrs = []
    for fname in [curr_file, past_file]:
        if op.exists(fname):
            with open(fname, "r") as f:
                tldrs += json.load(f)

    ofile = f"{output_dir}/latest.md"
    with open(ofile, "w") as f:
        f.write("---\n")
        f.write("title: {{ date | date('YYYY-MM-DD') }} " + f"{category}\n")
        f.write(f"labels: {category}, daily\n")
        f.write("---\n\n")

        for article in articles:
            tldr = [tldr['tldr'] for tldr in tldrs if tldr['id'] == article['id']]
            if tldr: tldr = tldr[0]

            # minor clean-ups
            article['abstract'] = article['abstract'].replace("\n", " ")

            f.write(article_md(article, tldr=tldr))

if __name__ == "__main__":
    make_summary()