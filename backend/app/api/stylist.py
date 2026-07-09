from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    StylistChatRequest,
    StylistChatResponse,
)
from app.services.openai_service import AIStylistService
from app.services.product_service import ProductService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/stylist", tags=["personal stylist"])


@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    products = ProductService(db).list_products(active_only=True, in_stock_only=True)
    recommendations = RecommendationService().recommend(
        products,
        payload.profile,
        limit=payload.limit,
    )
    return RecommendationResponse(recommendations=recommendations)


@router.post("/chat", response_model=StylistChatResponse)
def chat_with_stylist(
    payload: StylistChatRequest,
    db: Session = Depends(get_db),
) -> StylistChatResponse:
    product_service = ProductService(db)
    recommendation_service = RecommendationService()
    products = product_service.list_products(active_only=True, in_stock_only=True)

    profile = payload.profile
    if profile is None:
        from app.schemas import StyleProfile

        profile = StyleProfile(style_preferences=[payload.message])

    recommendations = recommendation_service.recommend(
        products,
        profile,
        limit=payload.limit,
    )

    ai_reply = AIStylistService().generate_reply(
        message=payload.message,
        profile=profile,
        recommendations=recommendations,
    )

    if ai_reply:
        return StylistChatResponse(
            reply=ai_reply,
            recommendations=recommendations,
            used_model="ollama",
        )

    return StylistChatResponse(
        reply=recommendation_service.build_fallback_reply(
            payload.message,
            recommendations,
        ),
        recommendations=recommendations,
        used_model="rule-based",
    )
