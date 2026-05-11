import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    artifact_dir = Path(os.environ["NETOPS_ARTIFACT_DIR"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "title": "AWS Architecture Diagram",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "operator": os.getenv("NETOPS_OPERATOR", "unknown"),
        "profile": os.getenv("AWS_PROFILE", "unset"),
        "message": "Replace this sample with boto3 inventory and diagram generation.",
        "nodes": [
            {"id": "vpc", "label": "VPC"},
            {"id": "subnets", "label": "Subnets"},
            {"id": "ec2", "label": "EC2 Instances"}
        ],
        "edges": [
            {"from": "vpc", "to": "subnets"},
            {"from": "subnets", "to": "ec2"}
        ]
    }

    output_path = artifact_dir / "aws-architecture-diagram.json"
    output_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
