# Koristi ovo ako pokreces iz konzole
import sys
sys.path.insert(0, '../')

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studservice.settings")
import django

django.setup()

from studserviceapp.models import Predmet,Nastavnik,Nalog,Grupa,Semestar,RasporedNastave,Termin
import csv
from datetime import datetime

FILE_NAME = "raspored.csv"

GODINA = 2018

def simplify(string):
	ch_from = "ČĆŠŽčćšž"
	ch_to = "CCSZccsz"

	for i in range(len(ch_from)):
		string = string.replace(ch_from[i],ch_to[i])

	string = string.replace("Đ","Dj")
	string = string.replace("đ","dj")

def parse_vreme_termina(string):
	(begin,end) = string.split("-")
	begin_date = datetime.strptime(begin, '%H:%M')
	end_date = datetime.strptime(end,"%H")
	return (begin_date,end_date)


def skip(row):
	if(not row): # Ako je prazan
		return True

	if(row[0]=='Svi smerovi, odeljenje 1'): # Prvi red
		return True

	if(row[1]=='Predavanja' or row[1]=='Nastavnik(ci)'): # Nazivi kolona
		return True

	return False

def process_nastavnik(row,curr_predmet,offset):
	nastavnik = None
	if(len(row[offset].split(" ")) == 3):
		prezime1,prezime2,ime = row[offset].split(" ")
		prezime = prezime1 + " " + prezime2
	else:
		prezime,ime = row[offset].split(" ")
		
	if(Nastavnik.objects.filter(ime=ime,prezime=prezime).exists()): # Ako nastavnik vec postoji u bazi
		nastavnik = Nastavnik.objects.get(ime=ime,prezime=prezime)
	else:
		username = (ime[0] + prezime).lower() if ime else prezime.lower()
		print("Kreiranje {} naloga".format(username))
		nalog = Nalog.objects.create(username=username,uloga="nastavnik")
		print("Kreiranje {} {} nastavnika".format(ime,prezime))
		nastavnik = Nastavnik.objects.create(ime=ime,prezime=prezime,nalog=nalog)
	nastavnik.predmet.add(curr_predmet)
	return nastavnik

def process_grupe(row,curr_semestar,offset):
	grupe = row[offset+2].split(",")
	ret_grupe = []
	for grupa in grupe:
		grupa = grupa.strip()
		if(Grupa.objects.filter(oznaka_grupe = grupa).exists()):
			ret_grupe.append(Grupa.objects.get(oznaka_grupe = grupa))
			continue
		print("Kreiranje {} grupe".format(grupa))
		g = Grupa.objects.create(oznaka_grupe = grupa , semestar = curr_semestar)
		ret_grupe.append(g)
	return ret_grupe

def process_termin(row,predmet,nastavnik,grupe,semestar,offset):
	tip_nastave = {1: "Predavanja" , 9:"Praktikum" , 17:"Vezbe" ,25:"Pred. i Vez."}[offset]
	vreme = parse_vreme_termina(row[offset+5])
	oznaka_ucionice = row[offset+6]
	dan = row[offset+4]
	raspored = RasporedNastave.objects.get(semestar=semestar)
	print("Kreiranje {} {}-{} {} termina".format(tip_nastave,vreme[0],vreme[1],dan))
	termin = Termin.objects.create(oznaka_ucionice = oznaka_ucionice,
		pocetak=vreme[0],
		zavrsetak = vreme[1],
		dan = dan,
		tip_nastave = tip_nastave,
		nastavnik = nastavnik,
		predmet = predmet ,
		raspored = raspored)
	for grupa in grupe:
		termin.grupe.add(grupa)

def process_row(row,curr_predmet,curr_semestar):
	for i in [1,9,17,25]:
		if(row[i]):
			nastavnik = process_nastavnik(row,curr_predmet,i)
			grupe = process_grupe(row,curr_semestar,i)
			process_termin(row,curr_predmet,nastavnik,grupe,curr_semestar,i)

def create_semestri():
	print("Kreiranje semestara")
	neparni_semestar = Semestar.objects.create(vrsta="neparni",
			skolska_godina_pocetak=GODINA,
			skolska_godina_kraj=GODINA+1)

	# parni_semestar = Semestar.objects.create(vrsta="parni",
	# 		skolska_godina_pocetak=GODINA,
	# 		skolska_godina_kraj=GODINA+1)

	RasporedNastave.objects.create(datum_unosa=datetime.now(),semestar = neparni_semestar)
	# RasporedNastave.objects.create(datum_unosa=datetime.now(),semestar = parni_semestar)

	return neparni_semestar

if __name__ == "__main__":	
	with open(FILE_NAME,encoding='utf-8') as f:
		curr_semestar = create_semestri()
		raspored_csv = csv.reader(f,delimiter=";")
		curr_predmet = None
		for row in raspored_csv:
			if(skip(row)):
				continue
			if(len(row)==2):
				print("Kreiranje {} predmeta ".format(row[0]))
				curr_predmet = Predmet.objects.create(naziv=row[0])
			else:
				process_row(row,curr_predmet,curr_semestar)



