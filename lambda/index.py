import json
import urllib.request
import ssl

# FastAPI のエンドポイント (あなたの API URL に変更)
FASTAPI_ENDPOINT = "https://dfe8-34-23-144-134.ngrok-free.app/"

# SSL 証明書の検証を無効化 (必要に応じて)
ssl._create_default_https_context = ssl._create_unverified_context

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # リクエストのパース
        body = json.loads(event['body'])
        message = body['message']

        print("Processing message:", message)

        # FastAPI エンドポイントに送るデータ
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
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
        assistant_response = response_body.get("generated_text", "応答なし")

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
