PY := python3
COV := coverage3
TESTMODULES := test_datautils test_pack test_readtext test_readxl test_dbf

# "normal" assignment:
TAGRX1 := '/[ \t]*\([^ \t]+\)[ \t]*=[ \t]*[^ \t]+/\1/'
# the first of unpacked variables:
TAGRX2 := '/[ \t]*\([^ \t]+\), *[^=]+?=[ \t]*[^ \t]+/\1/'
# "normal" import
TAGRX3 := '/[ \t]*import[ \t]+\([^ \t]+\)\>/\1/'
# from m import ...:
TAGRX4 := '/[ \t]*from +[^ \t]+ +import +\([^ \t]+\)/\1/'
TAGRX5 := '/[ \t]*def \([^ \t]\)'

tags : TAGS
TAGS : *.py */*.py
	etags --regex=$(TAGRX1) --regex=$(TAGRX2) --regex=$(TAGRX3) \
	      --regex=$(TAGRX4) $^

test:
	cd tests; $(PY) -m unittest $(TESTMODULES)

linter:
	for name in $$(ls channelpack/*.py tests/*.py); do \
	flake8 $$name ; \
	done

coverage:
	cd tests; $(COV) run --source .. --omit ../tests.py -m unittest $(TESTMODULES)
	cd tests; $(COV) html
	see tests/htmlcov/index.html

doc:
	cd docs && make html

doctest:
	$(PY) -m doctest *.rst docs/*.rst

dist:
	$(PY) setup.py sdist bdist_wheel

release:
	twine upload dist/*

install:
	$(PY) setup.py install

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
