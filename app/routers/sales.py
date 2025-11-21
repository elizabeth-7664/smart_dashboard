import csv
import io
from fastapi import APIRouter, UploadFile, HTTPException
from app.database.setup import async_session
from app.models.sales import Sale
from datetime import datetime
from sqlalchemy import select

router = APIRouter()

# ---------- SAFE CAST UTILITIES ----------
def to_int(val): 
    try: 
        return int(val)
    except (ValueError, TypeError): 
        return 0

def to_float(val): 
    try: 
        return float(val)
    except (ValueError, TypeError): 
        return 0.0

def to_str(val):
    if val is None: 
        return ""
    return str(val).strip()

def to_date(val):
    if not val:
        return None
    try:
        # assuming format "YYYY-MM-DD"
        return datetime.strptime(val, "%Y-%m-%d").date()
    except:
        return None
# ---------- MAIN ROUTE ----------
@router.post("/upload-sales")
async def upload_sales(file: UploadFile):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Must upload a CSV file.")

    # Read CSV safely (handles BOM characters from Excel)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file is empty or malformed.")

    # Normalize headers: strip spaces and lowercase
    reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

    # Columns your model expects
    required_fields = [
        "date",
        "product_name",
        "quantity",
        "cost_price",
        "selling_price",
        "payment_method",
        "mpesa_transaction_id"
    ]

    # Verify all required columns exist, add missing ones as None
    for field in required_fields:
        if field not in reader.fieldnames:
            reader.fieldnames.append(field)

    rows_to_insert = []

    for raw_row in reader:
        # Guarantee all required keys exist
        row = {key: raw_row.get(key, None) for key in required_fields}

        # Skip completely empty rows
        if not row["date"] and not row["product_name"]:
            continue

        sale = Sale(
            date=to_date(row["date"]),
            product_name=to_str(row["product_name"]),
            quantity=to_int(row["quantity"]),
            cost_price=to_float(row["cost_price"]),
            selling_price=to_float(row["selling_price"]),
            payment_method=to_str(row["payment_method"]),
            mpesa_transaction_id=to_str(row["mpesa_transaction_id"])
        )

        rows_to_insert.append(sale)

    # Insert to database
    async with async_session() as session:
      async with session.begin():
        session.add_all(rows_to_insert)


        # Count rows after insert
        result = await session.execute(select(Sale))
        total_rows = len(result.scalars().all())

    return {
        "message": "Upload successful",
        "inserted": len(rows_to_insert),
        "ignored_empty_rows": len([r for r in rows_to_insert if r.product_name == ""]),
        "total_rows_in_db": total_rows
    }
 
