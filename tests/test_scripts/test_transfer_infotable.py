import pytest

from transfer_infotable import parse_position_value

# Constants
# P
APPOINTED_BY = 'P748'
# Q
MAYOR_OF_A_CORUNA = 'Q12391919'
MAYOR_OF_LA_VALL_D_UIXO = 'Q26693191'
MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA = 'Q18714088'
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'
MINISTER_OF_THE_NAVY = 'Q15895305'
PARLIAMENT_OF_CATALONIA = 'Q135630'
PRESIDENT_OF_COLOMBIA = 'Q853475'
PRESIDENT_OF_THE_COUNCIL_OF_CASTILE = 'Q6360109'


class TestScriptTransferInfotable:

    @pytest.mark.parametrize("position_value, expected_claim_id, expected_qualifiers", [
        ("[[Ministeri de Marina d'Espanya|Ministre de Marina]]", MINISTER_OF_THE_NAVY, []),
        ("[[La Corunya|Alcalde de La Corunya]]", MAYOR_OF_A_CORUNA, []),
        ("Diputada al [[Parlament de Catalunya]]", MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA, []),
        ("[[Senat d'Espanya|Senadora]] designat pel [[Parlament de Catalunya]]", MEMBER_OF_THE_SENATE_OF_SPAIN, [
            (APPOINTED_BY, PARLIAMENT_OF_CATALONIA)]),
        ("Alcalde de [[la Vall d'Uixó]]", MAYOR_OF_LA_VALL_D_UIXO, []),
        ("[[Llista de presidents de Colòmbia|President de Colòmbia]]", PRESIDENT_OF_COLOMBIA, []),
        ("[[President del Consell de Castella]]", PRESIDENT_OF_THE_COUNCIL_OF_CASTILE, []),
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

