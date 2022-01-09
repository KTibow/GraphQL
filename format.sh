#!/bin/bash
python -m black . --line-length=128
npx prettier . --write
npx tailwindcss -i frontend/style.css -o frontend/site.css
