from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product


DEMO_PRODUCTS = [
    {
        "sku": "FT-BLAZER-ALFA-PRETO",
        "name": "Blazer Alfaiataria Preto",
        "description": "Blazer estruturado para looks de trabalho, jantar e producoes elegantes.",
        "category": "blazer",
        "price": Decimal("329.90"),
        "stock": 8,
        "image_url": "",
        "sizes": ["p", "m", "g"],
        "colors": ["preto"],
        "tags": ["elegante", "trabalho", "noite"],
        "style_keywords": ["classico", "sofisticado", "alfaiataria"],
    },
    {
        "sku": "FT-VESTIDO-MIDI-TERRACOTA",
        "name": "Vestido Midi Terracota",
        "description": "Vestido midi fluido, ideal para almoco, viagem e eventos casuais chic.",
        "category": "vestido",
        "price": Decimal("249.90"),
        "stock": 10,
        "image_url": "",
        "sizes": ["pp", "p", "m", "g"],
        "colors": ["terracota", "laranja"],
        "tags": ["casual", "evento", "verao"],
        "style_keywords": ["romantico", "leve", "feminino"],
    },
    {
        "sku": "FT-CAMISA-OFF-WHITE",
        "name": "Camisa Off White Cetim",
        "description": "Camisa acetinada versatil para composicoes de trabalho ou saida noturna.",
        "category": "camisa",
        "price": Decimal("179.90"),
        "stock": 14,
        "image_url": "",
        "sizes": ["p", "m", "g", "gg"],
        "colors": ["off white", "branco"],
        "tags": ["trabalho", "basico", "noite"],
        "style_keywords": ["minimalista", "elegante", "versatil"],
    },
    {
        "sku": "FT-CALCA-WIDE-AREIA",
        "name": "Calca Wide Leg Areia",
        "description": "Calca wide leg de cintura alta para looks modernos e confortaveis.",
        "category": "calca",
        "price": Decimal("219.90"),
        "stock": 12,
        "image_url": "",
        "sizes": ["36", "38", "40", "42", "44"],
        "colors": ["areia", "bege"],
        "tags": ["trabalho", "casual", "conforto"],
        "style_keywords": ["moderno", "minimalista", "chic"],
    },
    {
        "sku": "FT-TOP-CANELADO-VERDE",
        "name": "Top Canelado Verde Oliva",
        "description": "Top canelado para sobreposicoes, looks casuais e producoes de fim de semana.",
        "category": "top",
        "price": Decimal("89.90"),
        "stock": 20,
        "image_url": "",
        "sizes": ["pp", "p", "m", "g"],
        "colors": ["verde", "oliva"],
        "tags": ["casual", "fim de semana", "basico"],
        "style_keywords": ["despojado", "natural", "urbano"],
    },
]


def seed_demo_products(db: Session) -> None:
    has_products = db.scalar(select(Product.id).limit(1))
    if has_products:
        return

    for product_data in DEMO_PRODUCTS:
        db.add(Product(**product_data))
    db.commit()
