"""Pure-Python pipeline context. No Django/Celery imports here so the
pipeline stages can be unit-tested and reused outside the web app."""
from dataclasses import dataclass, field
from typing import Any, Optional

from PIL import Image


@dataclass
class PipelineParams:
    output_size_px: int = 2000
    padding_percent: float = 8.0
    output_format: str = "WEBP"
    output_quality: int = 90
    min_processing_edge_px: int = 1200
    prompt_template_text: Optional[str] = None

    qc_background_whiteness_tolerance: float = 6.0
    qc_centering_tolerance_percent: float = 2.5
    qc_min_product_coverage_percent: float = 15.0
    qc_max_product_coverage_percent: float = 95.0
    qc_identity_similarity_threshold: float = 0.80

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineParams":
        fields = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in fields and v is not None})


@dataclass
class PipelineContext:
    mode: str  # "recreate_studio" | "enhance_only"
    params: PipelineParams

    image: Optional[Image.Image] = None          # working RGB image, mutated stage to stage
    pre_ai_image: Optional[Image.Image] = None    # snapshot right before AI recreate, for identity QC
    post_ai_image: Optional[Image.Image] = None   # snapshot right after AI recreate, before bg removal overwrites ctx.image
    cutout_rgba: Optional[Image.Image] = None     # after background removal
    final_image: Optional[Image.Image] = None     # after square/center/pad
    export_bytes: Optional[bytes] = None
    export_checksum: str = ""

    detail: dict = field(default_factory=dict)   # accumulated per-stage metrics for logs + QC
    warnings: list = field(default_factory=list)
