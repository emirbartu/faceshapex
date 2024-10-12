import io
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Security, Request, BackgroundTasks
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
from faceshapex.face_shape_detector import FaceShapeDetector
import asyncpg
import uuid
from datetime import datetime, timedelta
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback  # Add this import

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

face_shape_detector = FaceShapeDetector()

# API key configuration
API_KEY = "fs_prod_your_api_key_here"  # Replace with a secure API key
API_KEY_NAME = "Authorization"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Database configuration
DATABASE_URL = "postgres://user_mmjwbpycud:rw9KIOXNheM3YYZEwvsR@devinapps-backend-prod.cluster-clussqewa0rh.us-west-2.rds.amazonaws.com/db_pmovtfhicd?sslmode=require"

async def get_database_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Database connection established successfully")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Error details: {type(e).__name__}, {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise

async def create_request_table():
    conn = await get_database_connection()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id UUID PRIMARY KEY,
            api_key TEXT UNIQUE,
            source TEXT,
            timestamp TIMESTAMP,
            request_count INTEGER
        )
    ''')
    await conn.close()

@app.on_event("startup")
async def startup_event():
    await create_request_table()
    asyncio.create_task(schedule_daily_report())

async def generate_daily_report():
    conn = await get_database_connection()
    yesterday = datetime.now() - timedelta(days=1)
    report = await conn.fetch('''
        SELECT api_key, COUNT(*) as request_count, array_agg(DISTINCT source) as sources
        FROM requests
        WHERE timestamp >= $1
        GROUP BY api_key
    ''', yesterday)
    await conn.close()
    return report

async def send_email_report(report):
    sender_email = "your_email@example.com"
    receiver_email = "admin@example.com"
    password = "your_email_password"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Daily API Usage Report"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = "Daily API Usage Report\n\n"
    html = "<html><body><h2>Daily API Usage Report</h2><table border='1'><tr><th>API Key</th><th>Request Count</th><th>Sources</th></tr>"

    for row in report:
        text += f"API Key: {row['api_key']}, Requests: {row['request_count']}, Sources: {', '.join(row['sources'])}\n"
        html += f"<tr><td>{row['api_key']}</td><td>{row['request_count']}</td><td>{', '.join(row['sources'])}</td></tr>"

    html += "</table></body></html>"

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

async def schedule_daily_report():
    while True:
        now = datetime.now()
        next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        report = await generate_daily_report()
        await send_email_report(report)

# Move the get_api_key function above the get_daily_report endpoint
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header and api_key_header.startswith("Bearer "):
        api_key = api_key_header.split(" ")[1]
        if api_key == API_KEY:
            return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

@app.get("/daily-report")
async def get_daily_report(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    report = await generate_daily_report()
    background_tasks.add_task(send_email_report, report)
    return {"message": "Daily report generated and sent via email", "report": report}

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header and api_key_header.startswith("Bearer "):
        api_key = api_key_header.split(" ")[1]
        if api_key == API_KEY:
            return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

async def log_request(api_key: str, source: str):
    conn = None
    try:
        print("Starting log_request function")
        conn = await get_database_connection()
        print("Database connection established")
        request_id = uuid.uuid4()
        timestamp = datetime.now()
        print(f"Attempting to log request: ID={request_id}, API Key={api_key}, Source={source}, Timestamp={timestamp}")

        # Check if the API key already exists
        existing_row = await conn.fetchrow('SELECT * FROM requests WHERE api_key = $1', api_key)
        print(f"Existing row: {existing_row}")

        if existing_row:
            # Update existing row
            result = await conn.fetchrow('''
                UPDATE requests
                SET request_count = request_count + 1, timestamp = $2, source = $3
                WHERE api_key = $1
                RETURNING request_count
            ''', api_key, timestamp, source)
        else:
            # Insert new row
            result = await conn.fetchrow('''
                INSERT INTO requests (id, api_key, source, timestamp, request_count)
                VALUES ($1, $2, $3, $4, 1)
                RETURNING request_count
            ''', str(request_id), api_key, source, timestamp)

        print(f"SQL query executed. Result: {result}")
        if result:
            request_count = result['request_count']
            print(f"Request logged successfully. ID: {request_id}, Count: {request_count}")
            return request_id, request_count
        else:
            print("Error: No result returned from database operation")
            return request_id, 0
    except Exception as e:
        print(f"Error logging request: {e}")
        print(f"Error details: {type(e).__name__}, {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return uuid.uuid4(), 0
    finally:
        if conn:
            await conn.close()
            print("Database connection closed")

@app.post("/detect-face-shape")
async def detect_face_shape(file: UploadFile = File(...), api_key: str = Depends(get_api_key), request: Request = Request):
    client_host = request.client.host
    print(f"Received request from {client_host} with API key: {api_key}")

    try:
        request_id, request_count = await log_request(api_key, client_host)
        print(f"Request logged with ID: {request_id}, Count: {request_count}")
    except Exception as e:
        print(f"Error logging request: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        request_id, request_count = uuid.uuid4(), 0

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = face_shape_detector.detect_face_shape(img)

    if result is None:
        return {"error": "No face detected in the image"}

    response = {
        "success": "true",
        "faces": [result],
        "request_count": request_count,
        "request_id": str(request_id)
    }
    print(f"Returning response: {response}")
    return response

def gradio_interface(image):
    result = face_shape_detector.detect_face_shape(image)
    if result is None:
        return "No face detected in the image"
    return str(result)

iface = gr.Interface(
    fn=gradio_interface,
    inputs=gr.Image(),
    outputs="text",
    title="Face Shape Detection",
    description="Upload an image to detect face shape and other features."
)

app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
