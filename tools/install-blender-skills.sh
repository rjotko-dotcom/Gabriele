#!/usr/bin/env bash
# Įdiegia kevinbadi/blender-skills (blender-toolkit, product-polish, turntable, ...)
# į tavo asmeninį ~/.claude/skills. Ta repozitorija neturi licencijos, todėl jos
# nekopijuojam į šį projektą – diegiama tik tavo kompiuteryje.
# Reikia: Blender 5.x + "MCP for Blender" addon (žr. SKILLS.md), node, ffmpeg (video).
set -euo pipefail
dest="${HOME}/.claude/skills"
tmp="$(mktemp -d)"
git clone --depth 1 https://github.com/kevinbadi/blender-skills "$tmp/blender-skills"
mkdir -p "$dest"
for s in blender-toolkit product-polish turntable perfect-loop polyhaven-studio-setup threejs-export; do
  rm -rf "${dest:?}/$s"
  cp -r "$tmp/blender-skills/$s" "$dest/$s"
  echo "įdiegta: $s"
done
rm -rf "$tmp"
