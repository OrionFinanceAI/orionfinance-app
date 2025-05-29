#!/bin/bash
curl -Ls https://astral.sh/uv/install.sh | sh
$HOME/.local/bin/uv pip install -e ."[dev]"
