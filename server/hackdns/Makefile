PYTHON := /usr/bin/env python
MANAGE := $(PYTHON) manage.py

KEY_BITS      := 1024
SETTINGS_PROD := --settings=hackdns.settings_production
SETTINGS_TEST := --settings=hackdns.settings_example

.PHONY: help

help:
	@echo $(MAKE) config
	@echo $(MAKE) syncdb

config:
	@if [ -e settings_production.py ]; then echo "settings_production.py already exists"; exit 1; fi
	cp settings_example.py settings_production.py
	ls -al settings_production.py
	@echo
	@echo "Now edit hackdns/server/hackdns/settings_production.py"
	@echo

bootstrap:
	@bin/server-bootstrap

keys:
	@if [ -e secure/server.key ]; then echo "secure/server.key already exists"; exit 1; fi
	mkdir -p secure
	> secure/server.key
	chmod 600 secure/server.key
	openssl genrsa $(KEY_BITS) > secure/server.key
	openssl rsa -in secure/server.key -pubout -out secure/server.pub

shell:
	@$(MANAGE) shell_plus $(SETTINGS_PROD) 2>/dev/null || $(MANAGE) shell $(SETTINGS_PROD)

syncdb:
	$(MANAGE) syncdb $(SETTINGS_PROD)

shell_test:
	@$(MANAGE) shell_plus $(SETTINGS_TEST) 2>/dev/null || $(MANAGE) shell $(SETTINGS_TEST)

syncdb_test:
	$(MANAGE) syncdb $(SETTINGS_TEST)

