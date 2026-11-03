"""Tool registry exposing all agent tools for binding and execution."""

from src.agent.tools.sql_tools import (
    consultar_catalogo_produtos,
    consultar_status_pedido,
)

from src.agent.tools.rag_tools import consultar_politicas_loja

ALL_TOOLS = [
    consultar_politicas_loja,
    consultar_catalogo_produtos,
    consultar_status_pedido,
]

__all__ = [
    "consultar_politicas_loja",
    "consultar_catalogo_produtos",
    "consultar_status_pedido",
    "ALL_TOOLS",
]
