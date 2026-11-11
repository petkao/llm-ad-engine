from __future__ import annotations

from pydantic import BaseModel, Field


class BuyerSearchRequest(BaseModel):
    query: str = Field(description="Buyer query or purchase intent.")
    category: str | None = Field(default=None, description="Optional category filter.")
    device_id: str | None = Field(default=None, description="Anonymous device identifier.")
    limit: int | None = Field(default=None, description="Maximum number of matches to inspect.")
    video_only: bool = Field(default=False, description="True when video ads are required.")


class BuyerExplainRequest(BaseModel):
    ad_id: str = Field(description="Ad UUID to explain.")
    query: str = Field(description="Buyer query or purchase intent.")
    category: str | None = Field(default=None, description="Optional category filter.")
    device_id: str | None = Field(default=None, description="Anonymous device identifier.")
    limit: int | None = Field(default=None, description="Maximum number of ranked items to inspect.")


class SellerBillingRequest(BaseModel):
    seller_id: str = Field(description="Seller UUID.")
    create_ticket: bool = Field(default=False, description="Create a billing support ticket when true.")
    subject: str | None = Field(default=None, description="Ticket subject when a ticket is needed.")
    description: str | None = Field(default=None, description="Ticket description when a ticket is needed.")
    email: str | None = Field(default=None, description="Optional contact email for the ticket.")
    priority: str = Field(default="medium", description="Ticket priority.")


class SellerAdLookupRequest(BaseModel):
    ad_id: str = Field(description="Ad UUID to inspect.")


class SellerSupportRequest(BaseModel):
    seller_id: str | None = Field(default=None, description="Seller UUID when known.")
    ad_id: str | None = Field(default=None, description="Ad UUID when known.")
    query: str | None = Field(default=None, description="Buyer query when match quality is part of the issue.")
    category: str | None = Field(default=None, description="Optional category filter.")
    billing_related: bool = Field(default=False, description="Whether the issue includes billing context.")
    needs_match_explanation: bool = Field(default=False, description="Whether to explain match quality.")


class QaRequest(BaseModel):
    objective: str = Field(description="The workflow or tool behavior to validate.")
