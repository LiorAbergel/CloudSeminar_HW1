# Exercise 1: Serverless Chatbot with AWS Lambda and OpenAI API

## Links
- Lambda Function URL: https://2fdl56o2kppjedibpmzbaetuay0hvzec.lambda-url.us-east-1.on.aws/
- Amplify live site: https://main.d14kumdsv47azd.amplifyapp.com/

## Architecture
Browser (Amplify) -> Lambda Function URL -> Lambda (open-ai-chatbot)
  -> OpenAI Responses API, and DynamoDB (chat-history) for the last 6 messages

## Lambda
- Runtime: Python 3.12, role: LabRole, timeout: 30s
- Input: POST JSON {"user_prompt": "...", "user_id": "..."}
- Output: {"ai_reply": "...", "openai_response_time_ms": 1234}
- Non-POST methods return 405; OPTIONS returns 200 with CORS headers
- OPENAI_API_KEY is stored as a Lambda environment variable (not in the repo)

## DynamoDB
- Table: chat-history
- Partition key: user_id (String)
- Sort key: timestamp (Number, epoch ms)
- Attributes: role (user / assistant), content (message text)
- Each request reads the last 6 messages and writes the user message and the AI reply

## Response times
- OpenAI API time: measured in Lambda around client.responses.create
- Total request time: measured in the browser around fetch
- Shown as a Chart.js line chart with averages, kept for the browser session only

## Screenshots
See /screenshots