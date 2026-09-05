#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
verifier="$project_root/scripts/verify-a2a-1.0.1-sources.sh"
test_root=$(mktemp -d "${TMPDIR:-/tmp}/agsdl-a2a-verifier.XXXXXX")
test_project="$test_root/project"
source_tree="$test_root/source"

trap 'rm -rf "$test_root"' EXIT

mkdir -p \
  "$test_project/docs/research" \
  "$test_project/scripts" \
  "$source_tree/docs" \
  "$source_tree/specification"
cp "$verifier" "$test_project/scripts/verify-a2a-1.0.1-sources.sh"

write_fixture() {
  cat >"$source_tree/docs/specification.md" <<'EOF'
# Synthetic A2A specification fixture
EOF

  cat >"$source_tree/docs/whats-new-v1.md" <<'EOF'
# Synthetic A2A migration fixture
EOF

  cat >"$source_tree/specification/a2a.proto" <<'EOF'
service A2AService {}
message AgentCard {}
message AgentInterface {}
message AgentSkill {}
message Task {}
message Message {}
message Artifact {}
message TaskStatusUpdateEvent {}
message TaskArtifactUpdateEvent {}
message AgentExtension {}
message SecurityScheme {}
TASK_STATE_COMPLETED
TASK_STATE_FAILED
TASK_STATE_CANCELED
TASK_STATE_REJECTED
TASK_STATE_INPUT_REQUIRED
TASK_STATE_AUTH_REQUIRED
EOF
}

write_manifest() {
  (
    cd "$source_tree"
    shasum -a 256 \
      docs/specification.md \
      specification/a2a.proto \
      docs/whats-new-v1.md
  ) >"$test_project/docs/research/a2a-v1.0.1.sha256"
}

write_fixture
write_manifest
"$test_project/scripts/verify-a2a-1.0.1-sources.sh" "$source_tree" >/dev/null

printf '\ntampered\n' >>"$source_tree/docs/specification.md"
if "$test_project/scripts/verify-a2a-1.0.1-sources.sh" "$source_tree" \
  >/dev/null 2>&1; then
  echo "Verifier accepted a source file with a mismatched digest." >&2
  exit 1
fi

write_fixture
grep -Fv 'TASK_STATE_AUTH_REQUIRED' "$source_tree/specification/a2a.proto" \
  >"$source_tree/specification/a2a.proto.tmp"
mv "$source_tree/specification/a2a.proto.tmp" "$source_tree/specification/a2a.proto"
write_manifest
if "$test_project/scripts/verify-a2a-1.0.1-sources.sh" "$source_tree" \
  >/dev/null 2>&1; then
  echo "Verifier accepted a source tree without a reviewed declaration." >&2
  exit 1
fi

echo "A2A source verifier tests passed."
