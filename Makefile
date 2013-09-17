all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./nflgame

pypi: docs
	sudo python2 setup.py register sdist bdist_wininst upload

longdesc.rst: nflgame/__init__.py docstring
	pandoc -f markdown -t rst -o longdesc.rst docstring
	rm -f docstring

docstring: nflgame/__init__.py
	./extract-docstring > docstring

dev-install: docs longdesc.rst
	[[ -n "$$VIRTUAL_ENV" ]] || exit
	rm -rf ./dist
	python setup.py sdist
	pip install -U dist/*.tar.gz

pep8:
	pep8-python2 nflgame/{__init__,alert,game,live,player,seq,statmap,version}.py
	pep8-python2 scripts/nflgame-update-players

push:
	git push origin master
	git push github master
