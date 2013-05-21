PHANTOMJS=$(CURDIR)/node_modules/.bin/mocha-phantomjs

.PHONY : test clean test-py test-js

default: test

test-py:
	python test/runtests.py

test-js: node_modules
	$(PHANTOMJS) test/tests.html

test: test-py test-js

node_modules: package.json
	npm install

clean:
	find . -name '*.pyc' | xargs rm -f