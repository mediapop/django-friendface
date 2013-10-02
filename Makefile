PACKAGE_PATH=friendface

.PHONY : test clean test-py test-js

default: coverage

develop: setup-git
	pip install -q "file://`pwd`#egg=django-friendface[tests]"
	pip install -q -e .

setup-git:
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../hooks/* ./

lint-python:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 $(PACKAGE_PATH)
	@echo ""

test-py:
	django-admin.py test $(PACKAGE_PATH) --settings=$(PACKAGE_PATH).tests.settings

test: install-test-requirements test-py

install-test-requirements:
	pip install "file://`pwd`#egg=django-friendface[tests]"

node_modules: package.json
	npm install

coverage: coverage-py

coverage-py:
	coverage run test/runtests.py --with-xunit && \
		coverage xml --omit="admin.py,*.virtualenvs/*,./test/*"

clean:
	find . -name '*.pyc' | xargs rm -f
