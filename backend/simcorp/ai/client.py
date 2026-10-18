"""Client for communicating with LM Studio / local OpenAI-compatible endpoints."""
from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from simcorp.models.ai_schemas import AIConfigModel, AIHealthStatus, ManagerProposal

class LMStudioClient:
    def __init__(self, config: AIConfigModel):
        self.config = config

    def check_health(self) -> AIHealthStatus:
        """Tests connection to LM Studio and fetches available models."""
        url = f"{self.config.base_url.rstrip('/')}/models"
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return AIHealthStatus(
                        connected=True,
                        provider=self.config.provider,
                        base_url=self.config.base_url,
                        model_id=self.config.model_id,
                        models_available=models
                    )
                return AIHealthStatus(
                    connected=False,
                    provider=self.config.provider,
                    base_url=self.config.base_url,
                    model_id=self.config.model_id,
                    error_message=f"HTTP {res.status_code}: {res.text[:100]}"
                )
        except Exception as e:
            return AIHealthStatus(
                connected=False,
                provider=self.config.provider,
                base_url=self.config.base_url,
                model_id=self.config.model_id,
                error_message=str(e)
            )

    def request_decision(self, system_prompt: str, user_prompt: str) -> Optional[ManagerProposal]:
        """Calls LM Studio's /chat/completions endpoint and parses structured JSON proposal."""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.config.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 800
        }

        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    print(f"[LM Studio Error]: HTTP {res.status_code} - {res.text[:150]}")
                    return None

                response_json = res.json()
                content = response_json["choices"][0]["message"]["content"]
                return self._parse_json_proposal(content)
        except Exception as e:
            print(f"[LM Studio Request Failed]: {e}")
            return None

    def _parse_json_proposal(self, raw_text: str) -> Optional[ManagerProposal]:
        """Extracts JSON block even if model includes markdown code fencing or reasoning preamble."""
        clean_text = raw_text.strip()
        # Find json markdown block ```json ... ``` or first { ... }
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            first_brace = clean_text.find("{")
            last_brace = clean_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = clean_text[first_brace:last_brace + 1]
            else:
                return None

        try:
            data = json.loads(json_str)
            return ManagerProposal(**data)
        except Exception as err:
            print(f"[JSON Parse Error]: {err} for content:\n{raw_text[:200]}")
            return None
