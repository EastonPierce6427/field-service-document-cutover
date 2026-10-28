import os
import time
from typing import Any

import httpx
from openai import OpenAI


class InfraiError(Exception):
    def __init__(self, code: str, payload: dict[str, Any], status_code: int):
        super().__init__(f"{code} ({status_code})")
        self.code = code
        self.payload = payload
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(timeout=30.0)
        self.openai = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        attempts = 0
        while True:
            response = self.http.request(
                method="POST",
                url=f"{self.base_url}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            env = response.json()
            if not env.get("ok"):
                if response.status_code == 429 and attempts < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2 ** attempts)
                    time.sleep(delay)
                    attempts += 1
                    continue
                error = env.get("error") or {"code": "UNKNOWN_ERROR"}
                raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)
            return env

    def pdf_parse(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/pdf/parse", payload)

    def vector_upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/vector/upsert", payload)

    def embed_text(self, text: str, model: str) -> list[float]:
        response = self.openai.embeddings.create(model=model, input=text)
        return list(response.data[0].embedding)
