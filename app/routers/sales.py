import csv
import io
import asyncio
from fastapi import APIRouter, UploadFile, HTTPException
from datetime import datetime
from sqlalchemy import select
from app.database.setup import async_session
from app.models.sales import Sale
from app.utils.email_sender import send_report

router = APIRouter()


def to_int(val):
    try:
        return int(val)
    except:
        return 0

def to_float(val):
    try:
        return float(val)
    except:
        return 0.0

def to_str(val):
    return str(val).strip() if val else ""

def to_date(val):
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except:
        return None


# -------- ANALYSIS FUNCTION --------

def compute_analysis(rows):
    summary = {
        "total_revenue": 0.0,
        "total_cost": 0.0,
        "total_profit": 0.0,
        "transactions": len(rows),
    }

    revenue_per_product = {}
    profit_per_product = {}
    sales_per_day = {}
    payment_methods = {}

    for r in rows:
        revenue = r.selling_price * r.quantity
        cost = r.cost_price * r.quantity
        profit = revenue - cost

        summary["total_revenue"] += revenue
        summary["total_cost"] += cost
        summary["total_profit"] += profit

        revenue_per_product[r.product_name] = revenue_per_product.get(r.product_name, 0) + revenue
        profit_per_product[r.product_name] = profit_per_product.get(r.product_name, 0) + profit

        day = r.date.isoformat() if r.date else "unknown"
        sales_per_day[day] = sales_per_day.get(day, 0) + revenue

        pm = r.payment_method or "unknown"
        payment_methods[pm] = payment_methods.get(pm, 0) + 1

    analysis = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            **summary,
            "best_products_revenue": sorted(revenue_per_product.items(), key=lambda x: x[1], reverse=True)[:5],
            "best_products_profit": sorted(profit_per_product.items(), key=lambda x: x[1], reverse=True)[:5],
            "sales_per_day": sales_per_day,
            "payment_methods": payment_methods,
        },
    }

    return analysis


# -------- MAIN ROUTE --------
@router.post("/upload-sales")
async def upload_sales(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")

    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    required_fields = [
        "date",
        "product_name",
        "quantity",
        "cost_price",
        "selling_price",
        "payment_method",
        "mpesa_transaction_id",
    ]


    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV missing header row")

    reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

    # Ensure missing fields exist
    for field in required_fields:
        if field not in reader.fieldnames:
            reader.fieldnames.append(field)

    rows_to_insert = []

    for raw in reader:
        if not raw.get("product_name"):
            continue

        sale = Sale(
            date=to_date(raw.get("date")),
            product_name=to_str(raw.get("product_name")),
            quantity=to_int(raw.get("quantity")),
            cost_price=to_float(raw.get("cost_price")),
            selling_price=to_float(raw.get("selling_price")),
            payment_method=to_str(raw.get("payment_method")),
            mpesa_transaction_id=to_str(raw.get("mpesa_transaction_id"))
        )

        rows_to_insert.append(sale)

    # INSERT INTO DB
    async with async_session() as session:
        async with session.begin():
            session.add_all(rows_to_insert)

        # Load all rows to compute analysis
        result = await session.execute(select(Sale))
        all_rows = result.scalars().all()

    # COMPUTE ANALYSIS
    analysis_data = compute_analysis(all_rows)

    # SEND EMAIL (ONLY ANALYSIS, no CSV attachments)
    asyncio.create_task(
        send_report(
            subject="Sales Analysis Report",
            to="elizabethndinda41@gmail.com",
            analysis_data=analysis_data,
            attachments=[]
        )
    )

    return {
        "message": "Upload successful, analysis emailed",
        "inserted": len(rows_to_insert),
        "total_in_db": len(all_rows)
    }

