#!/bin/bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv pip install -e ."[dev]"
