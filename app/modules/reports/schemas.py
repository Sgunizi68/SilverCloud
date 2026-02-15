from dataclasses import dataclass
from typing import Optional


@dataclass
class DateRange:
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class InvoicingSummaryResponse:
    total_invoices: float
    total_payments: float
    total_cash: float


@dataclass
class InventoryValuationResponse:
    inventory_valuation: float


@dataclass
class HRSummaryResponse:
    employee_count: int
