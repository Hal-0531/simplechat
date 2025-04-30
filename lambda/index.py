# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
import urllib.request
import ssl

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
bedrock_client = None

# FastAPI のエンドポイント
FASTAPI_ENDPOINT = "https://08d8-34-23-144-134.ngrok-free.app/chat"

# SSL証明書の検証を無効にする（自己署名証明書対応用）
ssl._create_default_https_context = ssl._create_unverified_context

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # ユーザー情報（オプション）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストのパース
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # FastAPI エンドポイントに送るデータ
        request_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }

        req = urllib.request.Request(
            url=FASTAPI_ENDPOINT,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        print("Sending request to FastAPI server...")

        # FastAPI にリクエストを送信
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read().decode("utf-8"))

        print("Received response from FastAPI:", json.dumps(response_body))

        # 応答の検証
        if "response" not in response_body:
            raise Exception("FastAPI response does not contain 'response' key")

        assistant_response = response_body["response"]

        # 会話履歴に追加
        conversation_history.append({
            "role": "user",
            "content": message
        })
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
