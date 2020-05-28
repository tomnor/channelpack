PY := python3
COV := coverage3
TESTMODULES := test_datautils test_pack test_readtext test_readxl test_dbf

tests:
	cd tests; $(PY) -m unittest $(TESTMODULES)

coverage:
	cd tests; $(COV) run --source .. --omit ../tests.py -m unittest $(TESTMODULES)

doc:
	cd docs && make html

sdist:
	python setup.py sdist --formats=gztar,zip

release:
	# python setup.py sdist upload
	twine upload dist/*

install:
	python setup.py install

uninstall:
	pip uninstall channelpack

clean:
	rm -f channelpack/*.pyc
	rm -f tests/*.pyc
	rm -f *.pyc
	rm -rf build *.egg-info dist
	rm -rf channelpack-[0-9]*
	rm -rf .coverage tests/.coverage tests/htmlcov

.PHONY: tests doc sdist release install uninstall clean
