#!/bin/sh
# Start the bundler locally, for testing.

export PYTHONPATH=.
exec python3 styrene "$@"
