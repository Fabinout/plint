#!/bin/bash

TEXT="$1"

./plint.py "plint/test_data/$TEXT.tpl" < "plint/test_data/$TEXT"
