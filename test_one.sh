#!/bin/bash

TEXT="$1"

python3 -m plint "plint/test_data/$TEXT.tpl" < "plint/test_data/$TEXT"
