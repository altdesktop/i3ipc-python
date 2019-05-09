.PHONY: test format lint all clean publish docs coverage docker-test
.DEFAULT_GOAL := all

source_dirs = i3ipc test examples

lint:
	flake8 $(source_dirs)

format:
	yapf -rip $(source_dirs)

test:
	./run-tests.py

docker-test:
	docker build -t i3ipc-python-test .
	docker run -it i3ipc-python-test

clean:
	rm -rf dist i3ipc.egg-info build docs/_build
	rm -rf `find -type d -name __pycache__`

publish:
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

docs:
	sphinx-build docs docs/_build/html

livedocs:
	sphinx-autobuild docs docs/_build/html --watch i3ipc -i '*swp' -i '*~'

all: format lint docker-test
