import os
from typing import Literal
from dotenv import load_dotenv
from anthropic import Anthropic
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

# 3. Give the model a "tool" whose input is your schema, and force it to use it
tools = [{
    "name": "save_invoice",
    "description": "Save the extracted invoice data.",
    "input_schema": Invoice.model_json_schema(),
}]

messages = [{"role": "user", "content": f"Extract the invoice data and save it with the save_invoice tool:\n{text}"}]

# 4. Call, validate, and retry if the output is wrong
for attempt in range(3):
    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1000,
        tools=tools,
        # Newer models don't allow forcing a tool, so we ask for it in the prompt
        tool_choice={"type": "auto"},
        messages=messages,
    )
    block = next((b for b in response.content if b.type == "tool_use"), None)
    if block is None:
        raise SystemExit("The model answered without calling save_invoice")

    try:
        invoice = Invoice.model_validate(block.input)
        break
    except ValidationError as e:
        print(f"Attempt {attempt + 1} failed:\n{e}\n")
        # Send the error back so the model can fix its answer
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": block.id,
            "is_error": True,
            "content": f"Validation failed, fix it: {e}",
        }]})
else:
    raise SystemExit("Could not get valid data after 3 attempts")

# 5. Now it's a real Python object
print(invoice.model_dump_json(indent=2))
print(f"\nVendor: {invoice.vendor}")
print(f"Items: {len(invoice.items)}, total: {invoice.total} {invoice.currency}")