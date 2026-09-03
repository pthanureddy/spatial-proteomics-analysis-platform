.PHONY: test backend-test frontend-test build scale-check compose-validate

test: backend-test frontend-test

backend-test:
	cd backend && python -m pytest

frontend-test:
	cd frontend && npm test

build:
	cd frontend && npm run build

scale-check:
	cd backend && python -m scripts.scale_check --rows 100000 --seed 2026

compose-validate:
	docker compose config

