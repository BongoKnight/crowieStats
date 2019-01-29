# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 08:22:24 2019

@author: nainvert
"""
import json
import datetime
import time
import sqlite3
import ciso8601
import dateutil.relativedelta
import matplotlib.pyplot as plt
from geolite2 import geolite2

def pie_graph(sql, alternate_text, savefile, limit=5, db='stats.db'):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(sql)
    nbs = []
    datas = []
    for row in c:
        nbs+=[row[1]]
        datas+=[row[0]]
    nbsClean = nbs
    datasClean = datas
    if len(nbs) > limit :
        nbsClean = nbs[0:limit] + [sum(nbs[limit:])]
        datasClean = datas[0:limit] + ["Autres (" + str(len(nbs[limit:])) + " " + alternate_text + ")" ]
    fig1, ax1 = plt.subplots()
    ax1.pie(nbsClean, labels=datasClean, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    fig1.savefig(savefile)
    conn.close()

    

def cmd_longest(db='stats.db'):
    sql = "Select timestamp, src_ip, input, a.session from command, (select session, count(1) as nb from command where datetime(timestamp,'unixepoch') >= date('now') group by session order by nb DESC limit 1 ) a where a.session = command.session ";
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(sql)
    text = "\n\nLa suite de commande la plus longue effectuée aujourd'hui est la suivante :\n\n```bash"
    for row in c:
        text+='\n' + str(row[2])
    text+='\n```\n\n'
    conn.close()
    return text



def cmd_used(db='stats.db'):
    sql="select input, count(1) as nb from command where input != '' group by input order by nb desc LIMIT 5"
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(sql)
    text = "\n\nLes commandes les plus utilisées sont :\n\n```bash"
    for row in c:
        text+='\n#' + str(row[1]) + " tentatives"
        text+='\n' + str(row[0])
    text+='\n```\n\n'
    conn.close()
    return text

def couple_used(db='stats.db'):
    sql= "SELECT username, password, count(1) as nb from (SELECT username, password from failed union all select username, password from success) group by username, password order by nb desc LIMIT 10"
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(sql)
    text = "\n\nLes couples \"utilisateurs / mots de passes\" les plus utilisées sont :\n\n| Utilisateurs | Mot de passe | Occurences |\n|-------|--------|------|"
    for row in c:
        text+='\n|' + str(row[0]) + "|" +  str(row[1]) + "|" + str(row[2]) + "|"
       
    text+='\n```\n\n'
    conn.close()
    return text






with open('./cowrie.json', "r") as f:
    datas = f.readlines()
f.closed
conn = sqlite3.connect('stats.db')
reader = geolite2.reader()
c = conn.cursor()


oldest = datetime.date.today() - dateutil.relativedelta.relativedelta(months=3)
print("Deleting entries older than : " + str(oldest))
c.execute("DELETE  from success where datetime(timestamp, 'unixepoch') <= date('"+ str(oldest) +"')")
c.execute("DELETE  from failed where datetime(timestamp, 'unixepoch') <= date('"+ str(oldest) +"')")
c.execute("DELETE  from command where datetime(timestamp, 'unixepoch') <= date('"+ str(oldest) +"')")
for data in datas :
    jsonData = json.loads(data)
    if jsonData['eventid'] != None:
        t = jsonData['timestamp']
        ts = ciso8601.parse_datetime(t)
        ts = time.mktime(ts.timetuple())
        loc = reader.get(jsonData['src_ip'])['country']['names']['fr']

        
        if jsonData['eventid'] == "cowrie.login.success":
            try :
                keys = (jsonData['session'],jsonData['username'],jsonData['password'],int(ts),jsonData['src_ip'],loc)
                c.execute("insert into success values (?,?,?,?,?,?)", keys )
            except :
                continue
                
        elif jsonData['eventid'] == "cowrie.login.failed":
            try :
                keys = (jsonData['session'],jsonData['username'],jsonData['password'],int(ts),jsonData['src_ip'],loc)
                c.execute("insert into failed values (?,?,?,?,?,?)", keys )
            except :
                continue                
        elif jsonData['eventid'] == "cowrie.command.input":
            try :
                keys = (int(ts),jsonData['src_ip'],jsonData['input'],jsonData['session'])
                c.execute("insert into command values (?,?,?,?)", keys )
            except :
                continue
geolite2.close()          
conn.commit()
conn.close()



print("Starting graphs generation.")
#Données du jour
pie_graph("select loc, count(*) as nb from failed where datetime(timestamp, 'unixepoch') >= date('"+ str(datetime.date.today()) +"') group by loc order by nb desc", 'pays', 'failed.png', 5)
pie_graph("select loc, count(*) as nb from success where datetime(timestamp, 'unixepoch') >= date('"+ str(datetime.date.today()) +"') group by loc order by nb desc", 'pays', 'success.png', 5)
pie_graph("select password, count(*) as nb from failed where datetime(timestamp, 'unixepoch') >= date('"+ str(datetime.date.today()) +"') group by password order by nb desc", 'mots de passe', 'failed_pass.png', 20)
pie_graph("select password, count(*) as nb from success where datetime(timestamp, 'unixepoch') >= date('"+ str(datetime.date.today()) +"') group by password order by nb desc", 'mots de passe', 'success_pass.png', 20)

#Données des derniers mois
pie_graph("select loc, count(*) as nb from failed  group by loc order by nb desc", 'pays', 'failed_3months.png', 5)
pie_graph("select loc, count(*) as nb from success  group by loc order by nb desc", 'pays', 'success_3months.png', 5)
pie_graph("select password, count(*) as nb from failed  group by password order by nb desc", 'mots de passe', 'failed_pass_3months.png', 20)
pie_graph("select password, count(*) as nb from success  group by password order by nb desc", 'mots de passe', 'success_pass_3months.png', 20)
print("Graphs generation complete.")

print("Generating report")
textReport = "---\ntitle: Rapport HoneyPot du " + str(datetime.date.today()) + "\nauthor: Hector \n \n..."

textReport+="\n# Statistiques générales"
textReport+=couple_used()

textReport+= "\n# Statistiques sur les connexions échouées"
textReport+= "\n\nVoici les données d'aujourd'hui :"
textReport+= "\n\n![Origine géographique des connexions échouées](failed.png){width=50%}"
textReport+= "\n\n![Mots de passe les plus courants](failed_pass.png){width=50%}"
textReport+= "\n\nEt celles des trois derniers mois :"
textReport+= "\n\n![Origine géographique des connexions échouées](failed_3months.png){width=50%}"
textReport+= "\n\n![Mots de passe les plus courants](failed_pass_3months.png){width=50%}"

textReport+= "\n\n# Statistiques sur les connexions réussies"
textReport+= "\n\nVoici les données d'aujourd'hui :"
textReport+= "\n\n![Origine géographique des connexions réussies](success.png){width=50%}"
textReport+= "\n\n![Mots de passe les plus courants](success_pass.png){width=50%}"
textReport+= "\n\nEt celles des trois derniers mois :"
textReport+= "\n\n![Origine géographique des connexions échouées](success_3months.png){width=50%}"
textReport+= "\n\n![Mots de passe les plus courants](success_pass_3months.png){width=50%}"

textReport+= "\n\n# Statistiques sur les commandes utilisées"
textReport+= cmd_longest()
textReport+= cmd_used()









file = open('Report.md', 'w')
file.write(textReport)
file.close()

