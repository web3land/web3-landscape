#!/usr/bin/python3

import argparse
import os
import shutil
from typing import Dict
import ruamel.yaml
import requests
from bs4 import BeautifulSoup
from enum import Enum

LANDSCAPE_FILE = 'landscape.yml'

def prepate_item(name, project_url, repo_url, logo_path):
    item = dict([('item', None), ('name', name), ('homepage_url', project_url), ('logo', logo_path)])
    if repo_url:
        item['repo_url'] = repo_url
    
    return item


def edit_yaml(landscape, category, subcategory, item, action):
    spot = None
    for _category in landscape:
        if _category['name'].lower() == category.lower():
            for _subcategory in _category['subcategories']:
                if _subcategory['name'].lower() == subcategory.lower():
                    spot = _subcategory
                    break

    if not spot:
        raise Exception("invalid place")

    if action == Action.delete:
        spot['items'].remove(item)
    elif action == Action.add:
        if not spot['items']:
            spot['items'] = [item]
        else:
            spot['items'].append(item)

    return landscape



def add_icon(action, category, subcategory, name, project_url, repo_url, logo_path):
    yaml = ruamel.yaml.YAML()
    with open(LANDSCAPE_FILE) as f:
        data = yaml.load(f)

    landscape = data['landscape']
    if not subcategory:
        subcategory = category

    item = prepate_item(name, project_url, repo_url, logo_path)
    landscape = edit_yaml(landscape, category, subcategory, item, action)

    with open(LANDSCAPE_FILE, 'w') as f:
        yaml.dump(data, f)


def fetch_logo(name, url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    favicon = [i for i in soup.find_all("link") if "icon" in i.get("rel") ]
    if not favicon:
        raise Exception("could not infer favicon from page, please provide a svg")
    
    favicon = favicon[0].get("href")
    if not favicon.startswith('https://'):
        favicon = url.replace('www.', '') + favicon
    
    data = requests.get(favicon).content


    tmp_file = '/tmp/favicon'
    with open(tmp_file, 'wb') as f:
        f.write(data)

    os.system(f'mogrify -format svg {tmp_file}')
    shutil.move(f'{tmp_file}.svg', f'hosted_logos/{name}.svg')
    os.unlink(tmp_file)

    return f'{name}.svg'


def complete_args(args):
    if not args['project_url']:
        args['project_url'] = f'https://www.{args["name"]}.com'
    
    if not args['logo'] and args['action'] != Action.delete:
        args['logo'] = fetch_logo(args['name'], args['project_url'])

    return args

class Action(Enum):
    add = "add"
    delete = "delete"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", dest="action", type=Action, choices=list(Action), help="action to be applied on landscape", required=True)
    parser.add_argument("--category", dest="category", help="category of new item", required=True)
    parser.add_argument("--subcategory", dest="subcategory", help="subcategory of new item", default='', required=False)
    parser.add_argument("--name", dest="name", help="name of new item", required=True)
    parser.add_argument("--project-url", dest="project_url", help="project url of new item", default='', required=False)
    parser.add_argument("--repo-url", dest="repo_url", help="repo url of new item", default='', required=False)
    parser.add_argument("--logo-path", dest="logo", help="logo path of new item", default='', required=False)
    args = vars(parser.parse_args())

    args = complete_args(args)
    add_icon(args['action'], args['category'], args['subcategory'], args['name'], args['project_url'], args['repo_url'], args['logo'])

if __name__ == "__main__":
    main()
