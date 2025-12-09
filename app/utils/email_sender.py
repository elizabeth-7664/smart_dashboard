import smtplib
import ssl
import os
import json
from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()

SMTP_SERVER = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT"))
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASSWORD")

print("=== EMAIL DEBUG ===")
print("SMTP_SERVER:", SMTP_SERVER)
print("SMTP_PORT:", SMTP_PORT)
print("SMTP_USER:", SMTP_USER)
print("SMTP_PASS:", SMTP_PASS)
print("===================")

def build_human_readable_report(analysis):
    """Generate human-readable text summary."""
    return f"""
SALES ANALYSIS REPORT

Generated at: {analysis.get('generated_at', 'N/A')}

-- SUMMARY --
Total Revenue: {analysis['summary'].get('total_revenue', 0)}
Total Cost: {analysis['summary'].get('total_cost', 0)}
Total Profit: {analysis['summary'].get('total_profit', 0)}
Transactions: {analysis['summary'].get('transactions', 0)}

-- BEST PRODUCTS (Revenue) --
{json.dumps(analysis['summary'].get('best_products_revenue', {}), indent=2)}

-- BEST PRODUCTS (Profit) --
{json.dumps(analysis['summary'].get('best_products_profit', {}), indent=2)}

-- SALES PER DAY --
{json.dumps(analysis['summary'].get('sales_per_day', {}), indent=2)}

-- PAYMENT METHODS --
{json.dumps(analysis['summary'].get('payment_methods', {}), indent=2)}
"""


async def send_report(subject, to, analysis_data=None, body=None, attachments=None):
    """Send an email report with optional attachments."""
    if attachments is None:
        attachments = []

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject

    # Build email body
    if analysis_data:
        readable = build_human_readable_report(analysis_data)
        json_part = json.dumps(analysis_data, indent=2)
        full_body = f"{readable}\n\n--- RAW JSON SUMMARY ---\n{json_part}"
        msg.set_content(full_body)
    else:
        msg.set_content(body or "No analysis available.")

    # Attach files if any
    for filepath in attachments:
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(filepath)
                )

    # Send email
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print("Failed to send email:", e)
