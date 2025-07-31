#!/bin/bash
# Train ML models - run via cron every 6 hours

cd /path/to/ethoscope
source .venv/bin/activate
python -m backend.ml.training >> logs/ml_training.log 2>&1
