StudWeb
=======

Script that sends email and/or SMS notification (for telenor or netcom users)
when new grades are published in [StudentWeb](http://www.studweb.no).

Written by [@tobiasvl](http://github.com/tobiasvl) and
[@jasama](http://github.com/jasama). Based on code by sindrf@math.uio.no and
[@runarfu](http://github.com/runarfu).

Requirements
------------

Python 2.5 or better and [`twill`](https://pypi.python.org/pypi/twill/0.9.1) are required. 

Usage
-----

Usage of config file is strongly recommended, as options passed to programs
tend to show up in the process list of some systems.

```
Usage: studweb.py [options]

Options:
  -h, --help            show this help message and exit
  -d, --daemon          daemonize
  -i INTERVAL, --interval=INTERVAL
                        update interval in minutes, 0 implies single run
                        [default: 15]
  -s STATEFILE, --statefile=STATEFILE
                        file for storing grades between runs [default:
                        studweb_state.pickle]
  -w WORKING_DIRECTORY, --working-directory=WORKING_DIRECTORY
                        working directory in daemon mode [default: /tmp]
  -c CONFIG_FILE, --config-file=CONFIG_FILE
                        read config from file [default: none]

  Studweb related options:
    WARNING: PIN code and FNR should be set in the config file (see -c),
    since these can appear in the process list of some systems.

    -f FNR, --fnr=FNR   Birth number used to log into Studentweb
    -p PIN, --pin=PIN   PIN code used with -f or --fnr

  Email notification options:
    -e EMAIL, --email=EMAIL
                        Email address used as to/from when sending
                        notification
    -r SMTP, --smtp=SMTP
                        SMTP server used to send email [default: smtp.uio.no]

  SMS notification using Netcom:
    The username must be your cell phone number. WARNING: password and
    username should be set in the config file (see -c) since these can
    appear in the process list of some systems.

    -n NETCOM_USER, --netcom-user=NETCOM_USER
    -m NETCOM_PASS, --netcom-password=NETCOM_PASS

  SMS notification using Telenor:
    The username must be your cell phone number. WARNING: password and
    username should be set in the config file (see -c) since these can
    appear in the process list of some systems.

    -t TELENOR_USER, --telenor-user=TELENOR_USER
    -y TELENOR_PASS, --telenor-password=TELENOR_PASS
```
