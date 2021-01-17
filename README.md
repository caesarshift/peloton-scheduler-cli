# Peloton&reg; Stack Scheduler CLI

**Please note that this tool is not affiliated with or created by Peloton Interactive, Inc.**

## Goal: Provide a method to automatically create scheduled stacks for scheduled workout plans

## Why

1. The new [Peloton stack feature](https://blog.onepeloton.com/stackedclasses/) allows for only a single stack with no repeated classes
  * No way to create daily stacks
  * Stacks cannot contain duplicate classes. A user cannot define a set of workouts for the coming week that also include the same warmup/cooldown classes

## Requirements

* Python
* A list of bookmarked classes that you want to organize into scheduled stacks
* Ability to create a scheduled task/cronjob

## Getting Started

The expected workflow is that you have previously browsed the Peloton class schedule and bookmarked classes that you are interested in scheduling. If you have no bookmarked classes, please pull up your favorite Peloton app and bookmark some classes first.

## Windows Setup

### Install required python modules

```
git clone https://github.com/caesarshift/peloton-scheduler-cli.git
cd peloton-scheduler-cli
mkdir .venv
venv .venv
.venv/Scripts/activate.bat
pip install -r requirements.txt
```

### Save Peloton username and password to an environment variable (Windows):

```
set PELOTON_USERNAME=youremail@domain.com
set PELOTON_PASSWORD=yourpassword
```

## Linux Setup

### Install required python modules

```
git clone https://github.com/caesarshift/peloton-scheduler-cli.git
cd peloton-scheduler-cli
mkdir .venv
venv .venv
.venv/source/activate
pip install -r requirements.txt
```

### Save Peloton username and password to an environment variable (Linux):

```
export PELOTON_USERNAME=youremail@domain.com
export PELOTON_PASSWORD=yourpassword
```

## Usage

### View bookmarked classes (no ability to add bookmarked classes from CLI)

`python scheduler.py listclasses`

### Schedule some classes for a date (use indexes listed from `listclasses`)

`python scheduler.py addschedule --date 2021-01-18 0 1 2`

### List schedules for upcoming dates

`python scheduler.py listschedule`

### Show the current peloton stack

`python scheduler.py showstack`

### Load a schedule into the peloton stack (This can be run via scheduled task/cron to keep your Peloton stack current)

`python scheduler.py loadschedule`

## Version history
* **0.1** (2021-01-17) - Initial release.
* **0.2** (2021-01-17) - Only overwrite existing schedule if `--force` is present

## License

peloton-scheduler-cli is licensed under the [MIT](http://www.opensource.org/licenses/mit-license.php).

## Other libraries used by peloton-scheduler-cli

* [python](https://docs.python.org/3/license.html#psf-license) *(PSF License)*
* [tabulate](https://github.com/astanin/python-tabulate) *(MIT License)*
* [requests](https://pypi.org/project/requests/) *(Apache2 License)*
