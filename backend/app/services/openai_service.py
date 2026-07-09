import json

import httpx

from app.core.config import Settings, get_settings
from app.schemas import ProductRecommendation, StyleProfile


class AIStylistService:
    """Optional local LLM integration through Ollama.

    The project does not require paid AI. If Ollama is disabled or unavailable,
    callers should use the deterministic recommendation fallback.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def generate_reply(
        self,
        *,
        message: str,
        profile: StyleProfile | None,
        recommendations: list[ProductRecommendation],
    ) -> str | None:
        if not self.settings.enable_ollama:
            return None

        catalog_context = [
            {
                "name": item.product.name,
                "category": item.product.category,
                "price": str(item.product.price),
                "colors": item.product.colors,
                "sizes": item.product.sizes,
                "reasons": item.reasons,
            }
            for item in recommendations
        ]

        system_prompt = (
            "Voce e uma consultora de moda da PriStilo. "
            "Responda em portugues do Brasil, com tom objetivo, elegante e vendedor. "
            "Use apenas produtos do contexto. Se faltar informacao, faca no maximo "
            "duas perguntas curtas. Nao invente estoque, desconto ou prazo."
        )

        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "mensagem_cliente": message,
                            "perfil": profile.model_dump(mode="json") if profile else None,
                            "produtos_recomendados": catalog_context,
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            "options": {"temperature": 0.4},
        }

        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        return data.get("message", {}).get("content")
