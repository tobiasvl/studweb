#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import email
import sys
import os
import twill.commands as tc
import shutil

# Innstillinger
fnr = '' # Ditt fÃ¸dselsnummer
pin = '' # PIN-kode til studweb
epost = '' # E-postadressen din
smtp = 'smtp.uio.no' # SMTP-server
terskel = 300 # Differanse pÃ¥ filer fÃ¸r og etter ny karakter

# Har vi noe Ã¥ sammenligne med?
if os.path.exists('studweb.html'):
    shutil.move('studweb.html', 'studweb_old.html')
else:
    open('studweb.html', 'w').close()
    open('studweb_old.html', 'w').close()

# Logg inn:
tc.go("https://studweb.uio.no/as/WebObjects/studentweb2.woa/3/wa/default?inst=UiO")
tc.fv("2", "fodselsnr", fnr)
tc.fv("2", "pinkode", pin)
tc.submit()

# Naviger til karakterer:
tc.follow('Se opplysninger om deg')
tc.follow('Resultater')
tc.save_html('studweb.html');
tc.show()

tc.follow('Logg ut')

# Sammenlign
ny_str = os.path.getsize('studweb.html')
gml_str = os.path.getsize('studweb_old.html')
delta = ny_str - gml_str

# FilstÃ¸rrelsen har endret seg tilstrekkeli, og det er ikke fÃ¸rste gang vi sjekker
if delta > terskel and gml_str != 0:
    print "Nytt resultat, sender e-post"
    msg = email.MIMEText("Nytt resultat fra StudentWeb. Logg inn her: https://studweb.uio.no")
    msg['Subject'] = "StudentWeb oppdatert"
    msg['From'] = epost
    msg['To'] = epost
    s = smtplib.SMTP(smtp)
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()
