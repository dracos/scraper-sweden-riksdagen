# coding: utf-8

import datetime
import scraperwiki
import sys
import json

TODAY = datetime.date.today().isoformat()

URL = 'http://data.riksdagen.se/personlista/?iid=&fnamn=&enamn=&f_ar=&kn=&parti=&valkrets=&rdlstatus=&org=&utformat=json&termlista='

GENDER = {
    'kvinna': 'female',
    'man': 'male',
}

PARTY = {
    'S': u'Socialdemokraterna',
    'MP': u'Miljöpartiet de gröna',
    'FP': u'Folkpartiet liberalerna ',
    'L': u'Liberalerna',
    'M': u'Moderata samlingspartiet',
    'C': u'Centerpartiet',
    'V': u'Vänsterpartiet',
    'KD': u'Kristdemokraterna',
    'SD': u'Sverigedemokraterna',
    '-': u'Independent',
}

def scrape_term(t):
    j = json.loads(scraperwiki.scrape(URL))

    for person in j['personlista']['person']:
        image = person['bild_url_max']  # also 192 and 80 instead of max
        dob = person['fodd_ar']  # Year
        gender = person['kon']  # kvinna / man
        surname = person['efternamn']
        forename = person['tilltalsnamn']
        disambiguation = person['iort']  # "Helene Petersson i Stockaryd"
        party = person['parti']  # Acronym
        constituency = person['valkrets']
        id = person['intressent_id']
        # status = person['status']  # Mostly MP, occasional vice-president, active replacement, Cabinet office
        # sortname = person['sorteringsnamn']

        name = '%s %s' % (forename, surname)
        if disambiguation:
            name += ' i %s' % disambiguation

        twitter = facebook = email = phone = website = None

        if isinstance(person["personuppgift"]['uppgift'], dict):
            person["personuppgift"]['uppgift'] = [person["personuppgift"]['uppgift']]
        for link in person["personuppgift"]['uppgift']:
            code = link['kod']  # Swedish term e.g. Webbsida, Officiell e-postadress, Tjänstetelefon
            value = link['uppgift']
            # typ = link['typ']  # eadress/telefonnummer/titlar(kod=lang)/val(kod=KandiderarINastaVal/uppgift=true)
            if code == 'Webbsida':
                website = value
            elif code == 'Officiell e-postadress':
                email = value.replace(u'[på]', '@')
            elif code == u'Tjänstetelefon':
                phone = value
            elif code == u'Övriga webbsidor':
                if 'facebook' in value:
                    facebook = value
                elif 'twitter' in value:
                    twitter = value

        seen = False
        for post in person['personuppdrag']['uppdrag']:
            if post['organ_kod'] != 'kam' or post['roll_kod'] not in ('Riksdagsledamot', u'Ersättare', u'Statsrådsersättare', u'Talmansersättare'):
                # Any roll_kod except the three vice talman
                continue
            # TODO: Only handles current posts! Ignores dates!
            if not post['from'] <= TODAY <= post['tom']:
                continue
            if seen:
                raise Exception("Only deals with one post!")
            seen = True
            # post['roll_kod']  # Andre/Forste/Tredje vice talman, Ersattare, Fiksdagsledamot, Statsrådsersättare, Talmansersättare
            # post['status']  # Ersättare, Ledig Ersättare, Ledig, Tjänstgörande
            # post['typ']  # kammaruppdrag, talmansuppdrag
            # post['from']
            # post['tom']
            # post['ordningsnummer']
            # post['uppgift']
            # post['sortering']
            # post["organ_sortering"]
            # post["uppdrag_rollsortering"]
            # post["uppdrag_statussortering"]
            data = {
                'id': id,
                'name': name,
                'image': image,
                'gender': GENDER[gender],
                'year_of_birth': dob,
                'area': constituency,
                'area_id': area_id(constituency),
                'party_id': party,
                'party': PARTY[party],
                'twitter': twitter,
                'facebook': facebook,
                'web': website,
                'phone': phone,
                'email': email,
                'term': t['id'],
                'source': t['source']
            }
            scraperwiki.sqlite.save(['name', 'term'], data)

        if not seen:
            print "Did not output anything for %s" % name
            sys.exit(1)

def area_id(area):
    return 'ocd-division/country:se/constituency:%s' % area.lower().replace(' ', '-')


terms = [
    {
        'id': 2014,
        'name': '2014 election',
        'start_date': '2014-09-14',
        'source': 'http://data.riksdagen.se/',
    },
]
scraperwiki.sqlite.save(['id'], terms, 'terms')

# TODO: This actually scrapes just current people, so don't do it in a loop
for term in terms:
    scrape_term(term)
