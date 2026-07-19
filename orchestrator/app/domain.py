from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class InventoryItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=100)
    large: bool = False


class MoveCreate(BaseModel):
    origin: str = Field(min_length=5, max_length=300)
    destination: str = Field(min_length=5, max_length=300)
    move_date: str = Field(min_length=8, max_length=32)
    budget_min: int = Field(ge=0, le=1_000_000)
    budget_max: int = Field(gt=0, le=1_000_000)
    service_type: Literal["labor_only", "truck_and_movers", "full_service"]
    bedrooms: int = Field(ge=0, le=20)
    movers_count: int = Field(ge=1, le=20)
    origin_floor: int = Field(ge=0, le=100)
    destination_floor: int = Field(ge=0, le=100)
    origin_elevator: bool = False
    destination_elevator: bool = False
    long_carry: bool = False
    parking_constraints: str = Field(default="", max_length=500)
    inventory: list[InventoryItem] = Field(min_length=1, max_length=100)
    notes: str = Field(default="", max_length=2000)
    confirmed: bool
    outreach_consent: bool
    max_carriers: int = Field(default=3, ge=1, le=3)

    @model_validator(mode="after")
    def validate_business_rules(self) -> MoveCreate:
        if self.budget_max < self.budget_min:
            raise ValueError("budget_max must be greater than or equal to budget_min")
        if not self.confirmed:
            raise ValueError("the move specification must be explicitly confirmed")
        if not self.outreach_consent:
            raise ValueError("separate outreach consent is required")
        return self


class QuoteResult(BaseModel):
    outcome: Literal[
        "itemized_quote",
        "partial_decline",
        "callback_commitment",
        "documented_decline",
        "no_answer",
        "technical_failure",
    ]
    initial_total: float | None = Field(default=None, ge=0)
    final_total: float | None = Field(default=None, ge=0)
    fees: list[dict] = Field(default_factory=list)
    included_services: list[str] = Field(default_factory=list)
    excluded_services: list[str] = Field(default_factory=list)
    binding: Literal["binding", "non_binding", "unknown"] = "unknown"
    availability: str = Field(default="", max_length=500)
    deposit_terms: str = Field(default="", max_length=1000)
    cancellation_terms: str = Field(default="", max_length=1000)
    quote_validity: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_quote(self) -> QuoteResult:
        if self.outcome == "itemized_quote" and self.final_total is None:
            raise ValueError("itemized_quote requires final_total")
        if self.outcome == "partial_decline" and self.initial_total is None and self.final_total is None:
            raise ValueError("partial_decline requires a stated price")
        return self
