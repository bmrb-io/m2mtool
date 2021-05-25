.DEFAULT_GOAL := all
.PHONY: all clean

#virtual environments are not relocatable, so we must create it where we want it installed
IDIR := /usr/software/m2mtool

$(IDIR):
	#create virtual environment
	python3.8 -m venv $(IDIR)

$(IDIR)/bin/python: $(IDIR)
	# a fake rule. The directory timestamp gets updated, causing a false positive
	# on needing to install requirements.txt. Make dependency on a file instead

$(IDIR)/lib/python3.6/site-packages/cursesmenu: $(IDIR)/bin/python
	$(IDIR)/bin/pip install -U pip
	$(IDIR)/bin/pip install -r requirements.txt

$(IDIR)/bin/m2mtool: $(IDIR)/lib/python3.6/site-packages/cursesmenu
	$(IDIR)/bin/python setup.py install

all: $(IDIR)/bin/m2mtool

clean:
	rm -fr $(IDIR)
