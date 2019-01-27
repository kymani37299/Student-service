import sys
sys.path.insert(0, '../')

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studservice.settings")
import django

django.setup()


from datetime import datetime
from studserviceapp.models import Nastavnik,Predmet,TerminPolaganja,RasporedPolaganja

def skip(row):
	if(row[0]=='Predmet'):
		return True
	if(not row[0]):
		return True
	return False

def simplify(string):
	ch_from = "ČĆŠŽčćšž"
	ch_to = "CCSZccsz"

	for i in range(len(ch_from)):
		string = string.replace(ch_from[i],ch_to[i])

	string = string.replace("Đ","Dj")
	string = string.replace("đ","dj")

	return string

def import_data(file,klk_nedelja=None,ispitni_rok=None):
	data_to_add = []
	errors = []
	data_to_correct = []

	row_count = -1
	for row in file:
		row_count += 1
		error_hapened = False
		if skip(row):
			continue
		predmet = simplify(row[0].strip())
		profesor = simplify(row[3].strip()).split(" ",1)
		ucionice = row[4].strip()
		vreme = row[5].strip()
		dan = row[6].strip()
		datum = row[7].strip()

		# Data validation

		if(not Predmet.objects.filter(naziv=predmet).exists()):
			errors.append("Greska u redu {} : Ne postoji {} u bazi predmeta".format(row_count,predmet))
			error_hapened = True
			row[0] = ""
		if(len(profesor)<2 or not Nastavnik.objects.filter(ime=profesor[0],prezime=profesor[1]).exists()):
			errors.append("Greska u redu {} : Ne postoji {} u bazi nastavnika".format(row_count," ".join(profesor)))
			error_hapened = True
			row[3] = ""

		try:
			(b,e) = vreme.split('-')
			b = datetime.strptime(b,"%H")
			e = datetime.strptime(e,"%H")
			vreme = (b,e)
		except ValueError:
			errors.append("Greska u redu {} : Ne validan unos vremena".format(row_count))
			error_hapened = True
			row[5]= ""

		try:
			(day,month,_) = datum.split('.')
			if(len(day)==1):
				day = '0'+day
			if(len(month)==1):
				month = '0'+month
			datum = datetime.strptime(day + " " + month , "%d %m")
		except ValueError:
			errors.append("Greska u redu {} : Ne validan unos datuma".format(row_count))
			error_hapened = True
			row[7] = ""
		#####

		if not error_hapened:
			data_to_add.append((predmet,profesor,ucionice,vreme,dan,datum))
		else:
			data_to_correct.append({'predmet':row[0],
				'profesor':row[3],
				'ucionice':row[4],
				'vreme':row[5],
				'dan':row[6],
				'datum':row[7]})


	if(RasporedPolaganja.objects.filter(ispitni_rok=ispitni_rok,kolokvijumska_nedelja=klk_nedelja).exists()):
		raspored_polaganja = RasporedPolaganja.objects.get(ispitni_rok=ispitni_rok,kolokvijumska_nedelja=klk_nedelja)
	else:
		raspored_polaganja = RasporedPolaganja.objects.create(ispitni_rok=ispitni_rok,kolokvijumska_nedelja=klk_nedelja)

	for data in data_to_add:
		predmet = Predmet.objects.get(naziv=data[0])
		profesor = Nastavnik.objects.get(ime=data[1][0],prezime=data[1][1])

		if( not TerminPolaganja.objects.filter(predmet=predmet,nastavnik=profesor,ucionice=data[2],pocetak=data[3][0],zavrsetak=data[3][1],datum=data[5],raspored_polaganja = raspored_polaganja).exists()):
			TerminPolaganja.objects.create(predmet=predmet,
				nastavnik=profesor,
				ucionice=data[2],
				pocetak=data[3][0],
				zavrsetak=data[3][1],
				datum=data[5],
				raspored_polaganja = raspored_polaganja)

	return errors , data_to_correct





