from abc import ABC, abstractmethod
from typing import Set, Tuple

from core.content import Content


class Rule(ABC):
    RULE_NAME = None

    @abstractmethod
    def apply_rule(self, content: Content) -> Set[Tuple[str, str, str]]:
        """
        Apply this rule to a piece of content. Returns a set of triplets in the knowledge graph.
        """
        pass

    def get_name(self) -> str:
        return self.RULE_NAME
