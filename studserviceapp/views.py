from django.shortcuts import render

import csv
import io

import json

# Create your views here.
from django.http import HttpResponse
from .models import *

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .parse_raspored_polaganja import import_data
from .send_gmail import create_and_send_message

def index(request):
    return render(request, 'studserviceapp/loginStranica.html')
    
def newGroup(request, username):
    predmetiSemestar = {}
    for semestar in range(1,9):
        predmetiSemestar[semestar] = []
        for predmet in Predmet.objects.all():
            if(predmet.semestar_po_programu==semestar):
                predmetiSemestar[semestar].append(predmet.naziv)
    context = { 'predmeti' : Predmet.objects.all(), 'predmetiSemestar' : json.dumps(predmetiSemestar), 'linkovi' : get_linkovi(username)}
    return render(request, 'studserviceapp/newGroup.html', context)

def addGroup(request):
    for oznaka_grupe in request.POST['oznaka_grupe'].split(';'):
        aktivna = False
        if 'aktivna' in request.POST and request.POST['aktivna']:
            aktivna = True
        izbornaGrupa = IzbornaGrupa(oznaka_grupe=oznaka_grupe, oznaka_semestra=request.POST['oznaka_semestra'], kapacitet=request.POST['kapacitet'], smer=request.POST['smer'], aktivna=aktivna, za_semestar=Semestar.objects.get(id = request.POST['za_semestar']))
        izbornaGrupa.save()
        for predmet_id in request.POST.getlist('predmeti'):
            izbornaGrupa.predmeti.add(Predmet.objects.get(id=predmet_id))
    return HttpResponse("Uspesno dodata grupa")

def izaberiGrupu(request):
    izabrana_grupa = IzbornaGrupa.objects.get(id=request.POST['izbor_grupe'])
    student = Student.objects.get(smer=request.POST['smer'],
        broj_indeksa=request.POST['broj_indeksa'],
        godina_upisa=int(request.POST['godina_upisa']))
    izbor_grupe = IzborGrupe.objects.create(
        ostvarenoESPB=int(request.POST['broj_ostvarenih_ESPB']),
        upisujeESPB=int(request.POST['broj_ESPB_upisanih']),
        broj_polozenih_ispita=int(request.POST['broj_polozenih_ispita']),
        upisuje_semestar=int(request.POST['oznaka_semestra']),
        prvi_put_upisuje_semestar=(request.POST['prvi_put_upisuje']=='Da'),
        nacin_placanja = request.POST['nacin_placanja'],
        student = student ,
        izabrana_grupa = izabrana_grupa ,
        upisan = False)
    for predmet_id in request.POST.getlist('predmeti'):
        print("Izabrani predmeti: {}".format(predmet_id))
        predmet = Predmet.objects.get(id=predmet_id)
        izbor_grupe.nepolozeni_predmeti.add(predmet)
    return HttpResponse("Uspesno izabrana grupa")

def izborgrupe(request,username):
    if(not Nalog.objects.filter(username=username).exists()):
        return HttpResponse("Nalog {} ne postoji".format(username))

    nalog = Nalog.objects.get(username=username)
    student = Student.objects.get(nalog=nalog)

    if(IzborGrupe.objects.filter(student=student).exists()):
        return HttpResponse("Vec ste izabrali grupu.")

    grupeSemestar = {}
    for semestar in range(1, 9):
        grupeSemestar[semestar] = []
        for grupa in IzbornaGrupa.objects.all():
            if grupa.oznaka_semestra == semestar:
                grupeSemestar[semestar].append(grupa.oznaka_grupe)

    curr_semestar = Semestar.objects.order_by('-pk')[0]
    neparni_semsetar = (curr_semestar.vrsta == 'neparni')

    skolska_godina_pocetak = curr_semestar.skolska_godina_pocetak
    skolska_godina_kraj = curr_semestar.skolska_godina_kraj

    semestri = [1,3,5,7] if neparni_semsetar else [2,4,6,8]
    predmeti = Predmet.objects.all()

    popunjenost_grupa = {x.id: 0 for x in IzbornaGrupa.objects.all()}
    for izbor_grupe in IzborGrupe.objects.all():
        popunjenost_grupa[izbor_grupe.izabrana_grupa.id] += 1
    izborne_grupe = list(filter(lambda grupa: popunjenost_grupa[grupa.id] < grupa.kapacitet and grupa.aktivna, IzbornaGrupa.objects.all()))

    smerovi = ['RN','RM','RD','RI','S','M','D']
    smerovi.remove(student.smer)
    smerovi = [student.smer] + smerovi

    godine_upisa = [2013,2014,2015,2016,2017,2018]
    godine_upisa.remove(student.godina_upisa)
    godine_upisa = [student.godina_upisa] + godine_upisa

    context = { 'student' : student ,
                'predmeti' : predmeti ,
                'smerovi' : smerovi ,
                'godine_upisa' : godine_upisa ,
                'skolska_godina_pocetak' : skolska_godina_pocetak ,
                'skolska_godina_kraj' : skolska_godina_kraj ,
                'semestri' : semestri ,
                'grupe' : izborne_grupe,
                'linkovi' : get_linkovi(username),
                'grupeSemestar': json.dumps(grupeSemestar)
                }
    return render(request,'studserviceapp/izborGrupe.html',context)

def changeGroup(request,grupa):
    predmetiSemestar = {}
    for semestar in range(1, 9):
        predmetiSemestar[semestar] = []
        for predmet in Predmet.objects.all():
            if (predmet.semestar_po_programu == semestar):
                predmetiSemestar[semestar].append(predmet.naziv)
    context = {'grupa' : IzbornaGrupa.objects.get(oznaka_grupe=grupa),
                'predmeti' : Predmet.objects.all(),
               'predmetiSemestar': json.dumps(predmetiSemestar)}
    return render(request,'studserviceapp/changeGroup.html',context)

def changedGroup(request):
    izbornaGrupa = IzbornaGrupa.objects.get(oznaka_grupe=request.POST['oznaka_grupe'])
    izbornaGrupa.oznaka_semestra = oznaka_semestra=request.POST['oznaka_semestra']
    izbornaGrupa.kapacitet = request.POST['kapacitet']
    izbornaGrupa.smer = request.POST['smer']
    izbornaGrupa.aktivna = False
    if 'aktivna' in request.POST and request.POST['aktivna']:
        izbornaGrupa.aktivna = True
    izbornaGrupa.za_semestar = Semestar.objects.get(id = request.POST['za_semestar'])
    izbornaGrupa.save()
    if 'reset' in request.POST:
        predmeti = izbornaGrupa.predmeti.through.objects.all()
        for predmet in predmeti:
            if(predmet.izbornagrupa_id==izbornaGrupa.id):
                predmet.delete()
    if 'predmeti' in request.POST:
        for predmet_id in request.POST.getlist('predmeti'):
            izbornaGrupa.predmeti.add(Predmet.objects.get(id=predmet_id))
    return HttpResponse("Uspesna izmena grupe")

def groupList(request, username):
    grupe = []
    for g in Grupa.objects.all():
        grupe.append(g)
    grupe.sort(key = lambda x : x.oznaka_grupe)
    grupePrva = []
    grupeDruga = []
    grupeTreca = []
    grupeCetvrta = []
    for g in grupe:
        if g.oznaka_grupe[0] == '1':
            grupePrva.append(g)
        elif g.oznaka_grupe[0] == '2':
            grupeDruga.append(g)
        elif g.oznaka_grupe[0] == '3':
            grupeTreca.append(g)
        else:
            grupeCetvrta.append(g)
    context = { 'g1' : grupePrva,
                'g2' : grupeDruga,
                'g3' : grupeTreca,
                'g4' : grupeCetvrta,
                'linkovi' : get_linkovi(username)}
    return render(request,'studserviceapp/groupList.html',context)

def groupStudents(request):
    studenti = {}
    group_id = int(request.POST['grupa'])
    for student in Student.objects.all():
        grupa = Grupa.objects.get(id = Student.grupa.through.objects.get(student_id=student.id).grupa_id)
        if(grupa.id == group_id):
            studentKey = student.ime + ' ' + student.prezime + ' ' + student.smer + ' ' + str(student.broj_indeksa)+'/'+str(student.godina_upisa)
            slikaUrl = ''
            if student.slika.name:
                slikaUrl = student.slika.url
            studenti[studentKey] = slikaUrl
    grupa = Grupa.objects.get(id = group_id).oznaka_grupe
    context = { 'studenti' : studenti,
                'grupa'    : grupa}
    return render(request,'studserviceapp/grupaStudenti.html', context)

def podaciStudenta(request, username):
    studentNalog = Nalog.objects.get(username = username)
    student = Student.objects.get(nalog=studentNalog)
    slikaUrl = ''
    if student.slika.name:
        slikaUrl = student.slika.url
    context = { 'student' : student, 'slikaURL' : slikaUrl,'linkovi':get_linkovi(username), 'oznaka_grupe':student.grupa.get().oznaka_grupe}
    return render(request, 'studserviceapp/podaciStudenta.html', context)

def uploadSliku(request):
    nalog = Nalog.objects.get(username = request.POST['nalog'])
    student = Student.objects.get(nalog = nalog)
    pic = request.FILES['pic']
    fs = FileSystemStorage()
    filename = fs.save(pic.name, pic)
    student.slika = fs.url(filename)
    student.save()
    return HttpResponse("Uspesno dodata slika")

def predajeStudentima(request, username):
    profesorNalog = Nalog.objects.get(username = username)
    profesor = Nastavnik.objects.get(nalog=profesorNalog)
    context = { 'predmeti' : {} }
    for predmet in profesor.predmet.all():
        context['predmeti'][predmet.naziv] = []
        for izbornaGrupa in IzbornaGrupa.objects.all():
            if predmet in izbornaGrupa.predmeti.all():
                context['predmeti'][predmet.naziv].append(izbornaGrupa)
    context['linkovi'] = get_linkovi(username)
    return render(request, 'studserviceapp/predajeStudentima.html', context)

def izbornaGrupaList(request, group):
    studenti = {}
    for student in Student.objects.all():
        studentKey = student.ime + ' ' + student.prezime + ' ' + student.smer + ' ' + str(student.broj_indeksa)+'/'+str(student.godina_upisa)
        try:
            izborGrupe = IzborGrupe.objects.get(student=student)
        except IzborGrupe.DoesNotExist:
            continue
        izbornaGrupa = IzbornaGrupa.objects.get(oznaka_grupe=izborGrupe.izabrana_grupa.oznaka_grupe)
        if(izbornaGrupa.oznaka_grupe==group):
            if student.slika and hasattr(student.slika, 'url'):
                studenti[studentKey] = student.slika.url
            else:
                studenti[studentKey] = ''
    context = {'oznaka_grupe' : group, 'studenti' : studenti}
    return render(request, "studserviceapp/izbornaGrupaList.html", context)

def submitRasporedPolaganja(request, username):
    if(username == 'submit'):
        return do_submitRasporedPolaganja(request)
    return render(request,'studserviceapp/submitRasporedPolaganja.html')

def do_submitRasporedPolaganja(request):
    if 'dokument' in request.FILES:
        tip_rasporeda = request.POST['tip_rasporeda']
        naziv_rasporeda = request.POST['naziv_rasporeda']
        file = request.FILES['dokument']
        file = file.read().decode('UTF-8')
        file = io.StringIO(file)
        dokument = csv.reader(file)

    else:
        tip_rasporeda = request.POST['tip_rasporeda']
        naziv_rasporeda = request.POST['naziv_rasporeda']
        predmeti = request.POST.getlist('predmet[]')
        profesori = request.POST.getlist('profesor[]')
        ucionice = request.POST.getlist('ucionice[]')
        vreme = request.POST.getlist('vreme[]')
        dan = request.POST.getlist('dan[]')
        datum = request.POST.getlist('datum[]')

        dokument = []

        for i in range(len(predmeti)):
            dokument.append([predmeti[i],"","",profesori[i],ucionice[i],vreme[i],dan[i],datum[i]])


    if(tip_rasporeda=='klk_nedelja'):
        errors,to_correct = import_data(dokument,klk_nedelja=naziv_rasporeda)
    else:
        errors,to_correct = import_data(dokument,ispitni_rok=naziv_rasporeda)
    if not errors:
        return HttpResponse("Uspesno ste izvrsili ubacivanje rasporeda")
    else:
        context = {'errors':errors,'to_correct':to_correct,'tip_rasporeda':tip_rasporeda,
        'naziv_rasporeda':naziv_rasporeda}
        return render(request,'studserviceapp/submitRasporedPolaganja_failed.html',context)
    

def sendMail(request, username):
    nalog = Nalog.objects.get(username=username)
    uloga = nalog.uloga
    opcije_predmeti = []
    opcije_grupe = []
    opcije_smer = []

    if username=='jmarkovic16': uloga = 'administrator'

    if (uloga == "student"):
        return HttpResponse("Student ne moze da salje email-ove!")

    elif(uloga == "nastavnik"):
        person = Nastavnik.objects.get(nalog=nalog)

        predmetiID = []
        for predmet in person.predmet.through.objects.all():
            if(predmet.nastavnik_id == person.nalog_id):
                predmetiID.append(predmet.predmet_id)
        for predmet in Predmet.objects.all():
            if predmet.id in predmetiID:
                opcije_predmeti.append(predmet)

        terminiID = []
        for termin in Termin.objects.all():
            if (termin.predmet_id in predmetiID and person.id==termin.nastavnik_id):
                ter = termin
                terminiID.append(termin.id)
        terminGrupe = ter.grupe.through.objects.all()
        grupeID = []
        for grupa in terminGrupe:
            if(grupa.termin_id in terminiID):
                grupeID.append(grupa.grupa_id)
        for grupa in Grupa.objects.all():
            if grupa.id in grupeID:
                opcije_grupe.append(grupa)

    else:
        person = nalog;
        for grupa in Grupa.objects.all():
            if not(grupa in opcije_grupe):
                opcije_grupe.append(grupa)
            if  (not grupa.smer in opcije_smer and grupa.smer!=None):
                opcije_smer.append(grupa.smer)
        for predmet in Predmet.objects.all():
            if not(predmet in opcije_predmeti):
                opcije_predmeti.append(predmet)

    opcije_smer.sort()
    opcije_grupe.sort(key = lambda x : x.oznaka_grupe)
    opcije_predmeti.sort(key = lambda x : x.naziv)
    context = {'person' : person,
                'uloga' : uloga,
                'opcije_predmeti' : opcije_predmeti,
                'opcije_grupe' : opcije_grupe,
                'opcije_smer' : opcije_smer,
                'linkovi': get_linkovi(username)}

    return render(request,'studserviceapp/mailForma.html',context)

def mailSent(request):
    to_list = []
    sender = " "
    body = " "
    subject = " "
    file = None

    if 'body' in request.POST:
         body = request.POST['body']
    if 'subject' in request.POST:
        subject = request.POST['subject']
    if 'uloga' in request.POST:
        if request.POST['uloga']=='nastavnik':
            sender = request.POST['sender-prof'] + "@raf.rs"
        else:
            sender = request.POST['sender'] + "@raf.rs"
    if 'file' in request.POST:
        file = request.POST['file']
    nalog_id = []
    student_id = []
    if 'to' in request.POST:
        primalac = request.POST['to']
        if primalac == 'svi':
            for student in Student.objects.all():
                nalog_id.append(student.nalog_id)
        elif primalac in request.POST['to_smer']:
            for student in Student.objects.all():
                if student.smer == primalac:
                    nalog_id.append(student.nalog_id)
        elif primalac in request.POST['to_grupe']:
            for student in Student.grupa.through.objects.all():
                if student.grupa_id == int(primalac):
                    nalog_id.append(Student.objects.get(id=student.student_id).nalog_id)
        else:
            for predmet in Predmet.objects.all():
                if primalac in predmet.naziv:
                    terminiID = []
                    for termin in Termin.objects.all():
                        if (termin.predmet_id==predmet.id):
                            ter = termin
                            terminiID.append(termin.id)
                    terminGrupe = ter.grupe.through.objects.all()
                    grupeID = []
                    for grupa in terminGrupe:
                        if(grupa.termin_id in terminiID):
                            grupeID.append(grupa.grupa_id)
                    for grupa in Grupa.objects.all():
                        if grupa.id in grupeID:
                            for student in Student.grupa.through.objects.all():
                                if student.grupa_id == grupa.id:
                                    nalog_id.append(Student.objects.get(id=student.student_id).nalog_id)
                    break

    for nalog in Nalog.objects.all():
        if nalog.id in nalog_id:
            create_and_send_message("Test",sender,nalog.username+"@raf.rs",subject,body,file)
    return HttpResponse("Uspesno poslat email!")

def get_linkovi(username):
    nalog = Nalog.objects.get(username = username)
    linkovi = {}
    linkovi['Home'] = 'http://localhost:8000/studserviceapp/home/'+username
    if(nalog.uloga == 'student'):
        linkovi['Ceo Raspored'] = 'http://127.0.0.1:8000/studserviceapp/ceoRaspored/' + username
        linkovi['Podaci Studenta'] = 'http://127.0.0.1:8000/studserviceapp/podaciStudenta/'+username
        if IzbornaGrupa.objects.count() > 0:
            linkovi['Izbor Grupe'] = 'http://127.0.0.1:8000/studserviceapp/izborgrupe/'+username
    elif(nalog.uloga == 'nastavnik'):
        linkovi['Ceo Raspored'] = 'http://127.0.0.1:8000/studserviceapp/ceoRaspored/' + username
        linkovi['Predaje Studentima'] = 'http://127.0.0.1:8000/studserviceapp/predajeStudentima/' + username
        linkovi['Slanje Mejla'] = 'http://127.0.0.1:8000/studserviceapp/mail/' + username
    elif(nalog.uloga == 'sekretar'):
        linkovi['Unos Obavestenja'] = 'http://127.0.0.1:8000/studserviceapp/unosObavestenja/' + username
        linkovi['Slanje Mejla'] = 'http://127.0.0.1:8000/studserviceapp/mail/' + username
        linkovi['Izborne Grupe'] = 'http://127.0.0.1:8000/studserviceapp/izborneGrupe/' + username
        linkovi['Spisak Studenata'] = 'http://127.0.0.1:8000/studserviceapp/groupList/' + username
        linkovi['Detalji Izbora Grupe'] = 'http://127.0.0.1:8000/studserviceapp/izborGrupeDetalji/' + username
    else:
        linkovi['Unos Rasporeda'] = 'http://127.0.0.1:8000/studserviceapp/submitRasporedPolaganja/' + username
        linkovi['Unos Obavestenja'] = 'http://127.0.0.1:8000/studserviceapp/unosObavestenja/' + username
        linkovi['Slanje Mejla'] = 'http://127.0.0.1:8000/studserviceapp/mail/' + username
        linkovi['Unos Grupe'] = 'http://127.0.0.1:8000/studserviceapp/newGroup/' + username
        linkovi['Izborne Grupe'] = 'http://127.0.0.1:8000/studserviceapp/izborneGrupe/' + username
        linkovi['Spisak Studenata'] = 'http://127.0.0.1:8000/studserviceapp/groupList/' + username
        linkovi['Detalji Izbora Grupe'] = 'http://127.0.0.1:8000/studserviceapp/izborGrupeDetalji/' + username
    return linkovi

def loginResponse(request):
    username = request.POST['username']
    return home(request,username)

def home(request, username):
    nalog = Nalog.objects.get(username = username)
    linkovi = get_linkovi(username)
    raspored =[]
    if nalog.uloga == 'student':
        student = Student.objects.get(nalog=nalog)
        for termin in Termin.objects.all():
            if student.grupa.get() in termin.grupe.all():
                terminGrupe = termin.grupe.order_by('oznaka_grupe').first().oznaka_grupe
                for grupa in termin.grupe.order_by('oznaka_grupe'):
                    terminGrupe += ', ' + grupa.oznaka_grupe
                raspored.append([termin.predmet.naziv, termin.tip_nastave, termin.nastavnik.ime + " " + termin.nastavnik.prezime, terminGrupe, termin.dan, termin.pocetak.strftime("%H:%M") + '-' + termin.zavrsetak.strftime("%H:%M"), termin.oznaka_ucionice])
    elif nalog.uloga == 'nastavnik':
        nastavnik = Nastavnik.objects.get(nalog=nalog)
        for termin in Termin.objects.all():
            if nastavnik == termin.nastavnik:
                terminGrupe = termin.grupe.order_by('oznaka_grupe').first().oznaka_grupe
                for grupa in termin.grupe.order_by('oznaka_grupe'):
                    terminGrupe += ', ' + grupa.oznaka_grupe
                raspored.append(
                    [termin.predmet.naziv, termin.tip_nastave, termin.nastavnik.ime + " " + termin.nastavnik.prezime,
                     terminGrupe, termin.dan,
                     termin.pocetak.strftime("%H:%M") + '-' + termin.zavrsetak.strftime("%H:%M"),
                     termin.oznaka_ucionice])
    elif nalog.uloga == 'sekretar':
        for termin in Termin.objects.all():
            terminGrupe = termin.grupe.order_by('oznaka_grupe').first().oznaka_grupe
            for grupa in termin.grupe.order_by('oznaka_grupe'):
                terminGrupe += ', ' + grupa.oznaka_grupe
            raspored.append(
                [termin.predmet.naziv, termin.tip_nastave, termin.nastavnik.ime + " " + termin.nastavnik.prezime,
                 terminGrupe, termin.dan,
                 termin.pocetak.strftime("%H:%M") + '-' + termin.zavrsetak.strftime("%H:%M"),
                 termin.oznaka_ucionice])
    else:
        for termin in Termin.objects.all():
            terminGrupe = termin.grupe.order_by('oznaka_grupe').first().oznaka_grupe
            for grupa in termin.grupe.order_by('oznaka_grupe'):
                terminGrupe += ', ' + grupa.oznaka_grupe
            raspored.append(
                [termin.predmet.naziv, termin.tip_nastave, termin.nastavnik.ime + " " + termin.nastavnik.prezime,
                 terminGrupe, termin.dan,
                 termin.pocetak.strftime("%H:%M") + '-' + termin.zavrsetak.strftime("%H:%M"),
                 termin.oznaka_ucionice])
    grupe = []
    for grupa in Grupa.objects.all():
        grupe.append(grupa.oznaka_grupe)
    grupe.sort()

    nastavnici = []
    for nastavnik in Nastavnik.objects.all():
        nastavnici.append(nastavnik.ime + ' ' + nastavnik.prezime)
    nastavnici.sort()

    ucionice = set()
    for termin in Termin.objects.all():
        ucionice.add(termin.oznaka_ucionice)
    ucionice = list(ucionice)
    ucionice.sort()

    obavestenja = []
    for obavestenje in Obavestenje.objects.order_by('datum_postavljanja').reverse()[0:5]:
        fajl = ''
        if obavestenje.fajl.name:
            fajl = obavestenje.fajl.url
        obavestenja.append([obavestenje.postavio.username, obavestenje.datum_postavljanja.strftime("%Y-%m-%d %H:%M:%S"), obavestenje.tekst, fajl])

    context = \
        {
            'linkovi' : json.dumps(linkovi),
            'raspored' : json.dumps(raspored),
            'grupe' : json.dumps(grupe),
            'nastavnici' : json.dumps(nastavnici),
            'ucionice' : json.dumps(ucionice),
            'obavestenja' : json.dumps(obavestenja)
        }
    return render(request, 'studserviceapp/home.html', context)

def izborGrupeDetalji(request, username):
    return render(request,'studserviceapp/izborGrupeDetalji.html', {'linkovi' : get_linkovi(username)})

def izborGrupeDetalji_request(request):
    unos = request.POST['unos']
    tip = request.POST['tip_pretrage']
    if(tip == 'imePrezime'):
        ime,prezime = unos.split(' ')
        student = Student.objects.get(ime=ime,prezime=prezime)
    else:
        student = Student.objects.get(broj_indeksa=unos)
    izbor_grupe = IzborGrupe.objects.get(student=student)

    prvi_put_upisuje_semestar = 'DA' if izbor_grupe.prvi_put_upisuje_semestar else 'NE'

    nepolozeni_predmeti = []
    for predmet in izbor_grupe.nepolozeni_predmeti.all():
        nepolozeni_predmeti.append(predmet.naziv)

    context = {
        'indeks' : student.smer + ' ' + str(student.broj_indeksa) + '/' + str(student.godina_upisa),
        'ime'    : student.ime,
        'prezime' :student.prezime,
        'broj_ESPB' : izbor_grupe.ostvarenoESPB,
        'upisujem_ESPB' : izbor_grupe.upisujeESPB,
        'br_polozenih_ispita': izbor_grupe.broj_polozenih_ispita,
        'semestar': izbor_grupe.upisuje_semestar,
        'prvi_put_upisuje_semestar' : prvi_put_upisuje_semestar,
        'izabrana_grupa' : izbor_grupe.izabrana_grupa.oznaka_grupe,
        'nepolozeni_predmeti' : nepolozeni_predmeti,
        'nacin_pacanja_skolarine': izbor_grupe.nacin_placanja

    }
    return render(request,'studserviceapp/izborGrupeDetalji_request.html',context)

def unosObavestenja(request, nalog):
    predmetiSemestar = {}
    for semestar in range(1,9):
        predmetiSemestar[semestar] = []
    for predmet in Predmet.objects.all():
        if predmet.semestar_po_programu:
            predmetiSemestar[predmet.semestar_po_programu].append(predmet.naziv)
    context = { 'predmeti' : Predmet.objects.all(), 'predmetiSemestar' : json.dumps(predmetiSemestar), 'linkovi' : get_linkovi(nalog), 'nalog' : Nalog.objects.get(username = nalog).id}
    return render(request, 'studserviceapp/unosObavestenja.html', context)

import datetime
def unesiObavestenje(request):

    obavestenje = Obavestenje(datum_postavljanja=datetime.datetime.now(), tekst=request.POST['tekst'], postavio_id=request.POST['nalog'])
    if 'fajl' in request.FILES:
        fajl = request.FILES['fajl']
        fs = FileSystemStorage()
        filename = fs.save(fajl.name, fajl)
        obavestenje.fajl = fs.url(filename)
    obavestenje.save()
    return HttpResponse("Uspesno dodato obavestenje")

def izborneGrupe(request, username):
    grupeSemestar = {}
    for semestar in range(1,9):
        grupeSemestar[semestar] = []
    grupeSmer = { 'RN' : [], 'RM' : []}
    for grupa in IzbornaGrupa.objects.all():
        grupeSemestar[grupa.oznaka_semestra].append(grupa.oznaka_grupe)
        grupeSmer[grupa.smer].append(grupa.oznaka_grupe)
    context = { 'izborneGrupe' : IzbornaGrupa.objects.all() , 'grupeSemestar' : grupeSemestar, 'grupeSmer' : grupeSmer, 'linkovi' : get_linkovi(username)}
    return render(request, 'studserviceapp/izborneGrupe.html', context)

def ceoRaspored(request, username):
    raspored =[]
    for termin in Termin.objects.all():
        terminGrupe = termin.grupe.order_by('oznaka_grupe').first().oznaka_grupe
        for grupa in termin.grupe.order_by('oznaka_grupe'):
            terminGrupe += ', ' + grupa.oznaka_grupe
        raspored.append(
            [termin.predmet.naziv, termin.tip_nastave, termin.nastavnik.ime + " " + termin.nastavnik.prezime,
             terminGrupe, termin.dan,
             termin.pocetak.strftime("%H:%M") + '-' + termin.zavrsetak.strftime("%H:%M"),
             termin.oznaka_ucionice])
    grupe = []
    for grupa in Grupa.objects.all():
        grupe.append(grupa.oznaka_grupe)
    grupe.sort()

    nastavnici = []
    for nastavnik in Nastavnik.objects.all():
        nastavnici.append(nastavnik.ime + ' ' + nastavnik.prezime)
    nastavnici.sort()

    ucionice = set()
    for termin in Termin.objects.all():
        ucionice.add(termin.oznaka_ucionice)
    ucionice = list(ucionice)
    ucionice.sort()

    linkovi = get_linkovi(username)
    context = \
    {
        'linkovi' : json.dumps(linkovi),
        'raspored' : json.dumps(raspored),
        'grupe' : json.dumps(grupe),
        'nastavnici' : json.dumps(nastavnici),
        'ucionice' : json.dumps(ucionice)
    }

    return render(request,'studserviceapp/ceoRaspored.html', context)