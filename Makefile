
.PHONY: test
test:
	python -m channelpack/tests

.PHONY: doc
doc:
	cd docs && make html