"""
src/core/__init__.py — Public interface for the core data layer.

Exposes the three primary domain classes so that external modules can import
them directly from ``src.core`` rather than navigating to the individual files:

    from src.core import PCBImage, SolderDefect, DetectionResult
"""
from .pcb_image import PCBImage
from .solder_defect import SolderDefect
from .detection_result import DetectionResult

__all__ = ["PCBImage", "SolderDefect", "DetectionResult"]
