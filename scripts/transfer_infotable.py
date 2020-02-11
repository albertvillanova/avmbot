"""
https://ca.wikipedia.org/wiki/Viquip%C3%A8dia:Consultes_de_manteniment/Wikidata #Paràmetres manuals d'Infotaules a traspassar a WD

https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona/%C3%BAs


%run scripts/transfer_infotable.py --debug
%run scripts/transfer_infotable.py --debug  --log logs/transfer_infotable-01.log

TEST:
%run scripts/harvest_template.py -lang:ca -family:wikipedia -cat:"Articles amb càrrecs manuals i P39" -template:"Infotaula persona" -namespace:0 carrec P39

"""
import argparse
import logging
import re

import pywikibot as pw
from pywikibot import pagegenerators as pg
from wikidatabot.models import Claim, Statement, Item


logger = logging.getLogger("transfer_infotable")


CA_SITE = pw.Site('ca', 'wikipedia')
EN_SITE = pw.Site('en', 'wikipedia')
ES_SITE = pw.Site('es', 'wikipedia')
GL_SITE = pw.Site('gl', 'wikipedia')

# Constants
POSITION_HELD = 'P39'
# Qualifiers
START_TIME = 'P580'
END_TIME = 'P582'
REPLACES = 'P1365'
REPLACED_BY = 'P1366'
#
COAT_OF_ARMS_IMAGE = 'P94'
#
ELECTED_IN = 'P2715'
ELECTORAL_DISTRICT = 'P768'
PARLIAMENTARY_TERM = 'P2937'
PARLIAMENTARY_GROUP = 'P4100'
APPOINTED_BY = 'P748'
#
CABINET = 'P5054'
#
SERIES_ORDINAL = 'P1545'
CONFERRED_BY = 'P1027'
OF = 'P642'
TOGETHER_WITH = 'P1706'
END_CAUSE = 'P1534'
#
DIOCESE = 'P708'
# Resources
IMPORTED_FROM_WIKIMEDIA_PROJECT = 'P143'
CATALAN_WIKIPEDIA = 'Q199693'

OFFICE_HELD_BY_HEAD_OF_GOVERNMENT = 'P1313'
OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION = 'P2388'
# Congress of Deputies
MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN = 'Q18171345'
# Parliament of Catalonia
MEMBER_OF_PARLIAMENT_OF_CATALONIA = 'Q18714088'
PRESIDENT_OF_PARLIAMENT_OF_CATALONIA = 'Q26000995'
# Senate
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'
#
MINISTER_OF_THE_NAVY_OF_SPAIN = 'Q15895305'

INFOTABLE_PARAMS = {
    'carrec': POSITION_HELD,
    'escut_carrec': COAT_OF_ARMS_IMAGE,
    'inici': START_TIME,
    'final': END_TIME,
    'predecessor': REPLACES,
    'successor': REPLACED_BY,
    'k_etiqueta': None,
    'k_nom': None,
}

LINK_REGEX = re.compile(r'\[\[(?P<link>[^\]|[<>{}]*)(?:\|(?P<text>.*?))?\]\]')

POSITION_MAPPING = {

}


TO_MONTH_NUMBER = {
    'gener': 1, 'febrer': 2, 'març': 3, 'abril': 4, 'maig': 5, 'juny': 6, 'juliol': 7, 'agost': 8, 'setembre': 9,
    'octubre': 10, 'novembre': 11, 'desembre': 12
}


def parse_args():
    parser = argparse.ArgumentParser(description="Transfer infotable")
    parser.add_argument('--log', default='')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


def config_logger(log_filename='', debug=False):
    # Set logging level
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(ch)
    if log_filename:
        # Create file handler
        fh = logging.FileHandler(filename=log_filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def create_generator(category='Categoria:Articles amb càrrecs manuals i P39', groupsize=50):  # lang='ca', family='wikipedia',
    site = CA_SITE
    cat = pw.Category(site, category)
    pages = cat.articles()
    return pg.PreloadingGenerator(pages, groupsize=groupsize)


def parse_infotable(page, infotable="Infotaula persona"):
    def get_redirects(title):
        temp = pw.Page(CA_SITE, title, ns=10)
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(with_ns=False).lower()
                  for page in temp.getReferences(filter_redirects=True, namespaces=[10], follow_redirects=False)]
        titles.append(temp.title(with_ns=False).lower())
        return titles
    infotable = infotable.replace('_', ' ')
    infotables = get_redirects(infotable)
    templates = pw.textlib.extract_templates_and_params(page.text, True, True)
    for template_name, template_params in templates:
        if template_name.lower() in infotables:
            return template_params
    # else:
    #     return templates


def extract_positions(template_params):
    positions = []
    position = {}
    for param_name, param_value in template_params.items():
        param_name = param_name if param_name[-1].isalpha() else param_name[:-1]
        if param_name == 'carrec':
            if position:
                positions.append(position)
            position = {param_name: param_value}
        elif param_name in INFOTABLE_PARAMS:
            position[param_name] = param_value
        else:
            if position:
                positions.append(position)
            position = {}
    return positions


def get_item_from_page_link(link):
    logger.info(f"Get item from page link {link}")
    try:
        item = pw.ItemPage.fromPage(pw.Page(pw.Link(link, source=CA_SITE)))
        logger.info(f"Found Wikidata item from ca page link: {item}")
    except pw.NoPage:
        logger.warning(f"No Wikidata item from ca page link: {link}")
        try:
            item = pw.ItemPage.fromPage(pw.Page(pw.Link(link, source=ES_SITE)))
            logger.info(f"Found Wikidata item from es page link: {item}")
        except pw.NoPage:
            logger.warning(f"No Wikidata item from es page link: {link}")
            try:
                item = pw.ItemPage.fromPage(pw.Page(pw.Link(link, source=GL_SITE)))
                logger.info(f"Found Wikidata item from gl page link: {item}")
            except pw.NoPage:
                logger.warning(f"No Wikidata item from gl page link: {link}")
                try:
                    item = pw.ItemPage.fromPage(pw.Page(pw.Link(link, source=EN_SITE)))
                    logger.info(f"Found Wikidata item from en page link: {item}")
                except pw.NoPage:
                    logger.error(f"No Wikidata item from (ca, es, gl, en) page links: {link}")
                    return
    return item


def get_office_held_by_head_from_link(link):
    logger.info(f"Get office held by head from link {link}")
    if not link:
        logger.error(f"No link")
        return
    if link.lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page_link(link)
    office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_GOVERNMENT)
    if not office_claims:
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION)
    if office_claims:
        if len(office_claims) == 1:
            position_item = office_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one office held by head found for item {organization_item}")
            return
    else:
        logger.error(f"No office held by head found for item {organization_item}")
        return
    return position_item


def parse_date(value):
    logger.info(f"Parse date")
    matches = LINK_REGEX.findall(value)
    if not matches:
        logger.error(f"Failed parsing as date: {value}")
        return
    if len(matches) == 1:
        year = int(matches[0][0])
        claim_value = {'year': year}
    elif len(matches) == 2:
        year = int(matches[1][0])
        if " de " in matches[0][0]:
            day, month = matches[0][0].split(" de ")
        elif " d'" in matches[0][0]:
            day, month = matches[0][0].split(" d'")
        day = int(day)
        month = int(TO_MONTH_NUMBER[month])
        claim_value = {'year': year, 'month': month, 'day': day}
    else:
        logger.error(f"Unforeseen date case for value: {value}")
        return
    return claim_value


def parse_list_link(link, word):
    logger.info(f"Parse list link {link}, using word {word}")
    pattern = r".+" + word + r"\w+ (?:de |d')(.+)"
    match = re.match(pattern, link)
    if not match:
        logger.error(f"Failed parsing list link {link}, using word {word}")
        return
    result = match.group(1)
    logger.info(f"Parsed list link result: {result}")
    return result


def parse_position_value(position_value):
    logger.info(f"Parse position value: {position_value}")
    position_item = None
    matches = LINK_REGEX.findall(position_value)
    position_link = matches[0][0]
    position_text = matches[0][1]
    if not position_text:
        position_text = position_value.replace('[[', '').replace(']]', '')
    if position_text.lower().startswith("alcalde"):
        if position_link.lower().startswith("alcalde"):
            position_item = get_item_from_page_link(position_link)
        else:
            position_item = get_office_held_by_head_from_link(position_link)
    elif position_text.lower().startswith("diputa"):
        # TODO
        if position_link == "Parlament de Catalunya":
            position_item = MEMBER_OF_PARLIAMENT_OF_CATALONIA
    elif position_text.lower().startswith("ministr"):
        if position_link.lower().startswith("ministr"):
            position_item = get_item_from_page_link(position_link)
        # elif position_link == "Ministeri de Marina d'Espanya":
        #     position_item = MINISTER_OF_THE_NAVY_OF_SPAIN
        else:
            position_item = get_office_held_by_head_from_link(position_link)
    elif position_text.lower().startswith("president"):
        if position_link.lower().startswith("president"):
            position_item = get_item_from_page_link(position_link)
        else:
            if position_link.lower().startswith("llista"):
                position_link = parse_list_link(position_link, "president")
            position_item = get_office_held_by_head_from_link(position_link)
    elif position_text.lower().startswith("senador"):
        if position_link == "Senat d'Espanya":
            position_item = MEMBER_OF_THE_SENATE_OF_SPAIN
    if not position_item:
        logger.error(f"Failed parsing position value: {position_link}, {position_text}")
    position_claim = Claim(property=POSITION_HELD, item=position_item) if position_item else None
    if position_claim:
        logger.info(f"Position held claim: {position_claim.value}")
    # Eventual qualifiers in position value
    qualifiers = []
    if len(matches) == 2:
        if 'designa' in position_value:
            logger.info(f"Parse appointed by")
            appointed_by_link = matches[1][0]
            appointed_by_item = get_item_from_page_link(appointed_by_link)
            # appointed_by_item = None
            # try:
            #     appointed_by_item = pw.ItemPage.fromPage(pw.Page(pw.Link(appointed_by_link, source=CA_SITE)))
            #     logger.info(f"Found Wikidata item from ca page")
            # except pw.NoPage:
            #     logger.warning(f"No Wikidata item from ca page: {appointed_by_link}")
            #     # TODO
            #     try:
            #         appointed_by_item = pw.ItemPage.fromPage(pw.Page(pw.Link(appointed_by_link, source=ES_SITE)))
            #         logger.info(f"Found Wikidata item from es page")
            #     except pw.NoPage:
            #         logger.error(f"No Wikidata item from ca and es pages: {appointed_by_link}")
            if appointed_by_item:
                appointed_by_claim = Claim(property=APPOINTED_BY, item=appointed_by_item)
                logger.info(f"Appointed by claim: {appointed_by_claim.value}")
                qualifiers.append(appointed_by_claim)
    return position_claim, qualifiers


def parse_position_qualifier(key, value):
    logger.info(f"Parse position qualifier: {key}: {value}")
    claim_value = None
    if key == 'escut_carrec':
        # Ignore it: this should be in the position item
        return
    elif key == 'inici' or key == 'final':
        # Date
        claim_value = parse_date(value)
        # logger.info(f"Parse as date")
        # matches = LINK_REGEX.findall(value)
        # if len(matches) == 1:
        #     year = int(matches[0][0])
        #     claim_value = {'year': year}
        # elif len(matches) == 2:
        #     year = int(matches[1][0])
        #     if " de " in matches[0][0]:
        #         day, month = matches[0][0].split(" de ")
        #     elif " d'" in matches[0][0]:
        #         day, month = matches[0][0].split(" d'")
        #     day = int(day)
        #     month = int(TO_MONTH_NUMBER[month])
        #     claim_value = {'year': year, 'month': month, 'day': day}
        # else:
        #     logger.error(f"Unforeseen date case for position qualifier: {key}: {value}")
    elif key == 'predecessor' or key == 'successor':
        # Item
        logger.info(f"Parse as item")
        matches = LINK_REGEX.findall(value)
        if not matches:  # No matches: -
            logger.error(f"Failed parsing as item: {value}")
        else:
            claim_link = matches[0][0]
            claim_item = get_item_from_page_link(claim_link)
            if claim_item:
                claim_value = {'item': claim_item}
    else:
        logger.error(f"Unforeseen case for position qualifier: {key}: {value}")
    if claim_value:
        logger.info(f"Found claim value {claim_value} for position qualifier: {key}: {value}")
    else:
        logger.error(f"No claim value found for position qualifier: {key}: {value}")
        return
    qualifier_claim = Claim(property=INFOTABLE_PARAMS[key], **claim_value)
    # logger.info(f"Qualifier claim: property {qualifier_claim.property}, value {qualifier_claim.value}")
    return qualifier_claim


def parse_position(position):
    logger.info(f"Parse position: {position}")
    position_claim, qualifiers = parse_position_value(position['carrec'])
    for position_key, position_value in position.items():
        # carrec
        if position_key == 'carrec':
            continue
        elif position_key == 'k_etiqueta':
            if 'k_nom' not in position:
                logger.warning(f"")
                continue
            # TODO
        elif position_key == 'k_nom':
            if 'k_etiqueta' not in position:
                logger.warning(f"")
            continue
        elif position_key in INFOTABLE_PARAMS:
            # TODO: parse position_value
            qualifier_claim = parse_position_qualifier(position_key, position_value)
            if qualifier_claim:
                qualifiers.append(qualifier_claim)
    return position_claim, qualifiers


def create_position_claims(positions):
    claims = []
    for position in positions:
        position_claim, qualifiers = parse_position(position)
        # for position_param, position_value in position.items():
        #     # carrec
        #     if position_param == 'carrec':
        #         position_claim, qualifiers = parse_position_value(position_value)
        #     else:
        #         qualifier = parse_position_qualifier(position_param, position_value)
        #         if qualifier:
        #             qualifiers.append(qualifier)
        claims.append((position_claim, qualifiers))
    return claims


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    # Configurate logger
    config_logger(log_filename=args.log, debug=args.debug)
    logger.info("START transfer_infotable")

    # Generator
    generator = create_generator(groupsize=1)  # TODO: remove groupsize in prod
    for i, page in enumerate(generator):
        logger.info(f"Page: {page}")
        infotable_params = parse_infotable(page)
        logger.info(f"Infotable parameters: {infotable_params}")
        positions = extract_positions(infotable_params)
        logger.info(f"Positions: {positions}")
        position_claims = create_position_claims(positions)

        # DEBUG
        if args.debug:
            # import pdb;pdb.set_trace()
            if i >= 49:
                break