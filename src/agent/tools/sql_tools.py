"""Deterministic relational tools for inventory lookups, pricing, and order status."""

from langchain_core.tools import tool
from sqlalchemy import select

from src.database.connection import SessionLocal
from src.database.models.category import Category
from src.database.models.customer import Customer
from src.database.models.order import Order, OrderItem
from src.database.models.product import Product
from src.database.models.promotion import Promotion
from src.utils.logger import logger


@tool
def consultar_catalogo_produtos(
    termo_busca: str | None = None,
    categoria: str | None = None,
    preco_maximo: float | None = None,
    apenas_disponiveis: bool = True,
    limite: int = 5,
) -> str:
    """Searches musical instruments in the store catalog by keyword, category, or budget.

    Args:
        termo_busca: Partial product name or brand (e.g., 'Yamaha', 'Fender', 'Takamine', 'violao').
        categoria: Category name (e.g., 'Guitarras', 'Baixos', 'Violões', 'Teclados', 'Baterias').
        preco_maximo: Maximum price filter in Brazilian Reais (BRL).
        apenas_disponiveis: Whether to filter only products with stock_quantity > 0. Defaults to True.
        limite: Maximum number of products to return (capped at 10).

    Returns:
        str: Formatted markdown list of matching instruments with prices and stock.
    """
    logger.info(
        f"[Tool: Catalog] Term: '{termo_busca}', Category: '{categoria}', Max Price: {preco_maximo}"
    )
    session = SessionLocal()
    try:
        stmt = (
            select(Product, Category.name.label("category_name"))
            .join(Category, Product.category_id == Category.category_id)
            .where(Product.status == "active")
        )

        if apenas_disponiveis:
            stmt = stmt.where(Product.stock_quantity > 0)

        if termo_busca:
            stmt = stmt.where(Product.name.ilike(f"%{termo_busca.strip()}%"))

        if categoria:
            stmt = stmt.where(Category.name.ilike(f"%{categoria.strip()}%"))

        if preco_maximo is not None:
            stmt = stmt.where(Product.price_brl <= preco_maximo)

        stmt = stmt.order_by(Product.price_brl.asc()).limit(min(limite, 10))
        results = session.execute(stmt).all()

        if not results:
            return "Nenhum instrumento encontrado com os critérios fornecidos."

        output_lines = []
        for product, category_name in results:
            promo_stmt = select(Promotion).where(
                Promotion.product_id == product.product_id,
                Promotion.is_active == 1,
            )
            promo = session.execute(promo_stmt).scalar_one_or_none()

            price_info = f"R$ {product.price_brl:.2f}"
            if promo:
                discounted_price = product.price_brl * (
                    1 - (promo.discount_percent / 100)
                )
                price_info += (
                    f" (PROMOÇÃO: {promo.discount_percent:.0f}% OFF -> "
                    f"R$ {discounted_price:.2f} - {promo.description})"
                )

            item_card = (
                f"- **{product.name}** (Cód: {product.product_id})\n"
                f"  Categoria: {category_name} | Preço: {price_info} | Estoque: {product.stock_quantity} un.\n"
                f"  Descrição: {product.description}"
            )
            output_lines.append(item_card)

        return "\n\n".join(output_lines)
    except Exception as exc:
        logger.error(f"[Tool: Catalog] Database query error: {str(exc)}")
        return f"Erro ao consultar catálogo no banco de dados: {str(exc)}"
    finally:
        session.close()


@tool
def consultar_status_pedido(
    order_id: int | None = None,
    telefone_cliente: str | None = None,
    email_cliente: str | None = None,
) -> str:
    """Queries detailed order information, tracking codes, payment, and delivery estimates.

    At least one identifier must be provided: order_id OR customer phone/email.

    Args:
        order_id: Numeric order identifier.
        telefone_cliente: Customer phone or WhatsApp number (with or without formatting).
        email_cliente: Customer registered email address.

    Returns:
        str: Formatted order summary including items, current status, and tracking code.
    """
    logger.info(
        f"[Tool: Order] ID: {order_id}, Phone: '{telefone_cliente}', Email: '{email_cliente}'"
    )
    if not order_id and not telefone_cliente and not email_cliente:
        return "Por favor, informe o número do pedido, telefone ou e-mail cadastrado para localizar a encomenda."

    session = SessionLocal()
    try:
        stmt = select(Order, Customer).join(
            Customer, Order.customer_id == Customer.customer_id
        )

        if order_id:
            stmt = stmt.where(Order.order_id == order_id)
        elif telefone_cliente:
            digits_only = "".join(filter(str.isdigit, telefone_cliente))
            stmt = stmt.where(Customer.phone.ilike(f"%{digits_only[-8:]}%"))
        elif email_cliente:
            stmt = stmt.where(Customer.email.ilike(email_cliente.strip()))

        stmt = stmt.order_by(Order.order_date.desc()).limit(3)
        orders = session.execute(stmt).all()

        if not orders:
            return "Nenhum pedido encontrado para as informações fornecidas."

        orders_output = []
        for order, customer in orders:
            # Query order items and joined product details
            items_stmt = (
                select(OrderItem, Product)
                .join(Product, OrderItem.product_id == Product.product_id)
                .where(OrderItem.order_id == order.order_id)
            )
            items = session.execute(items_stmt).all()
            products_summary = ", ".join(
                [f"{item.quantity}x {prod.name}" for item, prod in items]
            )

            details = (
                f"📦 **Pedido #{order.order_id}**\n"
                f"- Cliente: {customer.name} ({customer.phone})\n"
                f"- Data do Pedido: {order.order_date}\n"
                f"- Status Atual: {order.status.upper()}\n"
                f"- Itens: {products_summary}\n"
                f"- Valor Total: R$ {order.total_brl:.2f} (Pagamento: {order.payment_method})\n"
                f"- Código de Rastreamento: {order.tracking_code or 'Aguardando despacho'}\n"
                f"- Previsão de Entrega: {order.estimated_delivery or 'Não definida'}"
            )
            orders_output.append(details)

        return "\n\n---\n\n".join(orders_output)
    except Exception as exc:
        logger.error(f"[Tool: Order] Database query error: {str(exc)}")
        return f"Erro ao consultar pedidos no banco de dados: {str(exc)}"
    finally:
        session.close()
