"""
Step 2 — Structured output with Pydantic

The model returns a typed Python object instead of free text.
Run:  docker compose exec app python step2/extract.py
"""
import os
from typing import Literal

# Uses the API's structured outputs feature (output_config).
from anthropic import Anthropic, transform_schema
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, model_validator

load_dotenv()
client = Anthropic()


# 1. Describe the data you want, as Python classes
class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float


class Invoice(BaseModel):
    vendor: str
    invoice_date: str = Field(description="Date in YYYY-MM-DD format")
    currency: Literal["EUR", "MKD", "USD", "CHF"]
    items: list[LineItem]
    total: float

    # Your own business rule: the items must add up to the total
    @model_validator(mode="after")
    def check_total(self):
        calculated = sum(i.quantity * i.unit_price for i in self.items)
        if abs(calculated - self.total) > 0.01:
            raise ValueError(f"Items add up to {calculated}, but total is {self.total}")
        return self


# 2. Messy input text, the kind real systems get
text = """
Faturë nga Studio Maya, Shkup. Data: 28 tetor 2026.
2 fustane mbrëmje x 4500 den, 1 shall mëndafshi 1200 den.
Gjithsej: 10200 denarë.
"""

# 3. Structured outputs: the API guarantees JSON that matches this schema
output_config = {
    "format": {
        "type": "json_schema",
        "schema": transform_schema(Invoice.model_json_schema()),
    }
}

messages = [{"role": "user", "content": f"Extract the invoice data:\n{text}"}]

# 4. Call, validate, and retry if the output is wrong
for attempt in range(3):
    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1000,
        output_config=output_config,
        messages=messages,
    )
    raw_json = next(b.text for b in response.content if b.type == "text")

    try:
        # The SHAPE is guaranteed by the API; your business rules are checked here
        invoice = Invoice.model_validate_json(raw_json)
        break
    except ValidationError as e:
        print(f"Attempt {attempt + 1} failed:\n{e}\n")
        # Send the error back so the model can fix its answer
        messages.append({"role": "assistant", "content": raw_json})
        messages.append({"role": "user", "content": f"Validation failed, fix it: {e}"})
else:
    raise SystemExit("Could not get valid data after 3 attempts")

# 5. Now it's a real Python object
print(invoice.model_dump_json(indent=2))
print(f"\nVendor: {invoice.vendor}")
print(f"Items: {len(invoice.items)}, total: {invoice.total} {invoice.currency}")
