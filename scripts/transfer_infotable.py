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
from collections import defaultdict

import pywikibot as pw
from pywikibot import pagegenerators as pg
from wikidatabot.models import Claim, Statement, Item


logger = logging.getLogger("transfer_infotable")


CA_SITE = pw.Site('ca', 'wikipedia')
EN_SITE = pw.Site('en', 'wikipedia')
ES_SITE = pw.Site('es', 'wikipedia')
GL_SITE = pw.Site('gl', 'wikipedia')

# Constants

# Infotable parameters
POSITION_HELD = 'P39'
# Qualifiers
START_TIME = 'P580'
END_TIME = 'P582'
REPLACES = 'P1365'
REPLACED_BY = 'P1366'
#
COAT_OF_ARMS_IMAGE = 'P94'
SEAL_IMAGE = 'P158'
#
ELECTED_IN = 'P2715'
ELECTORAL_DISTRICT = 'P768'
PARLIAMENTARY_TERM = 'P2937'  # not in Infotaula
PARLIAMENTARY_GROUP = 'P4100'  # not in Infotaula
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

# Utils to find position from organization
OFFICE_HELD_BY_HEAD_OF_GOVERNMENT = 'P1313'
OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION = 'P2388'
OFFICE_HELD_BY_HEAD_OF_STATE = 'P1906'
HAS_PART = 'P527'
HAS_PARTS_OF_THE_CLASS = 'P2670'

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
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona/%C3%BAs
    'carrec': POSITION_HELD,
    'escut_carrec': COAT_OF_ARMS_IMAGE,
    'inici': START_TIME,
    'final': END_TIME,
    'predecessor': REPLACES,
    'successor': REPLACED_BY,
    'k_etiqueta': None,
    'k_nom': None,
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona?action=edit
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_de_pol%C3%ADtic/bloc_carrec
    'ordre': SERIES_ORDINAL,
    'junt_a': TOGETHER_WITH,
    'nominat': APPOINTED_BY,
    'designat': APPOINTED_BY,
    'a_etiqueta': None,
    'a_nom': None,
    'b_etiqueta': None,
    'b_nom': None,
    'e_etiqueta': None,
    'e_nom': None,
    'f_etiqueta': None,
    'f_nom': None,
    'l_etiqueta': None,
    'l_nom': None,
}

# Regex
DIGIT_REGEX = re.compile(r"(\d+)")
LINK_REGEX = re.compile(r'\[\[(?P<link>[^\]|[<>{}]*)(?:\|(?P<text>.*?))?\]\]')
ORDINAL_REGEX = re.compile(r"(\d+)[rntéèa]\.? .+")
PREPOSITION_REGEX = re.compile(r"(?: de | d'|\s)")

COUNTRIES = ["Espanya", "França", "Portugal", "Regne_Unit"]
AMBASSADOR_OF_SPAIN_TO_FRANCE = 'Q27969744'
AMBASSADOR_OF_SPAIN_TO_PORTUGAL = 'Q37140063'
AMBASSADOR_OF_SPAIN_TO_THE_UNITED_KINGDOM = 'Q43542408'
AMBASSADOR_OF_TO = {
    ("Espanya", "França"): AMBASSADOR_OF_SPAIN_TO_FRANCE,
    ("Espanya", "Portugal"): AMBASSADOR_OF_SPAIN_TO_PORTUGAL,
    ("Espanya", "Regne_Unit"): AMBASSADOR_OF_SPAIN_TO_THE_UNITED_KINGDOM,
}
SULTAN_OF_MOROCCO = 'Q14566713'

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
        fh = logging.FileHandler(filename=log_filename, encoding='utf-8')
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
    positions = defaultdict(dict)
    for param_name, param_value in template_params.items():
        param_name, *param_num = DIGIT_REGEX.split(param_name)
        param_num = param_num[0] if param_num else '1'
        if param_name in INFOTABLE_PARAMS:
            positions[param_num][param_name] = param_value
    if not positions:
        return []
    positions = [positions[position_num] for position_num in sorted(positions)]
    # Propagate 'carrec'
    for i, position in enumerate(positions):
        if 'carrec' not in position:
            position['carrec'] = positions[i - 1]['carrec']
    return positions


def get_page_from_link(link, langs=None):
    if not langs:
        langs = ['ca', 'es', 'gl', 'en']
    sites = {'ca': CA_SITE, 'es': ES_SITE, 'gl': GL_SITE, 'en': EN_SITE}
    logger.info(f"Get page from page link {link}")
    for lang in langs:
        site = sites[lang]
        page = pw.Page(pw.Link(link, source=site))
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        if page.exists():
            logger.info(f"Found Wikipedia page from {lang} page link {link}: {page}")
            return page
        else:
            logger.warning(f"No Wikipedia page from {lang} page link {link}")
    logger.error(f"No Wikipedia page from (ca, es, gl, en) page links: {link}")


def get_item_from_page(page):
    logger.info(f"Get item from page {page}")
    try:
        item = pw.ItemPage.fromPage(page)
    except pw.NoPage:
        logger.error(f"No Wikidata item from page: {page}")
        return
    logger.info(f"Found Wikidata item from page {page}: {item}")
    return item


def get_item_from_page_link(link, langs=None):
    logger.info(f"Get item from page link {link}")
    page = get_page_from_link(link, langs=langs)
    if not page:
        logger.error(f"No Wikidata item because no Wikipedia page from page link: {link}")
        return
    item = get_item_from_page(page)
    return item


# def get_item(page):
#     logger.info(f"Get item from {page}")
#     if isinstance(page, str):
#         link = page
#         page = get_page_from_link(link)
#     if not page:
#         logger.error(f"No Wikidata item because no Wikipedia page from link: {link}")
#         return
#     item = get_item_from_page(page)
#     return item


def get_office_held_by_head_from_page(page, of=None):
    logger.info(f"Get office held by head from page {page}")
    if not page:
        logger.error(f"No page")
        return
    if page.title().lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page(page)
    if not organization_item:
        logger.error(f"No organization item found from page {page}")
        return
    if of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
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


def get_office_held_by_head_from_link(link, of=None):
    logger.info(f"Get office held by head from link {link}")
    if not link:
        logger.error(f"No link")
        return
    if link.lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page_link(link)
    if not organization_item:
        logger.error(f"No organization item found from link {link}")
        return
    if of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
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


def get_office_held_by_head(organization_page, head_of=None, from_list_of=None, prepend_to_list_of=None):
    logger.info(f"Get office held by head from organization: {organization_page}")
    if not organization_page:
        logger.error(f"No organization: {organization_page}")
        return
    if isinstance(organization_page, str):
        organization_link = organization_page
        organization_page = get_page_from_link(organization_link)
    if not organization_page:
        logger.error(f"No Wikidata item because no Wikipedia page from link: {organization_link}")
        return
    # From list of
    if from_list_of and (organization_page.title().lower().startswith("llista") or
                         organization_page.title().lower().startswith(from_list_of + "s")):
        organization_page = get_organization_page_from_list_link(organization_page.title(), from_list_of,
                                                                 prepend=prepend_to_list_of)
        if not organization_page:
            logger.error(f"No organization page from list link: {organization_link}")
            return
    # Organization item
    organization_item = get_item_from_page(organization_page)
    if not organization_item:
        logger.error(f"No organization item found from organization: {organization_page}")
        return
    if head_of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
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


def get_has_part_from_link(link):
    logger.info(f"Get has part from link {link}")
    if not link:
        logger.error(f"No link")
        return
    if link.lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page_link(link)
    if not organization_item:
        logger.error(f"No organization item found from link {link}")
        return
    part_claims = organization_item.claims.get(HAS_PART)
    if not part_claims:
        part_claims = organization_item.claims.get(HAS_PARTS_OF_THE_CLASS)
    if part_claims:
        if len(part_claims) == 1:
            position_item = part_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one part found for item {organization_item}")
            return
    else:
        logger.error(f"No part found for item {organization_item}")
        return
    return position_item


def parse_date(value):
    logger.info(f"Parse date")
    if value.startswith('{{'):
        date_parts = value.replace('{{', '').replace('}}', '').split('|')
        date_parts = date_parts[1:] if len(date_parts) > 1 else []
    else:
        value = value.replace('[[', '').replace(']]', '')
        date_parts = PREPOSITION_REGEX.split(value)[::-1]
    if len(date_parts) < 1 or len(date_parts) > 3:
        logger.error(f"Failed parsing date: {value}")
        return
    date_parts = [int(part) if part.isdigit() else TO_MONTH_NUMBER[part] for part in date_parts]
    claim_value = {k: v for k, v in zip(['year', 'month', 'day'], date_parts)}
    return claim_value


def get_organization_link_from_list_link(link, word, prepend=None):
    logger.info(f"Get organization link from list link {link}, using word {word}")
    pattern = r".*" + word + r"\w+ (?P<preposition>de la |de |d')(?P<organization>.+)"
    match = re.match(pattern, link, re.I)
    if not match:
        logger.error(f"Failed getting organization link from list link {link}, using word {word}")
        return
    organization_link = match.group('organization')
    if prepend:
        # To cope with: Llista de ministres [(d')(Hisenda)] -> Llista de ministres del [Ministeri (d')(Hisenda)]
        organization_link = f"{prepend} {match.group('preposition')}{organization_link}"
    logger.info(f"Got organization link {organization_link} from list link {link}")
    return organization_link


def get_organization_page_from_list_link(link, word, prepend=None):
    logger.info(f"Get organization page from list link: {link}")
    organization_link = get_organization_link_from_list_link(link, word, prepend=prepend)
    if not organization_link:
        logger.error(f"No organization link from list link: {link}")
        return
    organization_page = get_page_from_link(organization_link)
    if not organization_page:
        logger.error(f"No organization page from organization link: {organization_link}")
        return
    return organization_page


def parse_position_value(position_value):
    logger.info(f"Parse position value: {position_value}")
    position_item = None
    position_claim = None
    qualifiers = []
    # Match links
    matched_links = LINK_REGEX.findall(position_value)
    # From links
    if matched_links:
        position_link = matched_links[0][0].strip()
        position_page = get_page_from_link(position_link)
        position_page_title = position_page.title() if position_page else ''
        position_text = matched_links[0][1].strip()
        if not position_text:
            position_text = position_value
        # No page link
        if not position_page_title:
            position_item = None
        # Page link
        elif position_text.lower().startswith("[["):
            position_item = get_item_from_page(position_page)
        # alcalde
        elif position_text.lower().startswith("alcalde"):
            if position_page_title.lower().startswith("alcalde"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, from_list_of="alcalde")
        # diputa
        elif position_text.lower().startswith("diputa"):
            if position_page_title == "Parlament de Catalunya":
                position_item = MEMBER_OF_PARLIAMENT_OF_CATALONIA
            else:
                position_item = get_has_part_from_link(position_link)
        # governador
        elif position_page_title.lower().startswith("governador"):
            if len(matched_links) == 2:
                state_link = matched_links[1][0].strip()
                position_item = get_office_held_by_head_from_link(state_link)
        # khediv
        elif position_page_title.lower().startswith("khediv") or position_page_title.lower().startswith("kediv"):
                position_item = get_item_from_page(position_page)
        # membre
        elif position_text.lower().startswith("membre"):
            position_item = get_has_part_from_link(position_link)
        # ministr
        elif position_text.lower().startswith("ministr"):
            if position_page_title.lower().startswith("ministr"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, from_list_of="ministr",
                                                        prepend_to_list_of="Ministeri")
        # president
        elif position_text.lower().startswith("president"):
            if position_page_title.lower().startswith("president"):
                position_item = get_item_from_page(position_page)
            else:
                # TODO: of='state'?
                position_item = get_office_held_by_head(position_page, from_list_of="president")
        # # regidor  # TODO: not yet a clearly established structure in Wikidata
        # elif position_text.lower().startswith("regidor"):
        #     position_item = get_has_part_from_link(position_link)
        # rei
        elif position_text.lower().startswith("rei"):
            if position_page_title.lower().startswith("rei") and not \
                    position_page_title.lower().startswith("rei" + "s"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, head_of="state", from_list_of="rei")
        # senador
        elif position_text.lower().startswith("senador"):
            if position_page_title == "Senat d'Espanya":
                position_item = MEMBER_OF_THE_SENATE_OF_SPAIN
        # Position claim
        if not position_item:
            logger.error(f"Failed parsing position value: {position_link}; {position_text}")
        # Eventual qualifiers in position value
        if len(matched_links) == 2:
            if 'designa' in position_value:
                logger.info(f"Parse appointed by")
                appointed_by_link = matched_links[1][0].strip()
                appointed_by_item = get_item_from_page_link(appointed_by_link)
                if appointed_by_item:
                    appointed_by_claim = Claim(property=APPOINTED_BY, item=appointed_by_item)
                    logger.info(f"Appointed by claim: {appointed_by_claim.value}")
                    qualifiers.append(appointed_by_claim)
        if position_text[0].isdigit():
            match = ORDINAL_REGEX.match(position_text)
            if match:
                series_ordinal_quantity = match.group(1)  # must be value=str
                series_ordinal_claim = Claim(property=SERIES_ORDINAL, value=series_ordinal_quantity)
                logger.info(f"Series ordinal claim: {series_ordinal_claim.value}")
                qualifiers.append(series_ordinal_claim)
    # Without links
    else:
        if position_value.lower().startswith("alcalde"):
            regex = "alcalde" + r"\S*\s(?:de |d')(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'))
        elif position_value.lower().startswith("president"):
            regex = "president" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                organization = match.group('organization')
                if organization == "Malta":
                    organization = "República de Malta"
                position_item = get_office_held_by_head_from_link(organization, of='state')
        elif position_value.lower().startswith("primer ministr") or \
                position_value.lower().startswith("primera ministr"):
            regex = "primera? ministr" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'))
        elif position_value.lower().startswith("rei"):
            regex = "rei" + r"\S*\s(?:de |d')(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'), of='state')
        elif position_value.lower().startswith("ambaixador"):
            # Join multi-word countries
            position_value = position_value.replace("Regne Unit", "Regne_Unit")
            words = re.split(r"[\s']", position_value)
            of_to = tuple(word for word in words if word in COUNTRIES)
            if len(of_to) != 2:
                logger.error(f"Failed parsing 'ambaixador': not a pair of countries found {of_to}")
            else:
                if of_to not in AMBASSADOR_OF_TO:
                    logger.error(f"Missing ambassador of_to {of_to}")
                else:
                    position_item = AMBASSADOR_OF_TO.get(of_to)
        elif position_value.lower().startswith("soldà"):
            regex = "soldà" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                organization = match.group('organization')
                if organization == "Marroc":
                    position_item = SULTAN_OF_MOROCCO
        if not position_item:
            logger.error(f"Failed parsing position value: {position_value}")
    if position_item:
        position_claim = Claim(property=POSITION_HELD, item=position_item)
        logger.info(f"Position held claim: {position_claim.value}")
    return position_claim, qualifiers


def parse_position_qualifier(key, value):
    logger.info(f"Parse position qualifier: {key}: {value}")
    claim_value = None
    # Equivalences
    if key.lower() == "proclamació":
        key = "inici"
    # Cases
    if key == 'escut_carrec':
        # Ignore it: this should be in the position item
        logger.warning(f"Skipped position qualifier because of key 'escut_carrec': value: {value}")
        return 'CONTINUE'
    elif key == 'inici' or key == 'final':
        if value == "present":
            # Ignore it: this is uninformative
            logger.warning(f"Skipped position qualifier because of value 'present': key: {key}")
            return 'CONTINUE'
        # Date
        claim_value = parse_date(value)
    elif key == 'predecessor' or key == 'successor':
        if value == "-":
            # Ignore it: this is uninformative
            logger.warning(f"Skipped position qualifier because of value '-': key: {key}")
            return 'CONTINUE'
        # Item
        logger.info(f"Parse as item")
        matches = LINK_REGEX.findall(value)
        if not matches:
            logger.error(f"Failed parsing as item: {value}")
            return
        else:
            claim_link = matches[0][0].strip()
            claim_item = get_item_from_page_link(claim_link)
            if claim_item:
                claim_value = {'item': claim_item}
    elif key.lower() == "circumscripció":
        # Item
        logger.info(f"Parse as item")
        matches = LINK_REGEX.findall(value)
        if matches:
            claim_link = matches[0][0].strip()
            claim_item = get_item_from_page_link(claim_link)
            if claim_item:
                claim_value = {'item': claim_item}
                claim_property = ELECTORAL_DISTRICT
        else:
            if value.lower()[0] in ['a', 'e', 'i', 'o', 'u']:
                claim_link = f"Circumscripció electoral d'{value}"
            else:
                claim_link = f"Circumscripció electoral de {value}"
            claim_item = get_item_from_page_link(claim_link, langs=['ca'])
            if claim_item:
                claim_value = {'item': claim_item}
                claim_property = ELECTORAL_DISTRICT
            else:
                logger.error(f"Failed parsing as item: {value}")
                return
    else:
        # TODO: ordre, junt_a, nominat, designat
        logger.error(f"Unforeseen case for position qualifier: {key}: {value}")
        return
    if claim_value:
        logger.info(f"Found claim value {claim_value} for position qualifier: {key}: {value}")
        if key in INFOTABLE_PARAMS:
            qualifier_claim = Claim(property=INFOTABLE_PARAMS[key], **claim_value)
        else:
            qualifier_claim = Claim(property=claim_property, **claim_value)
    else:
        logger.error(f"No claim value found for position qualifier: {key}: {value}")
        return
    return qualifier_claim


def parse_position(position):
    logger.info(f"Parse position: {position}")
    if 'carrec' not in position:
        logger.error(f"Malformed position does not contain 'carrec': {position}")
        return None, []
    position_claim, qualifiers = parse_position_value(position['carrec'])
    if not position_claim:
        logger.error(f"Skip parsing position qualifiers: no position claim found for {position['carrec']}")
        return None, []
    # Position qualifiers
    logger.info("Parse position qualifiers")
    for position_key, position_value in position.items():
        qualifier_claim = None
        # carrec
        if position_key == 'carrec':
            continue
        # k_etiqueta
        elif position_key == 'k_etiqueta':
            label_key = position_key
            label_value = position_value
            name_key = 'k_nom'  # position_key.replace('_etiqueta', '_nom')
            if name_key not in position:
                logger.error(
                    f"Missing member of k_(label, name) pair: no name {name_key} for label {label_key}: {label_value}")
                continue
            name_value = position[name_key]
            logger.info(f"Parse k_(label, name) pair: ({label_value}, {name_value})")
            qualifier_claim = parse_position_qualifier(label_value, name_value)
        elif position_key == 'k_nom':
            name_key = position_key
            name_value = position_value
            label_key = 'k_etiqueta'  # position_key.replace('_nom', '_etiqueta')
            if label_key not in position:
                logger.error(
                    f"Missing member of k_(label, name) pair: no label {label_key} for name {name_key}: {name_value}")
            continue # already parsed
        # _etiqueta
        elif '_etiqueta' in position_key:
            label_key = position_key
            label_value = position_value
            name_key = position_key.replace('_etiqueta', '_nom')
            if name_key not in position:
                logger.error(
                    f"Missing member of (label, name) pair: no name {name_key} for label {label_key}: {label_value}")
                continue
            # TODO: parse pair
            name_value = position[name_key]
            logger.error(f"TODO: Parse (label, name) pair ({label_key}, {name_key}): ({label_value}, {name_value})")
            return None, []
        elif '_nom' in position_key:
            name_key = position_key
            name_value = position_value
            label_key = position_key.replace('_nom', '_etiqueta')
            if label_key not in position:
                logger.error(
                    f"Missing member of (label, name) pair: no label {label_key} for name {name_key}: {name_value}")
            continue  # already parsed
        # rest
        elif position_key in INFOTABLE_PARAMS:
            qualifier_claim = parse_position_qualifier(position_key, position_value)
        else:
            logger.error(f"Unknown position qualifier key, value: {position_key}; {position_value}")
            return None, []
        if not qualifier_claim:
            logger.error(f"No qualifier claim")
            return None, []
        elif qualifier_claim == 'CONTINUE':
            continue
        qualifiers.append(qualifier_claim)
    return position_claim, qualifiers


def create_position_statements(positions):
    statements = []
    # Parse each position
    for position in positions:
        position_claim, qualifiers = parse_position(position)
        if not position_claim:
            # 1. Create the maximum number of statements
            # logger.error(f"No position claim: skipped position {position}")
            # continue
            # 2. Create either all or no statements
            logger.error(f"No position claim: skipped all positions because of position {position}")
            return
        statements.append((position_claim, qualifiers))
    # Create statements
    sources = [Claim(property=IMPORTED_FROM_WIKIMEDIA_PROJECT, item=CATALAN_WIKIPEDIA)]
    statements = [Statement(claim=position_claim, qualifiers=qualifiers, sources=sources)
                  for position_claim, qualifiers in statements]
    return statements


def get_item(page):
    item = get_item_from_page(page)
    item = Item.from_pwb(item)
    logger.info(f"Main item {item.id} from page: {page}")
    return item


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    # Configurate logger
    config_logger(log_filename=args.log, debug=args.debug)
    logger.info("START transfer_infotable")

    # Generator
    generator = create_generator(groupsize=1)  # TODO: remove groupsize in prod
    for i, page in enumerate(generator):
        logger.info(f"{i + 1} Page: {page}")
        infotable_params = parse_infotable(page)
        logger.info(f"Infotable parameters: {infotable_params}")
        positions = extract_positions(infotable_params)
        logger.info(f"Positions: {positions}")
        position_statements = create_position_statements(positions)
        if not position_statements:
            logger.error(f"No position statements. ")
            continue
        # Get item
        item = get_item(page)
        # DEBUG
        if args.debug:
            # import pdb;pdb.set_trace()
            if i >= 49:
                break
