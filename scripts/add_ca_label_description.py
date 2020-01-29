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
from pywikibot.exceptions import OtherPageSaveError

import wikidatabot
from wikidatabot.models import Item


logger = logging.getLogger('add_ca_label_description')


INSTANCE_OF = 'P31'
COMMUNE_NOUVELLE = 'Q2989454'
START_TIME = 'P580'
END_TIME = 'P582'

REPLACES = 'P1365'

LOCATED_IN = 'P131'
DEPARTMENT_OF_FRANCE = 'Q6465'
TNCC = {
    'Ain': 5, 'Aisne': 5, 'Allier': 5, 'Alpes-de-Haute-Provence': 4, 'Hautes-Alpes': 4, 'Alpes-Maritimes': 4,
    'Ardèche': 5, 'Ardennes': 4, 'Ariège': 5, 'Aube': 5, 'Aude': 5, 'Aveyron': 5, 'Bouches-du-Rhône': 4, 'Calvados': 2,
    'Cantal': 2, 'Charente': 3, 'Charente-Maritime': 3, 'Cher': 2, 'Corrèze': 3, "Côte-d'Or": 3, "Côtes-d'Armor": 4,
    'Creuse': 3, 'Dordogne': 3, 'Doubs': 2, 'Drôme': 3, 'Eure': 5, 'Eure-et-Loir': 1, 'Finistère': 2, 'Corse-du-Sud': 3,
    'Haute-Corse': 3, 'Gard': 2, 'Haute-Garonne': 3, 'Gers': 2, 'Gironde': 3, 'Hérault': 5, 'Ille-et-Vilaine': 1,
    'Indre': 5, 'Indre-et-Loire': 1, 'Isère': 5, 'Jura': 2, 'Landes': 4, 'Loir-et-Cher': 2, 'Loire': 3,
    'Haute-Loire': 3, 'Loire-Atlantique': 3, 'Loiret': 2, 'Lot': 2, 'Lot-et-Garonne': 2, 'Lozère': 3,
    'Maine-et-Loire': 2, 'Manche': 3, 'Marne': 3, 'Haute-Marne': 3, 'Mayenne': 3, 'Meurthe-et-Moselle': 0, 'Meuse': 3,
    'Morbihan': 2, 'Moselle': 3, 'Nièvre': 3, 'Nord': 2, 'Oise': 5, 'Orne': 5, 'Pas-de-Calais': 2, 'Puy-de-Dôme': 2,
    'Pyrénées-Atlantiques': 4, 'Hautes-Pyrénées': 4, 'Pyrénées-Orientales': 4, 'Bas-Rhin': 2, 'Haut-Rhin': 2,
    'Rhône': 2, 'Haute-Saône': 3, 'Saône-et-Loire': 0, 'Sarthe': 3, 'Savoie': 3, 'Haute-Savoie': 3, 'Paris': 0,
    'Seine-Maritime': 3, 'Seine-et-Marne': 0, 'Yvelines': 4, 'Deux-Sèvres': 4, 'Somme': 3, 'Tarn': 2,
    'Tarn-et-Garonne': 2, 'Var': 2, 'Vaucluse': 2, 'Vendée': 3, 'Vienne': 3, 'Haute-Vienne': 3, 'Vosges': 4, 'Yonne': 5,
    'Territoire de Belfort': 2, 'Essonne': 5, 'Hauts-de-Seine': 4, 'Seine-Saint-Denis': 3, 'Val-de-Marne': 2,
    "Val-d'Oise": 2, 'Guadeloupe': 3, 'Martinique': 3, 'Guyane': 3, 'La Réunion': 0, 'Mayotte': 0}
TNCC_CA = {**TNCC, **{
    'Ardennes': 7, 'Bouches-du-Rhône': 7, 'Calvados': 0, 'Cantal': 0, 'Charente': 2, 'Charente-Maritime': 2,
    "Côtes-d'Armor": 7, 'Finistère': 0, 'Corse-du-Sud': 0, 'Haute-Corse': 5, 'Haute-Garonne': 5, 'Isère': 3,
    'Landes': 7, 'Loir-et-Cher': 0, 'Loire': 2, 'Haute-Loire': 5, 'Loire-Atlantique': 2, 'Lot': 5, 'Lot-et-Garonne': 1,
    'Lozère': 2, 'Maine-et-Loire': 0, 'Marne': 2, 'Haute-Marne': 5, 'Mayenne': 2, 'Meuse': 2, 'Morbihan': 1,
    'Moselle': 2, 'Nièvre': 2, 'Haut-Rhin': 5, 'Haute-Saône': 5, 'Sarthe': 2, 'Haute-Savoie': 5, 'Seine-Maritime': 2,
    'Yvelines': 1, 'Deux-Sèvres': 0, 'Somme': 2, 'Tarn-et-Garonne': 0, 'Vaucluse': 0, 'Haute-Vienne': 5, 'Yonne': 2,
    'Seine-Saint-Denis': 0, 'Val-de-Marne': 3, "Val-d'Oise": 3, 'Guadeloupe': 0, 'La Réunion': 5,
}}

DE = {0: "de ",
      1: "d'",
      2: "del ",
      3: "de la ",
      4: "dels ",
      5: "de l'",
      6: "dels ",
      7: "de les ",
      8: "dels "}

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


def update_label_description(item, data, summary_what):
    summary = " and ".join(summary_what)
    summary = f"Update ca {summary}"
    try:
        logger.info(summary)
        item.editEntity(data, summary=summary)
    except OtherPageSaveError:
        logger.warning(f"Exception while updating item {item.id}")
        location = item
        instance_of = item.claims[INSTANCE_OF][0].target.id
        iteration = 0
        while instance_of != DEPARTMENT_OF_FRANCE and iteration < 5:
            iteration += 1
            location = location.claims[LOCATED_IN][0].target
            _ = location.get()
            instance_of = location.claims[INSTANCE_OF][0].target.id
        if instance_of != DEPARTMENT_OF_FRANCE:
            raise OtherPageSaveError
        location_ca_label = location.labels.get('ca')
        location_fr_label = location.labels.get('fr')
        ca_description = data['descriptions']['ca'] if 'descriptions' in data else item.descriptions.get('ca')
        ca_description += f" al departament {DE[TNCC_CA[location_fr_label]]}{location_ca_label}"
        logger.warning(f"Retry updating with new description: {ca_description}")
        ca_description = {'ca': ca_description}
        data['descriptions'] = ca_description
        summary_what = set(summary_what + ['description'])
        summary = " and ".join(set(summary_what))
        summary = f"Update ca {summary}"
        logger.info(summary)
        item.editEntity(data, summary=summary)


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
    _ = pwb_item.get()
    logger.info(f"Replaced item: {pwb_item.getID()}")
    data = {}
    summary_what = []

    # Label
    ca_label = pwb_item.labels.get('ca')
    if not ca_label:
        fr_label = pwb_item.labels.get('fr')
        if fr_label:
            ca_label = {'ca': fr_label}
            data['labels'] = ca_label
            summary_what.append('label')
        else:
            logger.error(f"No fr label for item {pwb_item.id}")
    else:
        logger.info(f"ca label already present for item {pwb_item.id}: {ca_label}")

    # Description
    ca_description = pwb_item.descriptions.get('ca')
    if not ca_description:
        ca_description = {'ca': 'antic municipi francès'}
        data['descriptions'] = ca_description
        summary_what.append('description')
    else:
        if ca_description.startswith('municipi'):
            if len(ca_description) > 16:
                logger.warning(f"ca description longer than expected for item {pwb_item.id}: {ca_description}")
            ca_description = {'ca': f'antic {ca_description}'}
            data['descriptions'] = ca_description
            summary_what.append('description')
        elif ca_description.startswith('antic'):
            logger.info(f"ca description already updated for item {pwb_item.id}: {ca_description}")
        else:
            logger.error(f"ca description different than expected for item {pwb_item.id}: {ca_description}")
    fr_description = pwb_item.descriptions.get('fr')
    if not fr_description:
        logger.warning(f"No fr description for item {pwb_item.id}")
    elif not fr_description.startswith('ancienne'):
        logger.warning(f"fr description does not start with 'ancienne' for item {pwb_item.id}: {fr_description}")

    # Update data
    if data:
        # entity = {'id': item.id}
        # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
        # print(response)
        update_label_description(pwb_item, data, summary_what)


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    # Configurate logger
    config_logger(log_filename=args.log)
    logger.info('START add_ca_label_description')

    # Asof: today
    today = str(datetime.date.today())

    # Query
    query = QUERY.replace('{administrative_division}', args.to).replace('{today}', today)

    # Create item generator
    pwb_items = pg.WikidataSPARQLPageGenerator(query, site=wikidatabot.site)
    # pwb_items = [1]

    for i, pwb_item in enumerate(pwb_items):
        # pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, 'Q764858')
        # pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, 'Q43781672')
        # logger.info(pwb_item)
        pwb_item.get()
        # pwb_item_id = pwb_item.getID()
        logger.info(f"Item: {pwb_item.getID()}")
        item = Item.from_pwb(pwb_item)

        # Update REPLACES municipalities
        update_replaced_municipalities(item)

        data = {}
        summary_what = []
        # Label
        ca_label = item.labels.get('ca')
        if not ca_label:
            fr_label = item.labels.get('fr')
            if fr_label:
                ca_label = {'ca': fr_label}
                data['labels'] = ca_label
                summary_what.append('label')
            else:
                logger.error(f"No fr label for item {item.id}")
        else:
            logger.info(f"ca label already present for item {item.id}: {ca_label}")

        # Description
        ca_description = item.descriptions.get('ca')
        if not ca_description:
            fr_description = item.descriptions.get('fr')
            if not fr_description:
                logger.warning(f"No fr description for item {item.id}")
            elif not fr_description.startswith('commune'):
                logger.warning(f"fr description does not start with 'commune' for item {item.id}: {fr_description}")
            ca_description = {'ca': 'municipi francès'}
            data['descriptions'] = ca_description
            summary_what.append('description')
        else:
            # TODO:
            logger.info(f"ca description already present for item {item.id}: {ca_description}")

        # Update data
        if data:
            # entity = {'id': item.id}
            # response = wikidatabot.repo.editEntity(entity, data, summary=summary)
            # print(response)
            update_label_description(pwb_item, data, summary_what)

        # if i >= 0:
        #     break
    logger.info('END add_ca_label_description')
