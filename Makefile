LANG=res/messages_fr.mo

.PHONY: all

%.mo: %.po
	msgfmt -o $*.mo $*.po

all: ${LANG}

