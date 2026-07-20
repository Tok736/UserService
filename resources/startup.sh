#!/bin/bash

python3 src/scripts/create_config.py
python3 src/scripts/create_database.py
alembic upgrade head

faststream run src.main:app --workers $(python3 src/scripts/get_workers_amount.py)