#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

import smtplib
from email.mime.text import MIMEText
import sys
import os
import twill
import twill.commands as tc
import twill.errors as te
import pickle
import re
import StringIO
import time
from optparse import OptionParser, OptionGroup

# Dumper data til statefil
def dump(data, statefile):
    f = open(statefile, 'w')
    pickle.dump(data, f)
    f.close()

def getResults(opts):
    # Twill pøser ut ymse rask, men det vil vi ikke ha
    twill.set_output(StringIO.StringIO())

    # Logg inn i studweb
    tc.go("https://studweb.uio.no/as/WebObjects/studentweb2.woa/3/wa/default?inst=UiO")
    tc.fv("2", "fodselsnr", opts["fnr"])
    tc.fv("2", "pinkode", opts["pin"])
    tc.submit()

    # Naviger til karakterer
    # Litt slapp lokalisering for nynorskbrukere. Bør utbedres
    try:
        tc.follow('Se opplysninger om deg')
    except te.TwillAssertionError:
        try:
            # Merk: wildcard i linknavn. krøll med æøå.
            tc.follow('Sj. opplysningar om deg')
        except te.TwillAssertionError:
            print "Feil: ukjent språg?"
            sys.exit(1)
    tc.follow('Resultater')

    # Lagrer HTML kode i variabel
    data = tc.show()

    tc.follow('Logg ut')

    # Napper fagkode og karakterer ut av HTML, konverterer stryk
    # til bokstavkarakter, og konverterer deretter til array.
    # Eks. på resultat: [["INF1000", "B"], ["INF1040", "E"]]
    res = re.findall('<tr class="pysj\d">(.*?)</tr>', data)
    ans = {}
    for i in res:
        if not re.search("Ikkje møtt|Ikke møtt", i):
            tmp = re.findall("<td.*?>(.*?)</td>", i)
            if not re.search("[A-E]", tmp[7]):
                tmp[7] = "F"
            if (not ans.has_key(tmp[1])) or (ans.has_key(tmp[1]) and ans[tmp[1]]== "F"):
                ans[tmp[1]] = tmp[7]
    return reduce(lambda x, y: x + [[y, ans[y]]], ans, [])

def sendNetcom(opts, msg):
    tc.go("https://www.netcom.no")
    tc.follow("» Logg inn på Min side")
    tc.fv('2', 'username', opts["netcom_user"])
    tc.fv('2', 'password', opts["netcom_pass"])
    tc.submit()
    tc.follow("Send 25 gratis SMS")
    tc.fv('2', 'gsmnumber', opts["netcom_user"])
    tc.submit('submitChooseContact')
    tc.fv('2', 'message', msg)
    tc.submit('submitSendsms')

def sendTelenor(opts, msg):
    # Login
    tc.go("https://telenormobil.no/norm/telenor/sms/send.do")
    tc.fv("loginForm", "phonenumber", opts["telenor_user"])
    tc.fv("loginForm", "password", opts["telenor_pass"])
    tc.submit()

    # Send
    tc.fv("smsSendSmsForm", "toAddress", opts["telenor_user"])
    tc.fv("smsSendSmsForm", "message", msg)
    tc.submit()

    # Logout
    tc.follow("Logg ut")

def sendEmail(opts, msg):
    m = MIMEText(msg)
    m['Subject'] = "StudentWeb oppdatert"
    m['From'] = opts["email"]
    m['To'] = opts["email"]
    s = smtplib.SMTP(opts["smtp"])
    s.sendmail(m['From'], m['To'], m.as_string())
    s.quit()

def checkAndSend(opts, olddata=[]):
    ans = getResults(opts)
    
    # Hvis første gang programmet kjører,
    # har vi ingen gammel fil å sammenligne med,
    # lagrer karakterstate og returnerer.
    if not os.path.exists(opts["statefile"]):
        dump(ans, opts["statefile"])
        return []
    elif olddata == []:
        # Laster state fra forrige kjøring
        try:
            f = open(opts["statefile"])
            olddata = pickle.load(f)
            f.close()
        except IOError:
            print "Feil: Noe er galt i statefilen"
            sys.exit(2)

    # Tar vekk gamle karakterer. Hvis len(new) da er sann, så har
    # vi fått en ny karakter siden sist kjøring.
    new = [x for x in ans if (lambda x: True if x not in olddata else False)(x)]
    
    # Vi har ny(e) karakter, send epost/sms med karakter.
    if len(new):
        dump(ans, opts["statefile"])
        print "Nytt resultat fra StudentWeb."

        # Lager pen tekst med fagkode og karakterer:
        msg = "Nytt resultat fra StudentWeb: "
        msg += reduce(lambda x,y: x + y[0] + ": " + y[1] + ", ", new, '')[:-2]
        
        if opts["email"]:
            print "Sender e-post"
            sendEmail(opts, msg)

        if opts["netcom_user"]:
            print "Sender SMS via NetCom"
            sendNetcom(opts, msg)

        if opts["telenor_user"]:
            print "Sender SMS via telenor"
            sendTelenor(opts, msg)
    return ans


if __name__ == "__main__": 
    parser = OptionParser()
    # generelle opsjoner
    parser.add_option("-d", "--daemon", action="store_true", dest="daemon",
            default=False, help="daemonize")
    parser.add_option("-i", "--interval", type="int", dest="interval",
            default=15, help="update interval in minutes, 0 implies single"+\
                    " run [default: %default]")
    parser.add_option("-s", "--statefile", type="string", dest="statefile",
            default="studweb_state.pickle",
            help="file for storing grades between runs [default: %default]")
    parser.add_option("-w", "--working-directory", type="string",
            dest="working_directory", default="/tmp",
            help="working directory in daemon mode [default: %default]")
    parser.add_option("-c", "--config-file", type="string", dest="config_file",
            default=None, help="read config from file [default: %default]")

    # Studweb relaterte opsjoner
    group = OptionGroup(parser, "Studweb related options", "WARNING: PIN" +\
            " code and FNR should be set in the config file (see -c), since" +\
            " these can appear in the process list of some systems.")
    group.add_option("-f", "--fnr", type="string", dest="fnr", default="",
            help="Birth number used to log into Studentweb")
    group.add_option("-p", "--pin", type="string", dest="pin", default="",
            help="PIN code used with -f or --fnr")
    parser.add_option_group(group)

    # Epost
    group = OptionGroup(parser, "Email notification options")
    group.add_option("-e", "--email", type="string", dest="email", default="",
            help="Email address used as to/from when sending notification")
    group.add_option("-r", "--smtp", type="string", dest="smtp",
            default="smtp.uio.no",
            help="SMTP server used to send email [default: %default]")
    parser.add_option_group(group)
    
    # SMS, netcom
    group = OptionGroup(parser, "SMS notification using Netcom",
            "The username must be your cell phone number.\n" + "WARNING: " +\
            "password and username should be set in the config file " +\
            "(see -c) since these can appear in the process list of some " +\
            "systems.")
    group.add_option("-n", "--netcom-user", type="string", dest="netcom_user",
            default="")
    group.add_option("-m", "--netcom-password", type="string",
            dest="netcom_pass", default="")
    parser.add_option_group(group)

    # SMS, Telenor
    group = OptionGroup(parser, "SMS notification using Telenor",
            "The username must be your cell phone number.\n" + "WARNING: " +\
            "password and username should be set in the config file " +\
            "(see -c) since these can appear in the process list of some " +\
            "systems.")
    group.add_option("-t", "--telenor-user", type="string", dest="telenor_user",
            default="")
    group.add_option("-y", "--telenor-password", type="string",
            dest="telenor_pass", default="")
    parser.add_option_group(group)
    (pa_options, args) = parser.parse_args()

    options = vars(pa_options)

    if pa_options.config_file:
        try:
            opt_keys = vars(pa_options).keys()
            f = open(pa_options.config_file)
            for l in f:
                if l[0] != '#' and len(l[:-1]):
                    tmp = l[:-1].split(':')
                    if tmp[0] in opt_keys:
                        obj = eval("pa_options." + tmp[0])
                        if type(obj) is str:
                            options[tmp[0]] = tmp[1]
                        else:
                            options[tmp[0]] = eval(tmp[1])
                    else:
                        print "Error: key error in config file, '" + tmp[0] + \
                            "' is not a key"
            f.close()
        except IOError:
            print "Error: cannot open " + options.config_file
            exit(1)

        ## Penere en å dumpe alt i en dict? virker dog ikke...       
        #try:
        #    opt_keys = vars(options).keys()
        #    f = open(options.config_file)
        #    for l in f:
        #        if l[0] != '#' and len(l[:-1]):
        #            tmp = l[:-1].split(':')
        #            if tmp[0] in opt_keys:
        #                obj = eval("options." + tmp[0])
        #                if type(obj) is str:
        #                    obj = eval("'" + tmp[1] + "'")
        #                else:
        #                    obj = eval(tmp[1])
        #            else:
        #                print "Error: key error in config file, '" + tmp[0] + \
        #                    "' is not a key"
        #    f.close()
        #except IOError:
        #    print "Error: cannot open " + options.config_file
        #    exit(1)

    if options["daemon"]:
        try:
            import daemon
            dae = daemon.DaemonContext()
            dae.working_directory = options.working_directory
            dae.umask = 0166
            with dae:
                if options["interval"]:
                    ans = []
                    while True:
                        ans = checkAndSend(options, ans)
                        time.sleep(options["interval"] * 60)
                else:
                    checkAndSend(options)
        except ImportError:
            print "Error: python-daemon is required"
    else:
        if options["interval"]:
            ans = []
            while True:
                ans = checkAndSend(options, ans)
                time.sleep(options["interval"] * 60)
        else:
            checkAndSend(options)

