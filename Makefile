# Execute the "targets" in this file with `make <target>` e.g., `make test`.
#
# You can also run multiple in sequence, e.g. `make clean lint test serve-coverage-report`

clean:
	bash run.sh clean

help:
	bash run.sh help

install:
	bash run.sh install

generate-project:
	bash run.sh generate-project

lint:
	bash run.sh lint

lint-ci:
	bash run.sh lint:ci

# Test tiers, fastest first:
#   test-fast  - in-process render + assertions (~1s, no network). Use this while editing.
#   test-quick - everything not marked `slow`
#   test       - the full suite, including the wheel-in-a-venv functional tests (slow)
test-fast:
	bash run.sh test:fast

test-quick:
	bash run.sh test:quick

test:
	bash run.sh run-tests
