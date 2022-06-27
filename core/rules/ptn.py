from binascii import hexlify
from typing import Set, Tuple

from core.content import Content
from core.rule import Rule

import PTN


class PTNRule(Rule):
    RULE_NAME = "PTN"

    def apply_rule(self, content: Content) -> Set[Tuple[str, str, str]]:
        metadata = PTN.parse(content.data.decode())
        print(metadata)
        triplets = set()
        for relation, tail in metadata.items():
            if not tail:
                continue
            if relation == "excess":
                continue

            # Some items can be a list and we have to add multiple triplets
            if isinstance(tail, list):
                for tail_item in tail:
                    triplets.add((hexlify(content.get_hash()).decode(), relation, tail_item))
            else:
                triplets.add((hexlify(content.get_hash()).decode(), relation, tail))
        return triplets
