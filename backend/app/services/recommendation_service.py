from decimal import Decimal
from unicodedata import category, normalize

from app.models import Product
from app.schemas import ProductRecommendation, StyleProfile


OCCASION_KEYWORDS: dict[str, list[str]] = {
    "trabalho": ["trabalho", "alfaiataria", "classico", "minimalista", "elegante"],
    "festa": ["festa", "evento", "noite", "sofisticado", "brilho"],
    "jantar": ["jantar", "noite", "sofisticado", "elegante"],
    "casual": ["casual", "fim de semana", "conforto", "despojado", "basico"],
    "viagem": ["viagem", "conforto", "leve", "versatil", "casual"],
    "verao": ["verao", "leve", "fluido", "natural", "colorido"],
}


def normalize_term(value: str) -> str:
    decomposed = normalize("NFD", value.lower().strip())
    return "".join(char for char in decomposed if category(char) != "Mn")


def product_text(product: Product) -> str:
    values = [
        product.name,
        product.description,
        product.category,
        " ".join(product.tags or []),
        " ".join(product.style_keywords or []),
        " ".join(product.colors or []),
    ]
    return normalize_term(" ".join(values))


class RecommendationService:
    def recommend(
        self,
        products: list[Product],
        profile: StyleProfile,
        *,
        limit: int = 5,
    ) -> list[ProductRecommendation]:
        scored: list[ProductRecommendation] = []

        for product in products:
            result = self._score_product(product, profile)
            if result is None:
                continue
            score, reasons = result
            scored.append(
                ProductRecommendation(
                    product=product,
                    score=round(score, 2),
                    reasons=reasons,
                )
            )

        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    def build_fallback_reply(
        self,
        message: str,
        recommendations: list[ProductRecommendation],
    ) -> str:
        if not recommendations:
            return (
                "Ainda nao encontrei uma peca ideal no catalogo atual. "
                "Me diga ocasiao, tamanho, cores preferidas e faixa de preco "
                "para eu refinar a sugestao."
            )

        top = recommendations[0]
        product = top.product
        reasons = "; ".join(top.reasons[:2])
        return (
            f"Para o que voce descreveu, eu comecaria por {product.name}. "
            f"Ela combina porque {reasons}. "
            "Se quiser, posso separar outras opcoes e enviar para a consultora finalizar."
        )

    def _score_product(
        self,
        product: Product,
        profile: StyleProfile,
    ) -> tuple[float, list[str]] | None:
        if not product.active or product.stock <= 0:
            return None

        text = product_text(product)
        score = 0.2
        reasons: list[str] = ["disponivel em estoque"]

        if profile.max_budget is not None:
            if Decimal(product.price) > profile.max_budget:
                return None
            score += 0.8
            reasons.append("dentro do orcamento informado")

        if profile.sizes:
            matching_sizes = set(profile.sizes).intersection(product.sizes or [])
            if matching_sizes:
                score += 1.0
                reasons.append(
                    f"tem tamanho {', '.join(sorted(matching_sizes))}"
                )
            elif product.sizes:
                score -= 0.6

        if profile.preferred_colors:
            normalized_product_colors = {normalize_term(color) for color in product.colors or []}
            normalized_profile_colors = {
                normalize_term(color) for color in profile.preferred_colors
            }
            matching_colors = normalized_profile_colors.intersection(
                normalized_product_colors
            )
            if matching_colors:
                score += 1.2
                reasons.append(
                    f"combina com as cores: {', '.join(sorted(matching_colors))}"
                )

        if profile.occasion:
            occasion = normalize_term(profile.occasion)
            keywords = OCCASION_KEYWORDS.get(occasion, [occasion])
            matches = [keyword for keyword in keywords if normalize_term(keyword) in text]
            if matches:
                score += 1.4
                reasons.append(f"funciona para {profile.occasion}")

        for style in profile.style_preferences:
            normalized_style = normalize_term(style)
            if normalized_style in text:
                score += 0.9
                reasons.append(f"tem leitura {style}")

        for avoid in profile.avoid:
            if normalize_term(avoid) in text:
                score -= 1.0

        if score <= 0:
            return None

        return score, reasons
