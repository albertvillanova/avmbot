"""

python scripts/add_ca_label_description.py | tee log/20190108.log
python scripts/add_ca_label_description.py | tee log/20190108-tmp.log
%run scripts/add_ca_label_description.py
"""
#
# import sys
# # sys.setdefaultencoding() does not exist, here!
# reload(sys)  # Reload does the trick!
# sys.setdefaultencoding('UTF8')
import random
import time

from pywikibot import pagegenerators as pg

import wikidatabot
from wikidatabot.models import Item


INSTANCE_OF = 'P31'
COMMUNE_NOUVELLE = 'Q2989454'
START_TIME = 'P580'

REPLACES = 'P1365'

QUERY = ("""
SELECT ?item 
WHERE {
    ?item p:{instance_of} ?instanceStatement.
    ?instanceStatement ps:{instance_of} wd:{commune_nouvelle};
                       pq:{start_time} ?date.
    FILTER (YEAR(?date) >= 2019).
}
""".replace('{instance_of}', INSTANCE_OF)
   .replace('{commune_nouvelle}', COMMUNE_NOUVELLE)
   .replace('{start_time}', START_TIME)
)


def update_replaced_municipalities(item):
    replaced_statements = item.statements.get(REPLACES)
    if not replaced_statements:
        return
    print("Start update of replaced municipalities")
    for statement in replaced_statements:
        replaced_municipality = statement.target
        update_replaced_municipality(replaced_municipality)
    print("End update of replaced municipalities")


def update_replaced_municipality(pwb_item):
    time.sleep(5 + 10 * random.random())
    print(pwb_item)
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
            print(f"ca label already present in {pwb_item.id}")
    else:
        print(f"fr label not in {pwb_item.id}")
    # Description
    if 'fr' in pwb_item.descriptions:
        fr_description = pwb_item.descriptions['fr']
        if len(fr_description) > 8 and fr_description[:8] == 'ancienne':
            if 'ca' in pwb_item.descriptions:
                ca_description = pwb_item.descriptions['ca']
                if len(ca_description) > 8 and ca_description[:8] == 'municipi':
                    if len(ca_description) > 16:
                        print(f"ca description already present in {pwb_item.id} is: {ca_description}")
                    ca_description = {'ca': f'antic {ca_description}'}
                    data['descriptions'] = ca_description
                    summary_what.append('description')
                elif len(ca_description) > 5 and ca_description[:5] == 'antic':
                    print(f"ca description already updated in {pwb_item.id}")
                else:
                    print(f"ca description already present in {pwb_item.id}: {ca_description}")
            else:
                ca_description = {'ca': 'antic municipi francès'}
                data['descriptions'] = ca_description
                summary_what.append('description')
            # else:
            #     print(f"ca description already present in {pwb_item.id}")
        else:
            print(f"fr description does not contain 'ancienne' in {pwb_item.id}")
    else:
        print(f"fr description not in {pwb_item.id}")
    # Update data
    if data:
        # entity = {'id': item.id}
        summary_what = " and ".join(summary_what)
        summary = f"Update ca {summary_what}"
        # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
        # print(response)
        pwb_item.editEntity(data, summary=summary)
        print(summary)


if __name__ == '__main__':
    print('BEGIN')
    query = QUERY

    # Create item generator
    pwb_items = pg.WikidataSPARQLPageGenerator(query, site=wikidatabot.site)

    for i, pwb_item in enumerate(pwb_items):
        time.sleep(5 + 10 * random.random())
        print(pwb_item)
        pwb_item.get()
        print(i + 1, pwb_item.labels.get('fr'))
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
                print(f"ca label already present in {item.id}")
        else:
            print(f"fr label not in {item.id}")
        # Description
        if 'fr' in item.descriptions:
            if 'ca' not in item.descriptions:
                ca_description = {'ca': 'municipi francès'}
                data['descriptions'] = ca_description
                summary_what.append('description')
            else:
                print(f"ca description already present in {item.id}")
        else:
            print(f"fr description not in {item.id}")
        # Update data
        if data:
            # entity = {'id': item.id}
            summary_what = " and ".join(summary_what)
            summary = f"Add ca {summary_what}"
            # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
            # print(response)
            pwb_item.editEntity(data, summary=summary)
            print(summary)

        # if i >= 1:
        #     break
    print('END')
