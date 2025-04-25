#!/bin/bash
CHK=$(checkupdates | wc -l)
CHKAUR=$(paru -Qau | wc -l)
SUM=$(($CHK + $CHKAUR))


if ! [ "$SUM" -eq 0 ]; then
  echo ${SUM}
fi
