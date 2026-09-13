# WhatsApp Webhook Handler - FastAPI

A simple production-style WhatsApp Cloud API webhook handler built using FastAPI and SQLite.

The service receives WhatsApp webhook events, extracts incoming messages, prevents duplicate processing, stores messages in SQLite, and processes supported message types in the background.

## Features

- FastAPI-based webhook service
- WhatsApp webhook verification
- Handles text messages
- Handles image messages
- Handles unsupported message types
- Idempotency using WhatsApp `message_id`
- Background message processing
- SQLite message storage
- Sender-based message filtering
- Pagination
- Handles malformed or incomplete webhook payloads safely

## Technologies Used

- Python 3.11+
- FastAPI
- Uvicorn
- SQLite
- python-dotenv

## Project Structure

```text
whatsapp-webhook/
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/sravani-1205/whatsapp-webhook.git
cd whatsapp-webhook
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create `.env`

Create a `.env` file in the project root:

```text
WHATSAPP_VERIFY_TOKEN=your_secret_token
```

### 6. Start the application

```bash
uvicorn app:app --reload
```

The application will run at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API Testing with curl

### 1. Check the application

```bash
curl http://127.0.0.1:8000/
```

### 2. Verify the WhatsApp webhook

Replace `your_secret_token` with the value configured in your `.env` file.

```bash
curl "http://127.0.0.1:8000/webhook?hub.mode=subscribe&hub.verify_token=your_secret_token&hub.challenge=123456"
```

Expected response:

```text
123456
```

### 3. Send a text message

```bash
curl -X POST "http://127.0.0.1:8000/webhook" ^
-H "Content-Type: application/json" ^
-d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"919876543210\",\"id\":\"wamid.TEST001\",\"timestamp\":\"1725000000\",\"type\":\"text\",\"text\":{\"body\":\"Hello from curl\"}}]}}]}]}"
```

### 4. Send an image message

```bash
curl -X POST "http://127.0.0.1:8000/webhook" ^
-H "Content-Type: application/json" ^
-d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"919876543210\",\"id\":\"wamid.IMAGE001\",\"timestamp\":\"1725000000\",\"type\":\"image\",\"image\":{\"id\":\"image_media_123\",\"caption\":\"Test image\"}}]}}]}]}"
```

### 5. Send an unsupported message

```bash
curl -X POST "http://127.0.0.1:8000/webhook" ^
-H "Content-Type: application/json" ^
-d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"919876543210\",\"id\":\"wamid.AUDIO001\",\"timestamp\":\"1725000000\",\"type\":\"audio\",\"audio\":{\"id\":\"audio_123\"}}]}}]}]}"
```

### 6. Get stored messages

```bash
curl "http://127.0.0.1:8000/messages?page=1&limit=10"
```

### 7. Get messages by sender

```bash
curl "http://127.0.0.1:8000/messages?sender=919876543210&page=1&limit=10"
```

## Live Deployment

The application is deployed on Render.

Live URL:

https://whatsapp-webhook-1t2g.onrender.com

Swagger API Documentation:

https://whatsapp-webhook-1t2g.onrender.com/docs