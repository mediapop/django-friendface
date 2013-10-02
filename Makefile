PACKAGE_PATH=friendface

.PHONY : test clean test-py

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

coverage: install-test-requirements
	coverage run --source=$(PACKAGE_PATH) `which django-admin.py` test $(PACKAGE_PATH) --settings=$(PACKAGE_PATH).tests.settings

clean:
	find . -name '*.pyc' | xargs rm -f
