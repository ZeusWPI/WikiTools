BEGIN {
  in_categories = 0
  ncats = 0
}
/\[\[Category:.*\]\]/ {
  in_categories = 1
  line=$0
  sub(/.*:/, "", line)
  sub("]]", "", line)
  categories[ncats++] = line
}
in_categories && $0 !~ /Category/ {
  in_categories = 0
  printf("{{tag>")
  for (i in categories) {
    printf("\"%s\" ", categories[i])
  }
  printf("}}\n")
}
!in_categories { print }
