
.PHONY: test
test:
	python -m channelpack/tests

.PHONY: docs
docs:
	cd docs && make html