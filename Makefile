PHANTOMJS=$(CURDIR)/node_modules/.bin/mocha-phantomjs

.PHONY : test clean test-py test-js

default: test

test-py:
	python test/runtests.py

test-js: node_modules
	$(PHANTOMJS) test/tests.html

test: test-js coverage

node_modules: package.json
	npm install

coverage:
	coverage run test/runtests.py --with-xunit && \
		coverage xml --omit="admin.py,*.virtualenvs/*,./test/*"

coverage-html:
	[ -d htmlcov ] || rm -rf htmlcov
	coverage run test/runtests.py && \
		coverage html --omit="admin.py,*.virtualenvs/*,./test/*"

clean:
	find . -name '*.pyc' | xargs rm -f
