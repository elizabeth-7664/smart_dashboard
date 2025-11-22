# app/services/sales_analysis.py
import csv
import io
import json
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import select, func, text
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse

from app.database.setup import async_session
from app.models.sales import Sale

router = APIRouter(prefix="/api")

# ----------------- helper conversions -----------------
def row_to_dict(row) -> Dict[str, Any]:
    """Convert SQLAlchemy row to plain dict safely."""
    return {k: (v if not isinstance(v, (datetime,)) else str(v)) for k, v in row._asdict().items()}

# ----------------- KPI queries -----------------
async def compute_summary() -> Dict[str, Any]:
    """Total revenue, cost, profit, transactions, profit_margin."""
    async with async_session() as session:
        q = select(
            func.coalesce(func.sum(Sale.quantity * Sale.selling_price), 0).label("total_revenue"),
            func.coalesce(func.sum(Sale.quantity * Sale.cost_price), 0).label("total_cost"),
            func.coalesce(func.sum((Sale.selling_price - Sale.cost_price) * Sale.quantity), 0).label("total_profit"),
            func.coalesce(func.count(Sale.id), 0).label("transactions"),
        )
        r = await session.execute(q)
        row = r.one()
        revenue = float(row.total_revenue or 0)
        cost = float(row.total_cost or 0)
        profit = float(row.total_profit or 0)
        margin = (profit / revenue * 100) if revenue else 0.0
        return {
            "total_revenue": revenue,
            "total_cost": cost,
            "total_profit": profit,
            "transactions": int(row.transactions),
            "profit_margin_percent": round(margin, 2),
        }

async def revenue_per_product() -> List[Dict[str, Any]]:
    async with async_session() as session:
        q = select(
            Sale.product_name,
            func.coalesce(func.sum(Sale.quantity * Sale.selling_price), 0).label("revenue"),
            func.coalesce(func.sum(Sale.quantity), 0).label("units_sold"),
        ).group_by(Sale.product_name).order_by(func.sum(Sale.quantity * Sale.selling_price).desc())
        r = await session.execute(q)
        return [{"product_name": row.product_name, "revenue": float(row.revenue), "units_sold": int(row.units_sold)} for row in r]

async def profit_per_product() -> List[Dict[str, Any]]:
    async with async_session() as session:
        q = select(
            Sale.product_name,
            func.coalesce(func.sum((Sale.selling_price - Sale.cost_price) * Sale.quantity), 0).label("profit"),
            func.coalesce(func.sum(Sale.quantity), 0).label("units_sold"),
        ).group_by(Sale.product_name).order_by(func.sum((Sale.selling_price - Sale.cost_price) * Sale.quantity).desc())
        r = await session.execute(q)
        return [{"product_name": row.product_name, "profit": float(row.profit), "units_sold": int(row.units_sold)} for row in r]

async def best_and_most_profitable() -> Dict[str, Any]:
    """Return best selling (by units) and most profitable (by profit)."""
    rev = await revenue_per_product()
    prof = await profit_per_product()
    best_selling = rev[0] if rev else {}
    most_profitable = prof[0] if prof else {}
    return {"best_selling_product": best_selling, "most_profitable_product": most_profitable}

async def sales_per_day() -> List[Dict[str, Any]]:
    async with async_session() as session:
        q = select(
            Sale.date,
            func.coalesce(func.sum(Sale.quantity * Sale.selling_price), 0).label("revenue"),
            func.coalesce(func.sum(Sale.quantity), 0).label("units_sold")
        ).group_by(Sale.date).order_by(Sale.date)
        r = await session.execute(q)
        return [{"date": str(row.date), "revenue": float(row.revenue), "units_sold": int(row.units_sold)} for row in r]

async def payment_method_breakdown() -> List[Dict[str, Any]]:
    async with async_session() as session:
        q = select(
            Sale.payment_method,
            func.count(Sale.id).label("transactions"),
            func.coalesce(func.sum(Sale.quantity * Sale.selling_price), 0).label("revenue")
        ).group_by(Sale.payment_method).order_by(func.count(Sale.id).desc())
        r = await session.execute(q)
        return [{"payment_method": row.payment_method or "", "transactions": int(row.transactions), "revenue": float(row.revenue)} for row in r]

async def mpesa_transaction_count() -> int:
    async with async_session() as session:
        q = select(func.count(Sale.id)).where(Sale.mpesa_transaction_id != "")
        r = await session.execute(q)
        return int(r.scalar() or 0)

# ----------------- persistence helpers -----------------
async def ensure_reports_table_exists():
    """Create a simple JSONB reports table if not exists."""
    async with async_session() as session:
        sql = text("""
        CREATE TABLE IF NOT EXISTS analysis_reports (
            id SERIAL PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            summary JSONB
        )
        """)
        await session.execute(sql)
        await session.commit()

async def save_report_to_db(name: str, summary: Dict[str, Any]) -> int:
    """Insert summary JSON into analysis_reports and return the id."""
    await ensure_reports_table_exists()
    async with async_session() as session:
        insert_sql = text("INSERT INTO analysis_reports (name, summary) VALUES (:name, :summary) RETURNING id")
        params = {"name": name, "summary": json.dumps(summary)}
        r = await session.execute(insert_sql, params)
        await session.commit()
        new_id_row = r.first()
        return int(new_id_row.id) if new_id_row else None

# ----------------- export helpers -----------------
def write_json_file(path: str, payload: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def write_csv_report(path: str, fieldnames: List[str], rows: List[Dict[str, Any]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

# ----------------- orchestrator -----------------
@router.post("/run-analysis")
async def run_full_analysis(save_json: bool = True, save_csv: bool = True, save_db: bool = True):
    """
    Run full analysis and optionally save results.
    - save_json: save summary JSON to sales_analysis_<timestamp>.json
    - save_csv: save product-level CSVs (revenue_per_product.csv, profit_per_product.csv)
    - save_db: save summary JSON into analysis_reports table
    Returns analysis JSON and file paths (if saved).
    """
    # 1) compute all pieces in parallel-ish (serial here but async DB calls)
    summary = await compute_summary()
    rev_by_product = await revenue_per_product()
    profit_by_product = await profit_per_product()
    best_and_profit = await best_and_most_profitable()
    daily = await sales_per_day()
    payment = await payment_method_breakdown()
    mpesa_count = await mpesa_transaction_count()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    report = {
        "generated_at": timestamp,
        "summary": summary,
        "revenue_per_product": rev_by_product,
        "profit_per_product": profit_by_product,
        "best_selling_product": best_and_profit.get("best_selling_product", {}),
        "most_profitable_product": best_and_profit.get("most_profitable_product", {}),
        "sales_per_day": daily,
        "payment_methods": payment,
        "mpesa_transaction_count": mpesa_count
    }

    saved_files = {}

    # Save JSON
    if save_json:
        json_path = f"sales_analysis_{timestamp}.json"
        write_json_file(json_path, report)
        saved_files["json"] = json_path

    # Save CSVs: revenue_by_product and profit_by_product and daily
    if save_csv:
        rev_csv = f"revenue_per_product_{timestamp}.csv"
        write_csv_report(rev_csv, ["product_name", "revenue", "units_sold"], rev_by_product)
        prof_csv = f"profit_per_product_{timestamp}.csv"
        write_csv_report(prof_csv, ["product_name", "profit", "units_sold"], profit_by_product)
        daily_csv = f"sales_per_day_{timestamp}.csv"
        write_csv_report(daily_csv, ["date", "revenue", "units_sold"], daily)
        saved_files["csv"] = {"revenue_by_product": rev_csv, "profit_by_product": prof_csv, "sales_per_day": daily_csv}

    # Save to DB
    saved_report_id = None
    if save_db:
        saved_report_id = await save_report_to_db(f"analysis_{timestamp}", report)
        saved_files["db_report_id"] = saved_report_id

    # Return JSON response + file paths and inserted id
    response = {"report": report, "saved_files": saved_files}
    return JSONResponse(response)
