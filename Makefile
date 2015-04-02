PYTHON=`which python`
DESTDIR=/
PROJECT=python-guild

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

purge:
	sudo apt-get purge $(PROJECT)

deb:
	rm -rf dist; python setup.py sdist && cd dist && py2dsc guild* && cd deb_dist && cd guild* && debuild -uc -us

use:
	cd dist && cd deb_dist && sudo dpkg -i python-guild*deb

clean:
	$(PYTHON) setup.py clean
	rm -rf dist
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete

devloop: purge clean deb use 