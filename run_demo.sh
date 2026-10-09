#!/usr/bin/env sh
# Rebuild demo fixtures from synthetic scenes, then open the demo.
python -m src.pipeline.build_demo --synthetic && echo "Open web/index.html in your browser."
