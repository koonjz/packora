"""
Packora CV Client — optional MobileNetV3 commodity identification
=================================================================

FEATURE FLAG: This module is only active when ENABLE_CV_FEATURE=true.
When the flag is false, identify_commodity() returns None immediately
and the system falls back to commodity_id supplied in the request.

DESIGN CONTRACT (per PROJECT_BRIEF.md §2.2 and §3):
  - This feature MUST NOT block or crash the core recommendation flow.
  - Returns None on any error (flag off, model not loaded, low confidence, exception).
  - Model file: backend/app/cv/mobilenetv3_packora.pt (tracked via Git LFS, not pip).
  - Confidence threshold is configurable via CV_CONFIDENCE_THRESHOLD in .env.
"""
from __future__ import annotations

import base64
import io
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_class_names: list[str] = []


def _load_model():
    """Load the fine-tuned MobileNetV3 model. Called lazily on first use."""
    global _model, _class_names
    if _model is not None:
        return _model

    if not settings.enable_cv_feature:
        return None

    model_path = settings.cv_model_path
    try:
        import json
        from pathlib import Path

        import torch
        import torchvision.models as models

        # Load class names (expected alongside the model file as mobilenetv3_classes.json)
        classes_path = Path(model_path).with_suffix("").with_name(
            Path(model_path).stem + "_classes.json"
        )
        if classes_path.exists():
            with open(classes_path) as f:
                _class_names = json.load(f)

        num_classes = len(_class_names) if _class_names else 100
        model = models.mobilenet_v3_small(pretrained=False)
        model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, num_classes)
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        _model = model
        logger.info("CV model loaded from %s (%d classes)", model_path, num_classes)
        return _model
    except Exception as exc:  # noqa: BLE001
        logger.warning("CV model failed to load (%s: %s) — CV feature disabled", type(exc).__name__, exc)
        return None


async def identify_commodity(image_b64: str | None) -> str | None:
    """
    Attempt to identify the commodity from a base64-encoded image.

    Returns the commodity name string on confident identification,
    or None if the flag is off, image is missing, model not loaded,
    or confidence is below threshold.
    """
    if not settings.enable_cv_feature:
        return None
    if not image_b64:
        return None

    model = _load_model()
    if model is None:
        return None

    try:
        import torch
        import torchvision.transforms as T
        from PIL import Image

        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, class_idx = torch.max(probs, dim=1)

        confidence_val = float(confidence.item())
        if confidence_val < settings.cv_confidence_threshold:
            logger.info(
                "CV confidence %.2f below threshold %.2f — returning None",
                confidence_val,
                settings.cv_confidence_threshold,
            )
            return None

        if _class_names:
            return _class_names[int(class_idx.item())]
        return f"commodity_class_{int(class_idx.item())}"

    except Exception as exc:  # noqa: BLE001
        logger.warning("CV inference failed (%s: %s) — returning None", type(exc).__name__, exc)
        return None
