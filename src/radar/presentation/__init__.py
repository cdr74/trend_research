"""Presentation layer exports and interfaces."""

from radar.presentation.projection import project_embeddings_to_2d
from radar.presentation.report import MarkdownReportGenerator

__all__ = ["MarkdownReportGenerator", "project_embeddings_to_2d"]
