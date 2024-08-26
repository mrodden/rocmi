.PHONY: dist publish fmt test

test:
	# make sure to install test-requirements locally first with:
	# pip install -r tests-req.in
	python -m unittest discover -v tests

fmt:
	black -t py36 setup.py src tests

dist:
	python setup.py sdist bdist_wheel

publish: dist
	pip install 'twine>=1.5.0'
	twine upload --repository rocmi --skip-existing dist/*
	rm -rf build dist .egg *.egg-info
