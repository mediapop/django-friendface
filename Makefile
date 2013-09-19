PACKAGE_PATH=friendface
PHANTOMJS=$(CURDIR)/node_modules/.bin/mocha-phantomjs

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
	python setup.py test

test-js: node_modules
	$(PHANTOMJS) -R tap test/tests.html

test: install-test-requirements test-js test-py

install-test-requirements:
	pip install "file://`pwd`#egg=django-friendface[tests]"

node_modules: package.json
	npm install

coverage: coverage-js coverage-py

coverage-py:
	coverage run test/runtests.py --with-xunit && \
		coverage xml --omit="admin.py,*.virtualenvs/*,./test/*"

coverage-js: node_modules
	$(PHANTOMJS) -R xunit test/tests.html > mochatests.xml

coverage-py-html:
	[ -d htmlcov ] || rm -rf htmlcov
	coverage run test/runtests.py && \
		coverage html --omit="admin.py,*.virtualenvs/*,./test/*"

clean:
	find . -name '*.pyc' | xargs rm -f
