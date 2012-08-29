docs:
	scripts/generate-docs
	rsync -rh --inplace \
		doc/* \
		Geils:~/www/burntsushi.net/public_html/doc/nflgame/

pypi: docs
	sudo python2 setup.py register sdist bdist_wininst upload

pypi-meta:
	python2 setup.py register

schedule:
	scripts/create-schedule > schedule.py

json:
	scripts/download-json
