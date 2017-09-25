#!/usr/bin/env python
"""Convert between HearthStone Collection Tracker and  HearthCollect backup formats.
HS Collection Tracker can be found https://freezard.github.io/hs-collection-tracker/
Hearthcollect can be found https://play.google.com/store/apps/details?id=at.xsphere.hearthcollect
For card data conversion HeartHstoneJson hearthstonejson.com is used.
Usage:
    convert.py (to_ht|to_hc) [-i infile] [-t template] [-o outfile]

Options:
    -i <file> specify input file    [default: HS_Collection_Tracker.json]
    -o <file> specify output file    [default: out.json]
    -t <file> specify template file    [default: HearthCollectData.json]
"""
import codecs
import json
import logging
import os
import sys
from collections import OrderedDict

from ht import ht_struct

import requests
from docopt import docopt

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_ht_file(filename, cards_data):
    # This file has one row.
    result = {}
    count = 0
    with codecs.open(filename, 'r', 'utf-8-sig') as f:
        for line in f:
            line_data = json.loads(line)
            for k in iter(line_data):
                cards = line_data[k]['cards']
                for l in iter(cards):
                    for m in (cards[l]):
                        card = cards[l][m]
                        if card['normal'] or card['golden']:
                            cards_data_record = None
                            for card_data in cards_data:
                                if cards_data[card_data]['name'] == m:
                                    cards_data_record = cards_data[card_data]
                                    break
                            if not cards_data_record:
                                print("This class does not fit.")
                                print(card)
                                print(m)
                            result[cards_data_record['id']] = (card['normal'], card['golden'])
                            count += card['golden']
                            count += card['normal']
        logger.info("Input parsed. You have %s cards." % count)
        return result


def parse_hc_file(filename, cards_data):
    with codecs.open(filename, 'r', 'utf-8-sig') as f:
        hc_content = json.loads(f.read())
    for card in hc_content['cards']:
        if card['europe_normal'] or card['europe_golden']:
            cards_data[card['id']]['normal'] += card['europe_normal']
            cards_data[card['id']]['gold'] += card['europe_golden']
    return cards_data


def write_ht_file(filename, cards_data):
    def should_add(item):
        if item['class'] == 'deathknight':
            return False
        return True

    result = ht_struct
    for item in cards_data.values():
        if should_add(item):
            result[item['class']]['cards'][item['rarity']][item['name']] = {
                "name": item['name'],
                "rarity": item["rarity"],
                "mana": item["cost"],
                "type": item["type"],
                "className": item["class"],
                "set": "basic",
                "uncraftable": 'both' if item['rarity'] == 'free' else 'none',
                "normal": item['normal'],
                "golden": item['gold']
        }
    with open(filename, 'w') as f:
        f.write(json.dumps(result))
    logger.info("Output written to: %s" % filename)


def write_hc_file(filename, data, template):
    """
    datastructure = {
        "version": 2,
        "cards": []
    }
    """
    for card in template['cards']:
        if card['id'] in data:
            card["europe_normal"] = data[card['id']][0]
            card["europe_golden"] = data[card['id']][1]
        # print(card)
        """
        for card in data:
        template[]
            addthis = {
                "id": card[0],
                "europe_normal": card[1],
                "europe_golden": card[2],
            }
        """
    with open(filename, 'w') as f:
        f.write(json.dumps(template))
    logger.info("Output written to: %s" % filename)


def load_template(template_file):
    try:
        with open(template_file) as f:
            data = json.loads(f.read(), object_pairs_hook=OrderedDict)
            logger.info("Template loaded from: %s" % template_file)
            return data
    except IOError as e:
        logger.error(e)
        return {}


def load_hsjson():

    def fix_data(data):
        if data['id'] == 'ICC_833t':
            data['rarity'] = 'free'

    local_filename = "cards.json"
    hsjson_url = "https://api.hearthstonejson.com/v1/latest/enUS/cards.json"
    if not os.path.isfile(local_filename):
        logger.info("HSJson cards.json not found, fetching...")
        r = requests.get(hsjson_url, stream=True)
        with open(local_filename, 'wb') as f:
            for block in r.iter_content(1024):
                f.write(block)

    with open(local_filename) as f:
        counter = 0
        cards = {}
        for line in f:
            line_data = json.loads(line)
            for k in line_data:
                fix_data(k)
                if 'name' in k and 'rarity' in k and 'cost' in k:
                    counter += 1
                    cards[k['id']] = {
                        'id': k['id'],
                        'name': k['name'],
                        'rarity': k["rarity"].lower(),
                        'cost': k['cost'],
                        'type': k['type'].lower(),
                        'class': k['playerClass'].lower(),
                        'set': k['set'].lower(),
                        'gold': 0,
                        'normal': 0
                    }
        logger.info("%s cards loaded from HSJson." % counter)
        return cards


def main(args):
    cards = load_hsjson()
    if args['to_hc']:
        data = parse_ht_file(args.get('-i'), cards)
        template = load_template(args.get('-t'))
        write_hc_file(args.get('-o'), data, template)
    elif args['to_ht']:
        data = parse_hc_file(args.get('-i'), cards)
        write_ht_file(args.get('-o'),data)


if __name__ == "__main__":
    args = docopt(__doc__)
    main(args)
