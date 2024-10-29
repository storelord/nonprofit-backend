#!/bin/bash

# Check if the input file argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <inputfile>"
  exit 1
fi

# Input file from the first argument
INPUT_FILE="$1"

DEFAULT_PREFIX="split_part_"
OUTPUT_PREFIX="${2:-$DEFAULT_PREFIX}"

# Number of lines per split file (excluding the header)
LINES_PER_FILE=100000

# Get the header
HEADER=$(head -n 1 "$INPUT_FILE")

# Split the file, excluding the header
tail -n +2 "$INPUT_FILE" | split -l $LINES_PER_FILE - $OUTPUT_PREFIX

# Add the header to each split file
for FILE in $OUTPUT_PREFIX*
do
    echo "$HEADER" | cat - "$FILE" > temp && mv temp "$FILE"
done
