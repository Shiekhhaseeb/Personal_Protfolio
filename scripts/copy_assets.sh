#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/app/static/images"
mkdir -p "$ROOT/app/static/resume"
cp "$ROOT/ProfilePIc.jpeg" "$ROOT/app/static/images/profile.jpeg"
if [ -f "$ROOT/Resume.pdf" ]; then
  cp "$ROOT/Resume.pdf" "$ROOT/app/static/resume/Sheikh_Haseeb_Resume.pdf"
fi
echo "Copied profile image and resume assets"
