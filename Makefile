SUIT = '0 1 2 3 4 5 6 7 8 9 10'
SUIT = '0 1 2   4 5 6 7 8 9 10'

.PHONY: test
test:
	python -m channelpack.tests $(SUIT)

.PHONY: doc
doc:
	cd docs && make html

.PHONY: clean
clean:
	rm -f channelpack/*.pyc
	rm -f testdata/*.pyc
	rm -f *.pyc
