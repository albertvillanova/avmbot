"""
python -m pytest -s tests/test_scripts
"""

import pytest

from transfer_infotable import parse_date, parse_position_value

# Constants
# P
APPOINTED_BY = 'P748'
# Q
AMBASSADOR_OF_SPAIN_TO_FRANCE = 'Q27969744'
GENERAL_CAPTAIN_OF_VALENCIA = 'Q54875187'
MAYOR_OF_A_CORUNA = 'Q12391919'
MAYOR_OF_LA_VALL_D_UIXO = 'Q26693191'
MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN = 'Q18171345'
MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA = 'Q18714088'
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'
MINISTER_OF_FOREIGN_AFFAIRS_OF_SPAIN = 'Q32969906'
MINISTER_OF_THE_NAVY = 'Q15895305'
PARLIAMENT_OF_CATALONIA = 'Q135630'
PRESIDENT_OF_COLOMBIA = 'Q853475'
PRESIDENT_OF_THE_COUNCIL_OF_CASTILE = 'Q6360109'


class TestScriptTransferInfotable:

    @pytest.mark.parametrize("date, expected_date_claim_value", [
        ("[[23 de gener]] de [[1935]]", {'year': 1935, 'month': 1, 'day': 23}),
        ("[[7 d'agost]] de [[1926]]", {'year': 1926, 'month': 8, 'day': 7}),
        ("[[1918]]", {'year': 1918}),
    ])
    def test_parse_date(self, date, expected_date_claim_value):
        date_claim_value = parse_date(date)
        assert date_claim_value == expected_date_claim_value

    @pytest.mark.parametrize("position_value, expected_claim_id, expected_qualifiers", [
        ("[[Ministeri de Marina d'Espanya|Ministre de Marina]]", MINISTER_OF_THE_NAVY, []),
        ("[[La Corunya|Alcalde de La Corunya]]", MAYOR_OF_A_CORUNA, []),
        ("Diputada al [[Parlament de Catalunya]]", MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA, []),
        ("[[Senat d'Espanya|Senadora]] designat pel [[Parlament de Catalunya]]", MEMBER_OF_THE_SENATE_OF_SPAIN, [
            (APPOINTED_BY, PARLIAMENT_OF_CATALONIA)]),
        ("Alcalde de [[la Vall d'Uixó]]", MAYOR_OF_LA_VALL_D_UIXO, []),
        ("[[Llista de presidents de Colòmbia|President de Colòmbia]]", PRESIDENT_OF_COLOMBIA, []),
        ("[[President del Consell de Castella]]", PRESIDENT_OF_THE_COUNCIL_OF_CASTILE, []),
        ("Ambaixador del regne d'Espanya al Regne de França", AMBASSADOR_OF_SPAIN_TO_FRANCE, []),
        ("[[Capità general de València]]", GENERAL_CAPTAIN_OF_VALENCIA, []),
        ("[[Llista dels Ministres d'Afers Exteriors d'Espanya|Ministre d'Estat]]", MINISTER_OF_FOREIGN_AFFAIRS_OF_SPAIN,
         []),
        ("Diputat al [[Congrés dels Diputats]]", MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN, [])
    ])
    def test_parse_position_value(self, position_value, expected_claim_id, expected_qualifiers):
        position_claim, qualifiers = parse_position_value(position_value)
        assert position_claim.value.id == expected_claim_id
        if qualifiers:
            for claim, (pid, qid) in zip(qualifiers, expected_qualifiers):
                assert claim.property == pid
                assert claim.value.id == qid
        else:
            assert qualifiers == expected_qualifiers

