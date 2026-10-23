"""Radar domain exceptions."""


class RadarError(Exception):
    """Base exception for all Radar operations."""


class ConfigurationError(RadarError):
    """Raised when environment or pipeline configuration is invalid."""


class ValidationError(RadarError):
    """Raised when schema validation or parsing fails."""


class ProviderError(RadarError):
    """Raised when an LLM or embedding provider fails."""


class IngestionError(RadarError):
    """Raised when data ingestion from a source fails."""


class PipelineExecutionError(RadarError):
    """Raised when a stage in the processing DAG fails."""
