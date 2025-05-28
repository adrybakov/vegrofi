#!/bin/bash
for filename in file-examples/not-valid/*.txt; do
    read -p "Press enter to test $filename"
    vegrofi "$filename"
    echo ""
done
