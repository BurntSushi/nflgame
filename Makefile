all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./nflgame

pypi: docs
	sudo python2 setup.py register sdist bdist_wininst upload

dev-install: docs
	[[ -n "$$VIRTUAL_ENV" ]] || exit
	rm -rf ./dist
	python2 setup.py sdist
	pip install -U dist/*.tar.gz

pep8:
	pep8-python2 nflgame/{__init__,alert,game,live,player,seq,statmap}.py

push:
	git push origin master
	git push github master
