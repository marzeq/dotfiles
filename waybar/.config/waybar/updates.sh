#!/bin/bash
CHK=$(checkupdates | wc -l)
CHKAUR=$(paru -Qau | wc -l)

echo $(($CHK + $CHKAUR))
