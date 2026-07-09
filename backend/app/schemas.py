from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    description: str = ""
    category: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    image_url: str | None = None
    sizes: list[str] = []
    colors: list[str] = []
    tags: list[str] = []
    style_keywords: list[str] = []
    active: bool = True

    @field_validator("sizes", "colors", "tags", "style_keywords")
    @classmethod
    def normalize_list(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value if item.strip()]


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    price: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    sizes: list[str] | None = None
    colors: list[str] | None = None
    tags: list[str] | None = None
    style_keywords: list[str] | None = None
    active: bool | None = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    phone: str = Field(min_length=8, max_length=30)
    email: EmailStr | None = None
    style_notes: str = ""


class CustomerRead(CustomerCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    size: str | None = None
    color: str | None = None


class OrderCreate(BaseModel):
    customer: CustomerCreate | None = None
    customer_id: int | None = None
    items: list[OrderItemCreate] = Field(min_length=1)
    notes: str = ""


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    size: str | None
    color: str | None
    product: ProductRead

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    customer_id: int | None
    status: str
    subtotal: Decimal
    whatsapp_message: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)


class WhatsAppCheckoutResponse(BaseModel):
    order: OrderRead
    message: str
    wa_me_url: str | None


class StyleProfile(BaseModel):
    occasion: str | None = Field(
        default=None,
        description="Ex: trabalho, festa, casual, jantar, viagem.",
    )
    style_preferences: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    max_budget: Decimal | None = Field(default=None, gt=0)
    avoid: list[str] = Field(default_factory=list)

    @field_validator("style_preferences", "preferred_colors", "sizes", "avoid")
    @classmethod
    def normalize_terms(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value if item.strip()]


class RecommendationRequest(BaseModel):
    profile: StyleProfile
    limit: int = Field(default=5, ge=1, le=20)


class ProductRecommendation(BaseModel):
    product: ProductRead
    score: float
    reasons: list[str]


class RecommendationResponse(BaseModel):
    recommendations: list[ProductRecommendation]


class StylistChatRequest(BaseModel):
    message: str = Field(min_length=2)
    profile: StyleProfile | None = None
    limit: int = Field(default=4, ge=1, le=10)


class StylistChatResponse(BaseModel):
    reply: str
    recommendations: list[ProductRecommendation]
    used_model: str
