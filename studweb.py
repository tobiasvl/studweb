#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import email
import sys
import os
import twill
import twill.commands as tc
import twill.errors as te
import pickle
import re
import StringIO

# Innstillinger:
statefile = 'studweb_state.pickle'
# StudWeb-innstillinger:
fnr = '' # Ditt fødselsnummer
pin = '' # PIN-kode til studweb
# E-postvarsel:
epost = '' # E-postadressen din
smtp = 'smtp.uio.no' # SMTP-server
# SMS-varsel (kun NetCom):
sms_brukernavn = '' # Tlfnr. for minside på necom.no
sms_passord    = '' # Passord for minside

# Logg inn:
tc.go("https://studweb.uio.no/as/WebObjects/studentweb2.woa/3/wa/default?inst=UiO")
tc.fv("2", "fodselsnr", fnr)
tc.fv("2", "pinkode", pin)
tc.submit()

# Naviger til, og lagrer karakterer:

# Litt slapp lokalisering for nynorskbrukere. Bør utbedres
try:
    tc.follow('Se opplysninger om deg')
except te.TwillAssertionError:
    try:
        tc.follow('Sjå opplysningar om deg')
    except te.TwillAssertionError:
        print "Feil: ukjent språg?"
        sys.exit(1)

tc.follow('Resultater')

# Følgende lagrer HTML kode i variabel, i stedet for fil.
# show() er desverre ganske snakkesalig, så vi bytter fra stdout
# til ett vilkårlig StringIO objekt under kall for å få mindre støy.
twill.set_output(StringIO.StringIO())
data = tc.show('studweb.html')
twill.set_output(fp=None)

tc.follow('Logg ut')


# Napper fagkode og karakterer ut av HTML, og putter i array.
# Eks. på resultat: [["INF1000", "B"], ["INF1040", "E"]]
res = re.findall('<tr class="pysj\d">(.*?)</tr>', data)
ans = []
for i in res:
    if not re.search("Ikkje|Ikke", i):
        tmp = re.findall("<td.*?>(.*?)</td>", i)
        ans = ans + [[tmp[1], tmp[7]]]

# Hvis første gang programmet kjører,
# har vi ingen gammel fil å sammenligne med,
# lagrer karakterstate og avslutter.
if not os.path.exists(statefile):
    f = open(statefile, 'w')
    pickle.dump(ans, f)
    f.close()
    sys.exit(0)

# Laster state fra forrige kjøring
olddata = []
try:
    f = open(statefile)
    olddata = pickle.load(f)
    f.close()
except IOError:
    print "Feil: Noe er galt i statefilen"
    sys.exit(2)

# Dumper nye karakterer til fil
if len(ans) > len(olddata):
    f = open(statefile, 'w')
    pickle.dump(ans, f)
    f.close()

# Tar vekk gamle karakterer. Hvis len(new) da er sann, så har
# vi fått en ny karakter siden sist kjøring.
new = [x for x in ans if (lambda x: True if x not in olddata else False)(x)]

# Vi har ny(e) karakter, send epost/sms med karakter.
if len(new):
    print "Nytt resultat fra StudentWeb."
    
    karakterer = reduce(lambda x,y: x + y[0] + ": " + y[1] + ", ", new, '')[:-2]
    print karakterer

    if epost:
        print "Sender e-post"
        msg = email.MIMEText("Nytt resultat fra StudentWeb. Logg inn her: https://studweb.uio.no\n" + karakterer)
        msg['Subject'] = "StudentWeb oppdatert"
        msg['From'] = epost
        msg['To'] = epost
        s = smtplib.SMTP(smtp)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()

    if sms_brukernavn:
        print "Sender SMS"
        tc.go("https://www.netcom.no")
        tc.follow("» Logg inn på Min side")
        tc.fv('2', 'username', sms_brukernavn)
        tc.fv('2', 'password', sms_passord)
        tc.submit()
        tc.follow("Send 25 gratis SMS")
        tc.fv('2', 'gsmnumber', sms_brukernavn)
        tc.submit('submitChooseContact')
        tc.fv('2', 'message', "Nytt resultat fra StudentWeb. Logg inn her: https://studweb.uio.no\n" + karakterer)
        tc.submit('submitSendsms')

