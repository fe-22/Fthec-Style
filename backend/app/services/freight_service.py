from decimal import Decimal


class FreightService:
    """Placeholder for future Melhor Envio integration."""

    def estimate_local_pickup(self) -> dict[str, str | Decimal]:
        return {
            "service": "Retirada ou combinacao via consultora",
            "price": Decimal("0.00"),
            "deadline": "A confirmar no WhatsApp",
        }
