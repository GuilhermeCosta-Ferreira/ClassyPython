.PHONY: format diagram lint dev

diagram:
	PLANTUML_LIMIT_SIZE=16384 plantuml -tpng docs/*.puml

format:
	docformatter --in-place --recursive --wrap-summaries 88 --wrap-descriptions 88 src/simulator
	black src/simulator/
	black tests/

lint:
	poetry run pylint --disable=C src/

dev: diagram format lint
