.PHONY: dist publish fmt 

fmt:
	black -t py36 setup.py src/rocmi.py

dist:
	python setup.py sdist bdist_wheel

publish: dist
	pip install 'twine>=1.5.0'
	twine upload --repository rocmi --skip-existing dist/*
	rm -rf build dist .egg *.egg-info
