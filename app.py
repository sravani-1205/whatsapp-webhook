from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import sqlite3
import os
import json
from datetime import datetime


# Load environment variables from .env
load_dotenv()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

app = FastAPI(
    title="WhatsApp Webhook Handler",
    version="1.0.0"
)


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

def get_db_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect("messages.db")
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    """Create the messages table if it doesn't already exist."""
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            sender TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT,
            timestamp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


create_database()


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "WhatsApp Webhook Handler is running"
    }


# ---------------------------------------------------------
# WhatsApp Webhook Verification
# ---------------------------------------------------------

@app.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    WhatsApp uses this endpoint to verify the webhook.

    If the verification token matches our environment variable,
    return the challenge. Otherwise return 403.
    """

    if hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Invalid verification token"
        )

    return hub_challenge or ""


# ---------------------------------------------------------
# Message Handlers
# ---------------------------------------------------------

def handle_text_message(sender, content):
    """Handle text messages."""
    print(f"[TEXT] Message from {sender}: {content}")


def handle_image_message(sender, content):
    """Handle image messages."""
    print(f"[IMAGE] Image received from {sender}: {content}")


def handle_unsupported_message(sender, message_type):
    """Handle message types that we don't currently support."""
    print(
        f"[UNSUPPORTED] Received '{message_type}' message "
        f"from {sender}"
    )


def process_message(sender, message_type, content):
    """
    Process the message in the background.

    Different message types have different handling paths.
    """

    if message_type == "text":
        handle_text_message(sender, content)

    elif message_type == "image":
        handle_image_message(sender, content)

    else:
        handle_unsupported_message(sender, message_type)


# ---------------------------------------------------------
# Extract WhatsApp Message
# ---------------------------------------------------------

def extract_messages(payload):
    """
    Safely extract messages from the WhatsApp nested structure:

    entry -> changes -> value -> messages
    """

    extracted_messages = []

    entries = payload.get("entry", [])

    if not isinstance(entries, list):
        return extracted_messages

    for entry in entries:

        if not isinstance(entry, dict):
            continue

        changes = entry.get("changes", [])

        if not isinstance(changes, list):
            continue

        for change in changes:

            if not isinstance(change, dict):
                continue

            value = change.get("value", {})

            if not isinstance(value, dict):
                continue

            messages = value.get("messages", [])

            if not isinstance(messages, list):
                continue

            for message in messages:

                if not isinstance(message, dict):
                    continue

                extracted_messages.append(message)

    return extracted_messages


# ---------------------------------------------------------
# POST Webhook
# ---------------------------------------------------------

@app.post("/webhook")
async def receive_webhook(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """
    Receive WhatsApp messages.

    The message is stored first and actual processing is
    scheduled as a background task.
    """

    try:
        messages = extract_messages(payload)

        # Malformed or incomplete payload
        if not messages:
            return {
                "status": "ignored",
                "message": "No valid WhatsApp messages found"
            }

        processed_count = 0
        duplicate_count = 0

        connection = get_db_connection()

        for message in messages:

            message_id = message.get("id")
            sender = message.get("from")
            message_type = message.get("type")

            # A valid WhatsApp message needs these fields
            if not message_id or not sender or not message_type:
                continue

            # -------------------------------------------------
            # Extract content based on message type
            # -------------------------------------------------

            content = None

            if message_type == "text":

                text_data = message.get("text", {})

                if isinstance(text_data, dict):
                    content = text_data.get("body")

            elif message_type == "image":

                image_data = message.get("image", {})

                if isinstance(image_data, dict):

                    image_id = image_data.get("id")
                    caption = image_data.get("caption")

                    content = json.dumps({
                        "image_id": image_id,
                        "caption": caption
                    })

            else:
                # Store unsupported message information
                content = json.dumps(message)

            timestamp = message.get("timestamp")

            # -------------------------------------------------
            # Idempotency
            # -------------------------------------------------

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO messages
                (
                    message_id,
                    sender,
                    message_type,
                    content,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    sender,
                    message_type,
                    content,
                    timestamp
                )
            )

            # rowcount = 1 means a new message was inserted
            # rowcount = 0 means the message_id already existed
            if cursor.rowcount == 0:
                duplicate_count += 1
                continue

            processed_count += 1

            # -------------------------------------------------
            # Background processing
            # -------------------------------------------------

            background_tasks.add_task(
                process_message,
                sender,
                message_type,
                content
            )

        connection.commit()
        connection.close()

        return {
            "status": "accepted",
            "processed": processed_count,
            "duplicates": duplicate_count
        }

    except Exception as error:

        print(f"Webhook error: {error}")

        # We don't want malformed webhook requests to crash
        # the application.
        return {
            "status": "error",
            "message": "Webhook payload could not be processed"
        }


# ---------------------------------------------------------
# Get Stored Messages
# ---------------------------------------------------------

@app.get("/messages")
def get_messages(
    sender: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve stored messages.

    Optional sender filter:
        /messages?sender=919876543210

    Pagination:
        /messages?page=1&limit=10
    """

    connection = get_db_connection()

    offset = (page - 1) * limit

    if sender:

        total_cursor = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM messages
            WHERE sender = ?
            """,
            (sender,)
        )

        total = total_cursor.fetchone()["total"]

        cursor = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE sender = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (sender, limit, offset)
        )

    else:

        total_cursor = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM messages
            """
        )

        total = total_cursor.fetchone()["total"]

        cursor = connection.execute(
            """
            SELECT *
            FROM messages
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

    messages = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "messages": messages
    }