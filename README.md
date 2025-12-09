Sales Analysis Automation Backend

This project processes sales CSV files, analyzes them, saves structured results, and automatically emails daily reports. It is built with FastAPI, SQLAlchemy, async workflows, and a small analytics engine.

 Features

Upload sales CSV files through an API

Cleans and validates messy CSV data

Stores sales records in a database

Generates:

Revenue per product

Profit per product

Sales per day

Full JSON analysis reports

Automatically emails daily reports

Environment-based configuration 

  Project Structure

app/
  main.py                # FastAPI entrypoint
  database/              # DB setup + session
  models/                # SQLAlchemy models
  routers/               # API routes
  services/              # Analysis logic
  utils/                 # Email + helper utilities
data/                    # Generated analysis outputs

  Setup Instructions

1. Clone the repository

git clone <your-repo-url>
cd backend_project

2. Create a virtual environment

python3 -m venv venv
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Create a .env file

The .env file is not committed and must be created manually:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password



▶  Running the App

Start the server:

uvicorn app.main:app --reload

Access docs:

http://127.0.0.1:8000/docs

  Testing

pytest 

 Daily Email Reports

The automatic email sender:

Collects the latest analysis results

Formats them into an email

Sends them using SMTP settings from .env

  Author

Built by Elizabeth Ndinda.

  License

MIT License .


