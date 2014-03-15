# Codery

Codery is a tool for content analysis in the social sciences.

## Trying it out

Clone this repository (or [download the
contents](https://github.com/inducer/codery/archive/master.zip) and unpack),
then say:

```
python manage.py syncdb
python manage.py runserver
```

## Complete set-up instructions

Entering the following commands should leave you with a working version:

```
# install virtualenv, create a virtualenv
curl -k https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.9.1.tar.gz | tar xfz -
python virtualenv-1.9.1/virtualenv.py --no-setuptools myenv
source myenv/bin/activate

# Download, install setuptools
curl -k https://bitbucket.org/pypa/setuptools/raw/bootstrap-py24/ez_setup.py | python -

# Download, install pip
curl http://git.tiker.net/pip/blob_plain/77f959a3ce9cc506efbf3a17290d387d0a6624f5:/contrib/get-pip.py | python -

hash -r

# Download, unpack codery
curl -O https://github.com/inducer/codery/archive/master.zip
unzip master.zip
cd codery-master
pip install -r requirements.txt
python manage.py syncdb
python manage.py runserver
```

## Dependencies

* [BeautfulSoup4](http://pypi.python.org/pypi/BeautfulSoup4) for picking apart
  HTML exported out of LexisNexis (Version 4 or newer)
* [Django](http://djangoproject.com) for picking apart
  HTML exported out of LexisNexis (Version 1.6 or newer)
