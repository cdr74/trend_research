"""Export JSON Schemas from Pydantic models for contract distribution."""

import json
from pathlib import Path

from radar.core.models import EnterpriseEvaluation, RadarItem, SignalDossier, TrendTopic


def export_schemas() -> None:
    schema_dir = Path("docs/schemas")
    schema_dir.mkdir(parents=True, exist_ok=True)

    # Signal schema
    signal_schema = RadarItem.model_json_schema()
    signal_schema["$id"] = "https://radar.internal/schemas/signal.schema.json"
    (schema_dir / "signal.schema.json").write_text(json.dumps(signal_schema, indent=2))

    # Topic schema
    topic_schema = TrendTopic.model_json_schema()
    topic_schema["$id"] = "https://radar.internal/schemas/topic.schema.json"
    (schema_dir / "topic.schema.json").write_text(json.dumps(topic_schema, indent=2))

    # Dossier schema
    dossier_schema = SignalDossier.model_json_schema()
    dossier_schema["$id"] = "https://radar.internal/schemas/dossier.schema.json"
    (schema_dir / "dossier.schema.json").write_text(json.dumps(dossier_schema, indent=2))

    # Evaluation schema
    eval_schema = EnterpriseEvaluation.model_json_schema()
    eval_schema["$id"] = "https://radar.internal/schemas/evaluation.schema.json"
    (schema_dir / "evaluation.schema.json").write_text(json.dumps(eval_schema, indent=2))

    print(f"Schemas successfully exported to {schema_dir}/")


if __name__ == "__main__":
    export_schemas()
