from __future__ import annotations

__all__ = ("Input",)

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.literal import Literal
from facilitate.model.node import Node
from facilitate.util import generate_id, quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Input(Node):
    name: str
    expression: Node | None

    @classmethod
    def create(
        cls,
        name: str,
        expression: Node | None,
        *,
        id_: str | None = None,
    ) -> Input:
        if not id_:
            id_ = generate_id(f"input:{name}")
        return cls(id_=id_, name=name, expression=expression)

    def __hash__(self) -> int:
        return hash(self.id_)

    def add_literal(self, value: str) -> Literal:
        if self.expression is not None:
            error = f"cannot add literal to {self.id_}: already has expression."
            raise ValueError(error)
        literal = Literal.create(value)
        literal.parent = self
        self.expression = literal
        return literal

    @classmethod
    def determine_id(cls, block_id: str, input_name: str) -> str:
        return f":input[{input_name}]@{block_id}"

    @overrides
    def copy(self: t.Self) -> t.Self:
        expression = None if self.expression is None else self.expression.copy()
        return self.__class__(
            id_=self.id_,
            tags=self.tags.copy(),
            name=self.name,
            expression=expression,
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Input) and self.name == other.name

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not self.surface_equivalent_to(other):
            return False
        assert isinstance(other, Input)

        if self.expression is None:
            return other.expression is None
        assert other.expression is not None
        return self.expression.equivalent_to(other.expression)

    @overrides
    def children(self) -> t.Iterator[Node]:
        if self.expression is not None:
            yield self.expression
        else:
            yield from ()

    @overrides
    def remove_child(self, child: Node) -> None:
        if self.expression is not child:
            error = f"cannot remove child {child.id_}: not expression of {self.id_}."
            raise ValueError(error)
        child.parent = None
        self.expression = None

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"input:{self.name}"'
        attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label=label,
            **attributes,
        )

        if self.expression is not None:
            self.expression._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(self.expression.id_))


