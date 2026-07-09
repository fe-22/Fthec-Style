from decimal import Decimal
from urllib.parse import quote_plus

from app.core.config import Settings, get_settings
from app.models import Customer, Order


def normalize_whatsapp_number(phone: str) -> str:
    return "".join(character for character in phone if character.isdigit())


def format_brl(value: Decimal) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class WhatsAppService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def build_checkout_message(
        self,
        *,
        order: Order,
        customer: Customer | None,
        notes: str = "",
    ) -> str:
        lines = [
            "Ola! Quero finalizar esta compra na PriStilo.",
            "",
            f"Pedido: #{order.id}",
        ]

        if customer:
            lines.extend(
                [
                    f"Cliente: {customer.name}",
                    f"Telefone: {customer.phone}",
                ]
            )

        lines.append("")
        lines.append("Itens:")

        for item in order.items:
            product = item.product
            variant_parts = []
            if item.size:
                variant_parts.append(f"tam. {item.size}")
            if item.color:
                variant_parts.append(f"cor {item.color}")
            variant = f" ({', '.join(variant_parts)})" if variant_parts else ""
            line_total = item.unit_price * item.quantity
            lines.append(
                f"- {item.quantity}x {product.name}{variant} - {format_brl(line_total)}"
            )

        lines.extend(["", f"Subtotal: {format_brl(order.subtotal)}"])

        if self.settings.public_store_url:
            lines.append(f"Link da vitrine: {self.settings.public_store_url}")

        if notes:
            lines.extend(["", f"Observacoes: {notes}"])

        lines.extend(
            [
                "",
                "Pode confirmar disponibilidade, frete e forma de pagamento?",
            ]
        )
        return "\n".join(lines)

    def build_checkout_url(self, message: str) -> str | None:
        phone = normalize_whatsapp_number(self.settings.consultant_whatsapp_number)
        if not phone:
            return None
        return f"https://api.whatsapp.com/send?phone={phone}&text={quote_plus(message)}"
