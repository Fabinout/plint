LANG=plint/res/messages_fr.mo

.PHONY: all test

%.mo: %.po
	msgfmt -o $*.mo $*.po

all: ${LANG}

test:
	python3 versetest.py

