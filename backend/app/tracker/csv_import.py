"""
CSV import parser for portfolio positions.

Supported CSV format:
  symbol, asset_type, quantity, price, date, option_type, strike, expiration

Required columns: symbol, quantity, price
Optional columns: asset_type (default: stock), date, option_type, strike, expiration
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ImportRow:
    symbol: str
    asset_type: str  # stock, option, leap
    quantity: float
    price: float
    date: datetime | None = None
    option_type: str | None = None  # call, put
    strike: float | None = None
    expiration: datetime | None = None


@dataclass
class ImportResult:
    rows: list[ImportRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: int = 0


REQUIRED_COLUMNS = {"symbol", "quantity", "price"}

COLUMN_ALIASES = {
    "ticker": "symbol",
    "sym": "symbol",
    "type": "asset_type",
    "asset_type": "asset_type",
    "qty": "quantity",
    "shares": "quantity",
    "quantity": "quantity",
    "price": "price",
    "cost": "price",
    "avg_cost": "price",
    "date": "date",
    "trade_date": "date",
    "timestamp": "date",
    "option_type": "option_type",
    "put_call": "option_type",
    "strike": "strike",
    "strike_price": "strike",
    "expiration": "expiration",
    "expiry": "expiration",
    "exp_date": "expiration",
}


def _normalize_header(header: str) -> str:
    cleaned = header.strip().lower().replace(" ", "_").replace("-", "_")
    return COLUMN_ALIASES.get(cleaned, cleaned)


def _parse_date(value: str) -> datetime | None:
    if not value.strip():
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_csv(content: str) -> ImportResult:
    """Parse CSV content into ImportRows."""
    result = ImportResult()
    reader = csv.DictReader(io.StringIO(content))

    if reader.fieldnames is None:
        result.errors.append("CSV has no header row")
        return result

    # Normalize headers
    normalized = {_normalize_header(h): h for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - set(normalized.keys())
    if missing:
        result.errors.append(f"Missing required columns: {', '.join(missing)}")
        return result

    for i, raw_row in enumerate(reader, start=2):
        row_map = {_normalize_header(k): v for k, v in raw_row.items()}

        try:
            symbol = row_map.get("symbol", "").strip().upper()
            if not symbol:
                result.errors.append(f"Row {i}: empty symbol")
                result.skipped += 1
                continue

            quantity = float(row_map.get("quantity", 0))
            price = float(row_map.get("price", 0))

            if quantity <= 0 or price <= 0:
                result.errors.append(f"Row {i}: quantity and price must be positive")
                result.skipped += 1
                continue

            asset_type = row_map.get("asset_type", "stock").strip().lower()
            if asset_type not in ("stock", "option", "leap"):
                asset_type = "stock"

            trade_date = _parse_date(row_map.get("date", ""))
            option_type = row_map.get("option_type", "").strip().lower() or None
            if option_type and option_type not in ("call", "put"):
                option_type = None

            strike = None
            if row_map.get("strike"):
                try:
                    strike = float(row_map["strike"])
                except ValueError:
                    pass

            expiration = _parse_date(row_map.get("expiration", ""))

            result.rows.append(ImportRow(
                symbol=symbol,
                asset_type=asset_type,
                quantity=quantity,
                price=price,
                date=trade_date,
                option_type=option_type,
                strike=strike,
                expiration=expiration,
            ))

        except (ValueError, KeyError) as e:
            result.errors.append(f"Row {i}: {e}")
            result.skipped += 1

    return result
