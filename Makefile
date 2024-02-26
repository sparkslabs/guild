PYTHON=`which python3`
DESTDIR=/
PROJECT=guild
VERSION=1.3.7

all:
	@echo "Preferred targets"
	@echo
	@echo "make deb - Generate a deb package"
	@echo "make use - Install the debian package"
	@echo "make purge - Uninstall the debian package"
	@echo "make devloop - purge current deb, build new deb, and install new debian package"
	@echo "----------------------------------------------------------------"
	@echo "Source based targets"
	@echo
	@echo "make source - Create source package"
	@echo "make install - Install source package on local system (prefer debs though)"
	@echo "----------------------------------------------------------------"
	@echo "make clean - Get rid of scratch and byte files (distclean is a synonym)"
	@echo "make test - run tests"
	# @echo "make buildrpm - Generate a rpm package"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

purge:
	sudo apt-get -y purge python3-$(PROJECT)


deb:
	# debuild -uc -us
	rm -rf dist
	$(PYTHON) setup.py sdist
	cd dist && py2dsc $(PROJECT)-* && cd deb_dist/$(PROJECT)-$(VERSION) && debuild -uc -us

ppadeb:
	$(PYTHON) setup.py sdist
	cd dist && py2dsc $(PROJECT)-* && cd deb_dist/$(PROJECT)-$(VERSION) && debuild -S && cd .. && dput ppa:sparkslabs/packages $(PROJECT)_*_source.changes
	@echo "Clean up dist before uploading to pypi, or it'll contain too much junk"

pypi:
	$(PYTHON) setup.py sdist upload

use:
	cd dist && cd deb_dist/ && sudo dpkg -i python3-$(PROJECT)_*


clean:
	$(PYTHON) setup.py clean
	rm -rf dist
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete
	rm -f *~

test:
	cd features && behave

distclean: clean

devloop: purge clean deb use

edit:
	((kate --new -s Guild </dev/null >/dev/null 2>/dev/null)&)&
