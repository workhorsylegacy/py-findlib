
VERSION = 0.1.0

all:
	@echo build: Builds the python source dist package
	@echo install: Installs python source dist package
	@echo clean: Removes any generated files
	@echo rst: uses pandoc to generate the README.rst file from README.md

clean:
	rm -f -rf py_findlib.egg-info
	rm -f -rf dist
	rm -f -rf py-findlib-$(VERSION)
	rm -f -rf py-findlib-$(VERSION).tar.gz

build: clean
	python setup.py sdist
	mv dist/py-findlib-$(VERSION).tar.gz py-findlib-$(VERSION).tar.gz
	rm -f -rf py_findlib.egg-info
	rm -f -rf dist

install: remove
	tar xzf py-findlib-$(VERSION).tar.gz
	cd py-findlib-$(VERSION)/ && sudo python setup.py install
	rm -f -rf py-findlib-$(VERSION)

	@echo now try "from findlib import findlib"
	@echo "findlib.get_cpu_info()"

remove:
	sudo rm -f -rf /usr/local/lib/python2.7/dist-packages/py_findlib-$(VERSION)-py2.7.egg

rst:
	rm -f -rf README.rst
	pandoc --from=markdown --to=rst --output=README.rst README.md



