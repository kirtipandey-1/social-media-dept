#!/bin/bash
set -e
LAUNCHD_DIR=~/Library/LaunchAgents
PLIST_DIR=~/social-media-dept/launchd
PROJECT_DIR="$HOME/social-media-dept"

mkdir -p "$LAUNCHD_DIR"
echo "Installing launchd agents..."
for plist in main weekly monthly; do
  src="$PLIST_DIR/com.socialdept.$plist.plist"
  dst="$LAUNCHD_DIR/com.socialdept.$plist.plist"
  sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$src" > "$dst"
  launchctl unload "$dst" 2>/dev/null || true
  launchctl load "$dst"
  echo "  ✓ com.socialdept.$plist loaded"
done
echo "All agents active. Pipeline runs at 3am daily."
