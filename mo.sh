#!/bin/bash
DOMAIN="uzanta"
xgettext -f "$(dirname "$0")""/locale/POTFILES.in" "$(dirname "$0")""/main.py" --output="$(dirname "$0")""/locale/traduko.pot" --from-code=UTF-8 --default-domain=$DOMAIN
for lingvo in en_US eo fa
do
    msgmerge -U "$(dirname "$0")""/locale/$lingvo/LC_MESSAGES/$lingvo.po" "$(dirname "$0")""/locale/traduko.pot"
    msgfmt -o "$(dirname "$0")""/locale/$lingvo/LC_MESSAGES/$DOMAIN.mo" "$(dirname "$0")""/locale/$lingvo/LC_MESSAGES/$lingvo.po"
done
