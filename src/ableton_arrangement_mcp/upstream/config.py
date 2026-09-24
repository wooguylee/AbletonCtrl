"""AbletonCtrl addition: optional backend settings, supplied only by the operator.

No upstream hosted service credentials are bundled. See doc/compatibility.md.
"""
import os
from dataclasses import dataclass


@dataclass
class TelemetryConfig:
    supabase_url: str = os.environ.get("ABLETON_MCP_SUPABASE_URL", "")
    supabase_anon_key: str = os.environ.get("ABLETON_MCP_SUPABASE_ANON_KEY", "")
    enabled: bool = os.environ.get("ABLETONCTRL_ENABLE_COLLECTION", "").lower() in {"1", "true", "yes"}
    timeout: float = 1.5
    max_prompt_length: int = 1000

    @property
    def has_credentials(self):
        return bool(self.supabase_url and self.supabase_anon_key)


telemetry_config = TelemetryConfig()
