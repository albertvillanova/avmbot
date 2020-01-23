"""

python ./scripts/add_ca_label_description.py --log logs/add_ca_label_description.log

python scripts/add_ca_label_description.py | tee log/20190108.log
python scripts/add_ca_label_description.py | tee log/20190108-tmp.log
%run scripts/add_ca_label_description.py
"""
#
# import sys
# # sys.setdefaultencoding() does not exist, here!
# reload(sys)  # Reload does the trick!
# sys.setdefaultencoding('UTF8')
import argparse
import datetime
import logging

from pywikibot import pagegenerators as pg

import wikidatabot
from wikidatabot.models import Item


logger = logging.getLogger('add_ca_label_description')


INSTANCE_OF = 'P31'
COMMUNE_NOUVELLE = 'Q2989454'
START_TIME = 'P580'
END_TIME = 'P582'

REPLACES = 'P1365'

QUERY = ("""
SELECT ?item
WHERE {
    ?item p:{instance_of} ?statement.
    ?statement ps:{instance_of} wd:{commune_nouvelle};
               pq:{start_time} ?date.
    FILTER (YEAR(?date) >= 2019).
}
""".replace('{instance_of}', INSTANCE_OF)
   .replace('{commune_nouvelle}', COMMUNE_NOUVELLE)
   .replace('{start_time}', START_TIME)
)

QUERY = ("""
SELECT DISTINCT ?item
WHERE {
  ?item p:{instance_of} ?st .
  ?st ps:{instance_of} wd:{administrative_division} .

  OPTIONAL{?st pq:{start_time} ?start_time_date}
  FILTER(IF(BOUND(?start_time_date), ?start_time_date <= "{today}"^^xsd:dateTime, true))

  OPTIONAL{?st pq:{end_time} ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), ?end_time_date > "{today}"^^xsd:dateTime, true))
}
""").replace('{instance_of}', INSTANCE_OF)\
    .replace('{start_time}', START_TIME)\
    .replace('{end_time}', END_TIME)


def config_logger(log_filename=''):
    # Set logging level
    logger.setLevel(logging.DEBUG)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if log_filename:
        # Create file handler
        fh = logging.FileHandler(filename=log_filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def parse_args():
    parser = argparse.ArgumentParser(description="Add ca label and description")
    parser.add_argument('-t', '--to', default=COMMUNE_NOUVELLE)
    parser.add_argument('--log', default='')
    return parser.parse_args()


def update_replaced_municipalities(item):
    replaced_statements = item.statements.get(REPLACES)
    if not replaced_statements:
        return
    logger.info("Start update of replaced municipalities")
    for statement in replaced_statements:
        replaced_municipality = statement.target
        update_replaced_municipality(replaced_municipality)
    logger.info("End update of replaced municipalities")


def update_replaced_municipality(pwb_item):
    logger.info(pwb_item)
    _ = pwb_item.get()
    data = {}
    summary_what = []
    # Label
    if 'fr' in pwb_item.labels:
        if 'ca' not in pwb_item.labels:
            ca_label = {'ca': pwb_item.labels['fr']}
            data['labels'] = ca_label
            summary_what.append('label')
        else:
            logger.info(f"ca label already present in {pwb_item.id}")
    else:
        logger.error(f"fr label not in {pwb_item.id}")
    # Description
    if 'fr' in pwb_item.descriptions:
        fr_description = pwb_item.descriptions['fr']
        if len(fr_description) > 8 and fr_description[:8] == 'ancienne':
            if 'ca' in pwb_item.descriptions:
                ca_description = pwb_item.descriptions['ca']
                if len(ca_description) > 8 and ca_description[:8] == 'municipi':
                    if len(ca_description) > 16:
                        logger.info(f"ca description already present in {pwb_item.id} is: {ca_description}")
                    ca_description = {'ca': f'antic {ca_description}'}
                    data['descriptions'] = ca_description
                    summary_what.append('description')
                elif len(ca_description) > 5 and ca_description[:5] == 'antic':
                    logger.info(f"ca description already updated in {pwb_item.id}")
                else:
                    logger.warning(f"ca description already present in {pwb_item.id}: {ca_description}")
            else:
                ca_description = {'ca': 'antic municipi francès'}
                data['descriptions'] = ca_description
                summary_what.append('description')
            # else:
            #     print(f"ca description already present in {pwb_item.id}")
        else:
            logger.error(f"fr description does not contain 'ancienne' in {pwb_item.id}")
    else:
        logger.error(f"fr description not in {pwb_item.id}")
    # Update data
    if data:
        # entity = {'id': item.id}
        summary_what = " and ".join(summary_what)
        summary = f"Update ca {summary_what}"
        # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
        # print(response)
        pwb_item.editEntity(data, summary=summary)
        logger.info(summary)


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    # Configurate logger
    config_logger(log_filename=args.log)
    logger.info('BEGIN')

    # Asof: today
    today = str(datetime.date.today())

    # Query
    query = QUERY.replace('{administrative_division}', args.to).replace('{today}', today)

    # Create item generator
    pwb_items = pg.WikidataSPARQLPageGenerator(query, site=wikidatabot.site)

    for i, pwb_item in enumerate(pwb_items):
        logger.info(pwb_item)
        pwb_item.get()
        logger.info(f"{i + 1}, {pwb_item.labels.get('fr')}")
        # print(municipality.labels['ca'])
        item = Item.from_pwb(pwb_item)
        # Update REPLACES municipalities
        update_replaced_municipalities(item)
        #
        # print(item.labels)
        data = {}
        summary_what = []
        # Label
        if 'fr' in item.labels:
            if 'ca' not in item.labels:
                ca_label = {'ca': item.labels['fr']}
                data['labels'] = ca_label
                summary_what.append('label')
            else:
                logger.info(f"ca label already present in {item.id}")
        else:
            logger.error(f"fr label not in {item.id}")
        # Description
        if 'fr' in item.descriptions:
            if 'ca' not in item.descriptions:
                ca_description = {'ca': 'municipi francès'}
                data['descriptions'] = ca_description
                summary_what.append('description')
            else:
                logger.info(f"ca description already present in {item.id}")
        else:
            logger.error(f"fr description not in {item.id}")
        # Update data
        if data:
            # entity = {'id': item.id}
            summary_what = " and ".join(summary_what)
            summary = f"Add ca {summary_what}"
            # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
            # print(response)
            pwb_item.editEntity(data, summary=summary)
            logger.info(summary)

        # if i >= 1:
        #     break
    logger.info('END')
