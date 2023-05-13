# define the name of the virtual environment directory
VENV := venv

all: venv src/vanna/__init.py___

venv: $(VENV)/bin/activate

# Rebuild the virtual environment when init.py changes
$(VENV)/bin/activate: src/vanna/__init.py__
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install .

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

.PHONY: all clean 