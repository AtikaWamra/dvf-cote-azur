.PHONY: install download run all demo test lint clean

install:            ## Installe le projet et les outils de dev
	pip install -e ".[dev]"

download:           ## Télécharge les fichiers Geo-DVF (data/raw)
	python -m dvf.cli download

run:                ## Entrepôt + contrôles qualité + analyses + graphiques + enseignements
	python -m dvf.cli run

all: download run   ## Tout, de zéro

demo:               ## Pipeline complet sur données synthétiques (sans internet)
	python -m dvf.cli demo

test:               ## Tests unitaires et de bout en bout
	pytest -q

lint:
	ruff check src tests

clean:
	rm -rf outputs outputs_demo data/demo .pytest_cache
