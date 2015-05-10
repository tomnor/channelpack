SUIT = '0 1 2 3 4 5 6 7 8 9 10'

.PHONY: test
test:
	python -m tests $(SUIT)

.PHONY: modconf
modconf:
	cp testdata/make_conf_file_mod.cfg testdata/conf_file_mod.cfg

.PHONY: doc
doc:
	cd docs && make html

.PHONY: sdist
sdist:
	python setup.py sdist

.PHONY: release
release:
	# python setup.py sdist upload
	twine upload dist/*

.PHONY: install
install:
	python setup.py install

.PHONY: uninstall
uninstall:
	pip uninstall channelpack

.PHONY: clean
clean:
	rm -f channelpack/*.pyc
	rm -f testdata/*.pyc
	rm -f *.pyc
	rm -rf build *.egg-info dist
	rm -rf channelpack-[0-9]*
