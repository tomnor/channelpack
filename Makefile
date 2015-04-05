SUIT = '0 1 2 3 4 5 6 7 8 9 10'

.PHONY: test
test:
	python -m channelpack.tests $(SUIT)

.PHONY: modconf
modconf:
	cp testdata/make_conf_file_mod.cfg testdata/conf_file_mod.cfg

.PHONY: doc
doc:
	cd docs && make html

.PHONY: clean
clean:
	rm -f channelpack/*.pyc
	rm -f testdata/*.pyc
	rm -f *.pyc
