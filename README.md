# Cobalt

## PROJECT UNDER DEVELOPMENT NOT FOR PRODUCTION USE

[![Code Climate](https://codeclimate.com/github/krodyrobi/cobalt/badges/gpa.svg)](https://codeclimate.com/github/krodyrobi/cobalt)
[![Test Coverage](https://codeclimate.com/github/krodyrobi/cobalt/badges/coverage.svg)](https://codeclimate.com/github/krodyrobi/cobalt/coverage)
[![Issue Count](https://codeclimate.com/github/krodyrobi/cobalt/badges/issue_count.svg)](https://codeclimate.com/github/krodyrobi/cobalt)
[![Documentation Status](https://readthedocs.org/projects/presslabs-cobalt/badge/?version=latest)](http://presslabs-cobalt.readthedocs.io/en/latest/?badge=latest)

### Testing

```bash
git clone git@github.com:Presslabs/cobalt
cd cobalt
mkvirtualenv -p python3 cobalt
pip install -r requirements/development.txt
PYTHONPATH=src py.test tests --cov=src
```

### Sample

To run the sample cluster you need ~6GB of space

From the project root folder

```bash
docker built -t presslabs/cobalt:latest .
sample/setup.sh
docker-compose up
```

### Reload drone.sec

Each time someone modifies .drone.yml this needs to be ran

```bash
drone secure --repo PressLabs/cobalt
```
