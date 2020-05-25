PY := python3
TESTMODULES := test_datautils test_pack test_readtext

tests:
	cd tests; $(PY) -m unittest $(TESTMODULES)

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

.PHONY: tests doc sdist release install uninstall clean
