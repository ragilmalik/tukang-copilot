"""Settings, read from environment variables or a `.env` file in the repo root (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:  # pragma: no cover - dotenv is optional
    pass


def _env(*names: str, default: str = "") -> str:
    for n in names:
        v = os.getenv(n)
        if v is not None and v.strip():
            return v.strip()
    return default


def _flag(*names: str, default: str = "0") -> bool:
    return _env(*names, default=default).lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    """All runtime configuration. Every field can be overridden by an environment variable."""

    # Meta Model API (https://dev.meta.ai/docs/authentication). Docs name the key MODEL_API_KEY.
    meta_api_key: str = field(default_factory=lambda: _env("META_API_KEY", "MODEL_API_KEY"))
    meta_api_base: str = field(
        default_factory=lambda: _env("META_API_BASE", default="https://api.meta.ai/v1").rstrip("/")
    )

    # Model ids, verified on https://dev.meta.ai/docs/models (2026-10-30). See docs/META_API_NOTES.md.
    asr_model: str = field(default_factory=lambda: _env("ASR_MODEL", default="muse-voice-transcribe-1.0"))
    audio_model: str = field(default_factory=lambda: _env("AUDIO_MODEL", default="muse-spark-1.2"))
    vision_model: str = field(default_factory=lambda: _env("VISION_MODEL", default="muse-spark-1.3"))
    reason_model: str = field(default_factory=lambda: _env("REASON_MODEL", default="muse-spark-1.3"))
    image_model: str = field(default_factory=lambda: _env("IMAGE_MODEL", default="muse-image-1.0"))
    sam_model: str = field(default_factory=lambda: _env("SAM_MODEL", default="sam-3.1"))

    # Open weights: Muse Spark Open on Baseten (https://dev.meta.ai/docs/muse-spark-open/deploy#baseten)
    use_open_weights: bool = field(default_factory=lambda: _flag("USE_OPEN_WEIGHTS"))
    baseten_api_key: str = field(default_factory=lambda: _env("BASETEN_API_KEY"))
    open_api_base: str = field(
        default_factory=lambda: _env("OPEN_API_BASE", default="https://inference.baseten.co/v1").rstrip("/")
    )
    open_model: str = field(default_factory=lambda: _env("OPEN_MODEL", default="meta-models/muse-spark-open"))

    # Behaviour
    mock: bool = field(default_factory=lambda: _flag("MOCK", "DEMO_MODE"))
    demo_mode: bool = field(default_factory=lambda: _flag("DEMO_MODE"))
    illustrate: bool = field(default_factory=lambda: _flag("ILLUSTRATE", default="1"))
    max_diagrams: int = field(default_factory=lambda: int(_env("MAX_DIAGRAMS", default="2")))
    max_cost_usd: float = field(default_factory=lambda: float(_env("MAX_COST_PER_SESSION_USD", default="0.50")))
    rate_limit_per_hour: int = field(default_factory=lambda: int(_env("RATE_LIMIT_PER_HOUR", default="30")))
    daily_budget_usd: float = field(default_factory=lambda: float(_env("DAILY_BUDGET_USD", default="10")))
    max_image_side: int = field(default_factory=lambda: int(_env("MAX_IMAGE_SIDE", default="1536")))
    retention_hours: float = field(default_factory=lambda: float(_env("RETENTION_HOURS", default="24")))
    max_check_fails: int = field(default_factory=lambda: int(_env("MAX_CHECK_FAILS", default="2")))
    diagram_checker: bool = field(default_factory=lambda: _flag("DIAGRAM_CHECKER", default="1"))
    narration_voice: bool = field(default_factory=lambda: _flag("NARRATION_VOICE", default="1"))
    # Live guide (camera overlay): SAM 3.1 on ~1 frame per second, capped per repair to keep cost bounded.
    max_track_frames: int = field(default_factory=lambda: int(_env("MAX_TRACK_FRAMES", default="120")))
    track_min_interval_s: float = field(default_factory=lambda: float(_env("TRACK_MIN_INTERVAL_S", default="0.6")))

    # Storage and web
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", default=str(ROOT / "data"))))
    public_base_url: str = field(default_factory=lambda: _env("PUBLIC_BASE_URL").rstrip("/"))
    cors_origins: str = field(default_factory=lambda: _env("CORS_ORIGINS", default="*"))

    @property
    def offline(self) -> bool:
        """True when no Meta key is set or MOCK=1: the whole app runs on canned fixtures, free."""
        return self.mock or not self.meta_api_key

    @property
    def open_weights_active(self) -> bool:
        return self.use_open_weights and bool(self.baseten_api_key)

    @property
    def mode(self) -> str:
        return "mock" if self.offline else "live"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
