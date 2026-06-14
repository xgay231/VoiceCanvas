import base64
import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

load_dotenv()

app = FastAPI(title="VoiceCanvas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.environ.get("MIMO_API_KEY", ""),
    base_url=os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
)


@app.get("/")
def read_root():
    return {"message": "VoiceCanvas API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/asr")
async def transcribe(audio: UploadFile):
    try:
        audio_bytes = await audio.read()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        completion = client.chat.completions.create(
            model="mimo-v2.5-asr",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:audio/wav;base64,{audio_base64}"
                            },
                        }
                    ],
                }
            ],
            extra_body={"asr_options": {"language": "zh"}},
        )
        return {"text": completion.choices[0].message.content, "success": True}
    except Exception as e:
        return {"text": "", "success": False, "error": str(e)}
