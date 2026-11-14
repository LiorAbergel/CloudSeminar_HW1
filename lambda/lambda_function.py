import base64
import json
import os
import time

import boto3
from boto3.dynamodb.conditions import Key
from openai import OpenAI

client = OpenAI() 
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
table = boto3.resource("dynamodb").Table("chat-history")
HISTORY_LIMIT = 6

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def response(status, body):
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def get_method(event):
    # Function URL puts the method here; the Lambda Test tab sends no requestContext
    method = event.get("requestContext", {}).get("http", {}).get("method")
    return (method or "POST").upper()


def parse_body(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    return json.loads(body) if isinstance(body, str) else body


def get_history(user_id):
    """Last HISTORY_LIMIT messages for this user, oldest first."""
    result = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,  # newest first
        Limit=HISTORY_LIMIT,
    )
    items = reversed(result.get("Items", []))
    return [{"role": i["role"], "content": i["content"]} for i in items]


def save_messages(user_id, user_prompt, ai_reply):
    now_ms = int(time.time() * 1000)
    with table.batch_writer() as batch:
        batch.put_item(Item={"user_id": user_id, "timestamp": now_ms,
                             "role": "user", "content": user_prompt})
        batch.put_item(Item={"user_id": user_id, "timestamp": now_ms + 1,
                             "role": "assistant", "content": ai_reply})


def lambda_handler(event, context):
    method = get_method(event)
    if method == "OPTIONS":  # CORS preflight
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}
    if method != "POST":
        return response(405, {"error": f"Method {method} not allowed, use POST"})

    try:
        data = parse_body(event)
    except (json.JSONDecodeError, ValueError):
        return response(400, {"error": "Body must be valid JSON"})

    user_prompt = (data.get("user_prompt") or "").strip()
    if not user_prompt:
        return response(400, {"error": "Missing field: user_prompt"})
    user_id = data.get("user_id") or "anonymous"  # Test tab sends no user_id

    messages = get_history(user_id) + [{"role": "user", "content": user_prompt}]

    start = time.perf_counter()
    try:
        ai = client.responses.create(model=MODEL, input=messages)
    except Exception as e:
        return response(502, {"error": f"OpenAI error: {e}"})
    openai_ms = round((time.perf_counter() - start) * 1000)

    ai_reply = ai.output_text
    save_messages(user_id, user_prompt, ai_reply)

    return response(200, {
        "ai_reply": ai_reply,
        "openai_response_time_ms": openai_ms,
    })