
.PHONY: test
test:
	python -m channelpack/tests

.PHONY: doc
doc:
	cd docs && make html

.PHONY: clean
clean:
	rm -f channelpack/*.pyc
	rm -f *.pyc