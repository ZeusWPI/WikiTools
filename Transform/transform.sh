#!/bin/bash

temp="$(mktemp)"
from="$(mktemp)"

find pages/ -type f ! -path 'pages/wiki/*' ! -path 'pages/wikizeus/*' | while read page; do
  echo "doing '$page'"
  cat "$page" > "$from"
  for script in $(ls transformations/); do
    script="transformations/$script"
    extension="${script: -3}"
    case "$extension" in
      "sed") sed -f "$script" "$from" > "$temp";;
      "awk") awk -f "$script" "$from" > "$temp";;
    esac
    cat "$temp" > "$from"
  done
  cat "$temp" > "$page"
  shift
done

rm "$temp"
rm "$from"

