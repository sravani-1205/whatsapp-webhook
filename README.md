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
├── README.md
│
├── .env              # Hided
├── messages.db       # Hided 
└── venv/             # Hided

## Live Deployment

The application is deployed on Render.

Live URL:
https://whatsapp-webhook-1t2g.onrender.com

Swagger API Documentation:
https://whatsapp-webhook-1t2g.onrender.com/docs