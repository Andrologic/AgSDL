#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 PATH_TO_A2A_V1_0_1_SOURCE_TREE" >&2
  exit 2
fi

source_root=$1
project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
manifest="$project_root/docs/research/a2a-v1.0.1.sha256"

if [[ ! -d "$source_root" ]]; then
  echo "A2A source directory does not exist: $source_root" >&2
  exit 2
fi

(
  cd "$source_root"
  shasum -a 256 -c "$manifest"
)

proto="$source_root/specification/a2a.proto"

required_proto_declarations=(
  'service A2AService'
  'message AgentCard'
  'message AgentInterface'
  'message AgentSkill'
  'message Task'
  'message Message'
  'message Artifact'
  'message TaskStatusUpdateEvent'
  'message TaskArtifactUpdateEvent'
  'message AgentExtension'
  'message SecurityScheme'
  'TASK_STATE_COMPLETED'
  'TASK_STATE_FAILED'
  'TASK_STATE_CANCELED'
  'TASK_STATE_REJECTED'
  'TASK_STATE_INPUT_REQUIRED'
  'TASK_STATE_AUTH_REQUIRED'
)

for declaration in "${required_proto_declarations[@]}"; do
  if ! grep -Fq "$declaration" "$proto"; then
    echo "Missing reviewed A2A declaration: $declaration" >&2
    exit 1
  fi
done

echo "A2A v1.0.1 pinned file contents and reviewed declarations verified."
