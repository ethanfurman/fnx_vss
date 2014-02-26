from VSS.utils import translator, AutoEnum
building_subs = set([
    '#','APARTMENT','APT','BLDG','BUILDING','CONDO','FL','FLR','FLOOR','LOT','LOWER','NO','NUM','NUMBER',
    'RM','ROOM','SLIP','SLP','SPACE','SP','SPC','STE','SUITE','TRLR','UNIT','UPPER',
    ])
caps_okay = set(['UCLA', 'OHSU', 'IBM', 'LLC', 'USA', 'NASA'])
lower_okay = set(['dba', 'c/o', 'attn'])


mixed_case_names = {
    'aj'        : 'AJ',
    'bj'        : 'BJ',
    'cj'        : 'CJ',
    'deangelis' : 'DeAngelis',
    'decarlo'   : 'DeCarlo',
    'decosta'   : 'DeCosta',
    'decristoforo' : 'DeCristoforo',
    'deferrari' : 'DeFerrari',
    'degrandpre': 'DeGrandpre',
    'degroat'   : 'DeGroat',
    'delucia'   : 'DeLucia',
    'denardis'  : 'DeNardis',
    'denorch'   : 'DeNorch',
    'depaola'   : 'DePaola',
    'deprez'    : 'DePrez',
    'deshields' : 'DeShields',
    'deshon'    : 'DeShon',
    'desousa'   : 'deSousa',
    'devet'     : 'DeVet',
    'devida'    : 'DeVida',
    'devore'    : 'DeVore',
    'difrederico':'DiFrederico',
    'diponziano': 'DiPonziano',
    'jd'        : 'JD',
    'jj'        : 'JJ',
    'joann'     : 'JoAnn',
    'joanne'    : 'JoAnne',
    'jodee'     : 'JoDee',
    'jp'        : 'JP',
    'jumaal'    : 'JuMaal',
    'delany'    : 'DeLany',
    'demerritt' : 'DeMerritt',
    'dewaal'    : 'DeWaal',
    'lamon'     : 'LaMon',
    'lebarron'  : 'LeBarron',
    'leeanne'   : 'LeeAnne',
    'maryjo'    : 'MaryJo',
    'tachelle'  : 'TaChelle',
    'tj'        : 'TJ',
    }

us_ca_state_abbr = {
    'AB' : 'ALBERTA' ,
    'AK' : 'ALASKA' ,
    'AL' : 'ALABAMA' ,
    'AR' : 'ARKANSAS' ,
    'AS' : 'AMERICAN SAMOA' ,
    'AZ' : 'ARIZONA' ,
    'BC' : 'BRITISH COLUMBIA' ,
    'CA' : 'CALIFORNIA' ,
    'CO' : 'COLORADO' ,
    'CT' : 'CONNECTICUT' ,
    'DC' : 'DISTRICT OF COLUMBIA' ,
    'DE' : 'DELAWARE' ,
    'FL' : 'FLORIDA' ,
    'FM' : 'FEDERATED STATES OF MICRONESIA' ,
    'GA' : 'GEORGIA' ,
    'GU' : 'GUAM' ,
    'HI' : 'HAWAII' ,
    'IA' : 'IOWA' ,
    'ID' : 'IDAHO' ,
    'IL' : 'ILLINOIS' ,
    'IN' : 'INDIANA' ,
    'KS' : 'KANSAS' ,
    'KY' : 'KENTUCKY' ,
    'LA' : 'LOUISIANA' ,
    'MA' : 'MASSACHUSETTS' ,
    'MB' : 'MANITOBA' ,
    'MD' : 'MARYLAND' ,
    'ME' : 'MAINE' ,
    'MH' : 'MARSHALL ISLANDS' ,
    'MI' : 'MICHIGAN' ,
    'MN' : 'MINNESOTA' ,
    'MO' : 'MISSOURI' ,
    'MP' : 'NORTHERN MARIANA ISLANDS' ,
    'MS' : 'MISSISSIPPI' ,
    'MT' : 'MONTANA' ,
    'NB' : 'NEW BRUNSWICK' ,
    'NC' : 'NORTH CAROLINA' ,
    'ND' : 'NORTH DAKOTA' ,
    'NE' : 'NEBRASKA' ,
    'NH' : 'NEW HAMPSHIRE' ,
    'NJ' : 'NEW JERSEY' ,
    'NL' : 'NEWFOUNDLAND' ,
    'NM' : 'NEW MEXICO' ,
    'NS' : 'NOVA SCOTIA' ,
    'NT' : 'NORTHWEST TERRITORY' ,
    'NU' : 'NUNAVUT' ,
    'NV' : 'NEVADA' ,
    'NY' : 'NEW YORK' ,
    'OH' : 'OHIO' ,
    'OK' : 'OKLAHOMA' ,
    'ON' : 'ONTARIO' ,
    'OR' : 'OREGON' ,
    'PA' : 'PENNSYLVANIA' ,
    'PE' : 'PRINCE EDWARD ISLAND' ,
    'PR' : 'PUERTO RICO' ,
    'PW' : 'PALAU' ,
    'QC' : 'QUEBEC' ,
    'RI' : 'RHODE ISLAND' ,
    'SC' : 'SOUTH CAROLINA' ,
    'SD' : 'SOUTH DAKOTA' ,
    'SK' : 'SASKATCHEWAN' ,
    'TN' : 'TENNESSEE' ,
    'TX' : 'TEXAS' ,
    'UT' : 'UTAH' ,
    'VA' : 'VIRGINIA' ,
    'VI' : 'VIRGIN ISLANDS' ,
    'VT' : 'VERMONT' ,
    'WA' : 'WASHINGTON' ,
    'WI' : 'WISCONSIN' ,
    'WV' : 'WEST VIRGINIA' ,
    'WY' : 'WYOMING' ,
    'YT' : 'YUKON' ,
    }
us_ca_state_name = dict([(v, k) for k, v in us_ca_state_abbr.items()])

ca_province_abbr = {
    'AB' : 'ALBERTA' ,
    'BC' : 'BRITISH COLUMBIA' ,
    'MB' : 'MANITOBA' ,
    'NB' : 'NEW BRUNSWICK' ,
    'NL' : 'NEWFOUNDLAND' ,
    'NS' : 'NOVA SCOTIA' ,
    'NT' : 'NORTHWEST TERRITORY' ,
    'NU' : 'NUNAVUT' ,
    'ON' : 'ONTARIO' ,
    'PE' : 'PRINCE EDWARD ISLAND' ,
    'QC' : 'QUEBEC' ,
    'SK' : 'SASKATCHEWAN' ,
    'YT' : 'YUKON' ,
    }
ca_province_name = dict([(v, k) for k, v in ca_province_abbr.items()])

addr_abbr = {
        'rd.'       : 'road',
        'rd'        : 'road',
        'st.'       : 'street',
        'st'        : 'street',
        'ste'       : 'suite',
        'ste.'      : 'suite',
        'ave.'      : 'avenue',
        'blvd.'     : 'boulevard',
        'blvd'      : 'boulevard',
        'e.'        : 'e',
        'east'      : 'e',
        'w.'        : 'w',
        'west'      : 'w',
        'n.'        : 'n',
        'north'     : 'n',
        's.'        : 's',
        'south'     : 's',
        'ne.'       : 'ne',
        'northeast' : 'ne',
        'se.'       : 'se',
        'southeast' : 'se',
        'nw.'       : 'nw',
        'northwest' : 'nw',
        'sw.'       : 'sw',
        'southwest' : 'sw',
        'so.'       : 's',
        'highway'   : 'hwy',
        'hwy.'      : 'hwy',
        'building'  : 'bldg',
        'bldg.'     : 'bldg',
        'ln.'       : 'lane',
        'apt.'      : 'apt',
        'apartment' : 'apt',
        'p.o.'      : 'po',
        'p.o'       : 'po',
        'po.'       : 'po',
        'p.o.box'   : 'po box',
        'po.box'    : 'po box',
        'pobox'     : 'po box',
        'pob'       : 'po box',
        }

bsns_abbr = {
        'inc.'      : 'incorporated',
        'inc'       : 'incorporated',
        'co.'       : 'company',
        'co'        : 'company',
        'corp.'     : 'corporation',
        'corp'      : 'corporation',
        'dept.'     : 'department',
        'dept'      : 'department',
        'ltd.'      : 'limited',
        'ltd'       : 'limited',
        }

country_abbr = {
    "AF":  "AFGHANISTAN",
    "AX":  "ALAND ISLANDS",
    "AL":  "ALBANIA",
    "DZ":  "ALGERIA",
    "AS":  "AMERICAN SAMOA",
    "AD":  "ANDORRA",
    "AO":  "ANGOLA",
    "AI":  "ANGUILLA",
    "AQ":  "ANTARCTICA",
    "AG":  "ANTIGUA AND BARBUDA",
    "AR":  "ARGENTINA",
    "AM":  "ARMENIA",
    "AW":  "ARUBA",
    "AU":  "AUSTRALIA",
    "AT":  "AUSTRIA",
    "AZ":  "AZERBAIJAN",
    "BS":  "BAHAMAS",
    "BH":  "BAHRAIN",
    "BD":  "BANGLADESH",
    "BB":  "BARBADOS",
    "BY":  "BELARUS",
    "BE":  "BELGIUM",
    "BZ":  "BELIZE",
    "BJ":  "BENIN",
    "BM":  "BERMUDA",
    "BT":  "BHUTAN",
    "BO":  "BOLIVIA, PLURINATIONAL STATE OF",
    "BQ":  "BONAIRE, SINT EUSTATIUS AND SABA",
    "BA":  "BOSNIA AND HERZEGOVINA",
    "BW":  "BOTSWANA",
    "BV":  "BOUVET ISLAND",
    "BR":  "BRAZIL",
    "IO":  "BRITISH INDIAN OCEAN TERRITORY",
    "BN":  "BRUNEI DARUSSALAM",
    "BG":  "BULGARIA",
    "BF":  "BURKINA FASO",
    "BI":  "BURUNDI",
    "KH":  "CAMBODIA",
    "CM":  "CAMEROON",
    "CA":  "CANADA",
    "CV":  "CAPE VERDE",
    "KY":  "CAYMAN ISLANDS",
    "CF":  "CENTRAL AFRICAN REPUBLIC",
    "TD":  "CHAD",
    "CL":  "CHILE",
    "CN":  "CHINA",
    "CX":  "CHRISTMAS ISLAND",
    "CC":  "COCOS (KEELING) ISLANDS",
    "CO":  "COLOMBIA",
    "KM":  "COMOROS",
    "CG":  "CONGO",
    "CD":  "CONGO, THE DEMOCRATIC REPUBLIC OF THE",
    "CK":  "COOK ISLANDS",
    "CR":  "COSTA RICA",
    "CI":  "IVORY COAST",
    "HR":  "CROATIA",
    "CU":  "CUBA",
    "CW":  "CURACAO",
    "CY":  "CYPRUS",
    "CZ":  "CZECH REPUBLIC",
    "DK":  "DENMARK",
    "DJ":  "DJIBOUTI",
    "DM":  "DOMINICA",
    "DO":  "DOMINICAN REPUBLIC",
    "EC":  "ECUADOR",
    "EG":  "EGYPT",
    "SV":  "EL SALVADOR",
    "GQ":  "EQUATORIAL GUINEA",
    "ER":  "ERITREA",
    "EE":  "ESTONIA",
    "ET":  "ETHIOPIA",
    "FK":  "FALKLAND ISLANDS (MALVINAS)",
    "FO":  "FAROE ISLANDS",
    "FJ":  "FIJI",
    "FI":  "FINLAND",
    "FR":  "FRANCE",
    "GF":  "FRENCH GUIANA",
    "PF":  "FRENCH POLYNESIA",
    "TF":  "FRENCH SOUTHERN TERRITORIES",
    "GA":  "GABON",
    "GM":  "GAMBIA",
    "GE":  "GEORGIA",
    "DE":  "GERMANY",
    "GH":  "GHANA",
    "GI":  "GIBRALTAR",
    "GR":  "GREECE",
    "GL":  "GREENLAND",
    "GD":  "GRENADA",
    "GP":  "GUADELOUPE",
    "GU":  "GUAM",
    "GT":  "GUATEMALA",
    "GG":  "GUERNSEY",
    "GN":  "GUINEA",
    "GW":  "GUINEA-BISSAU",
    "GY":  "GUYANA",
    "HT":  "HAITI",
    "HM":  "HEARD ISLAND AND MCDONALD ISLANDS",
    "VA":  "HOLY SEE (VATICAN CITY STATE)",
    "HN":  "HONDURAS",
    "HK":  "HONG KONG",
    "HU":  "HUNGARY",
    "IS":  "ICELAND",
    "IN":  "INDIA",
    "ID":  "INDONESIA",
    "IR":  "IRAN, ISLAMIC REPUBLIC OF",
    "IQ":  "IRAQ",
    "IE":  "IRELAND",
    "IM":  "ISLE OF MAN",
    "IL":  "ISRAEL",
    "IT":  "ITALY",
    "JM":  "JAMAICA",
    "JP":  "JAPAN",
    "JE":  "JERSEY",
    "JO":  "JORDAN",
    "KZ":  "KAZAKHSTAN",
    "KE":  "KENYA",
    "KI":  "KIRIBATI",
    "KP":  "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF",
    "KR":  "KOREA, REPUBLIC OF",
    "KW":  "KUWAIT",
    "KG":  "KYRGYZSTAN",
    "LA":  "LAO PEOPLE'S DEMOCRATIC REPUBLIC",
    "LV":  "LATVIA",
    "LB":  "LEBANON",
    "LS":  "LESOTHO",
    "LR":  "LIBERIA",
    "LY":  "LIBYA",
    "LI":  "LIECHTENSTEIN",
    "LT":  "LITHUANIA",
    "LU":  "LUXEMBOURG",
    "MO":  "MACAO",
    "MK":  "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF",
    "MG":  "MADAGASCAR",
    "MW":  "MALAWI",
    "MY":  "MALAYSIA",
    "MV":  "MALDIVES",
    "ML":  "MALI",
    "MT":  "MALTA",
    "MH":  "MARSHALL ISLANDS",
    "MQ":  "MARTINIQUE",
    "MR":  "MAURITANIA",
    "MU":  "MAURITIUS",
    "YT":  "MAYOTTE",
    "MX":  "MEXICO",
    "FM":  "MICRONESIA, FEDERATED STATES OF",
    "MD":  "MOLDOVA, REPUBLIC OF",
    "MC":  "MONACO",
    "MN":  "MONGOLIA",
    "ME":  "MONTENEGRO",
    "MS":  "MONTSERRAT",
    "MA":  "MOROCCO",
    "MZ":  "MOZAMBIQUE",
    "MM":  "MYANMAR",
    "NA":  "NAMIBIA",
    "NR":  "NAURU",
    "NP":  "NEPAL",
    "NL":  "NETHERLANDS",
    "NC":  "NEW CALEDONIA",
    "NZ":  "NEW ZEALAND",
    "NI":  "NICARAGUA",
    "NE":  "NIGER",
    "NG":  "NIGERIA",
    "NU":  "NIUE",
    "NF":  "NORFOLK ISLAND",
    "MP":  "NORTHERN MARIANA ISLANDS",
    "NO":  "NORWAY",
    "OM":  "OMAN",
    "PK":  "PAKISTAN",
    "PW":  "PALAU",
    "PS":  "PALESTINE, STATE OF",
    "PA":  "PANAMA",
    "PG":  "PAPUA NEW GUINEA",
    "PY":  "PARAGUAY",
    "PE":  "PERU",
    "PH":  "PHILIPPINES",
    "PN":  "PITCAIRN",
    "PL":  "POLAND",
    "PT":  "PORTUGAL",
    "PR":  "PUERTO RICO",
    "QA":  "QATAR",
    "RE":  "REUNION",
    "RO":  "ROMANIA",
    "RU":  "RUSSIAN FEDERATION",
    "RW":  "RWANDA",
    "BL":  "SAINT BARTHELEMY",
    "SH":  "SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA",
    "KN":  "SAINT KITTS AND NEVIS",
    "LC":  "SAINT LUCIA",
    "MF":  "SAINT MARTIN (FRENCH PART)",
    "PM":  "SAINT PIERRE AND MIQUELON",
    "VC":  "SAINT VINCENT AND THE GRENADINES",
    "WS":  "SAMOA",
    "SM":  "SAN MARINO",
    "ST":  "SAO TOME AND PRINCIPE",
    "SA":  "SAUDI ARABIA",
    "SN":  "SENEGAL",
    "RS":  "SERBIA",
    "SC":  "SEYCHELLES",
    "SL":  "SIERRA LEONE",
    "SG":  "SINGAPORE",
    "SX":  "SINT MAARTEN (DUTCH PART)",
    "SK":  "SLOVAKIA",
    "SI":  "SLOVENIA",
    "SB":  "SOLOMON ISLANDS",
    "SO":  "SOMALIA",
    "ZA":  "SOUTH AFRICA",
    "GS":  "SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS",
    "SS":  "SOUTH SUDAN",
    "ES":  "SPAIN",
    "LK":  "SRI LANKA",
    "SD":  "SUDAN",
    "SR":  "SURINAME",
    "SJ":  "SVALBARD AND JAN MAYEN",
    "SZ":  "SWAZILAND",
    "SE":  "SWEDEN",
    "CH":  "SWITZERLAND",
    "SY":  "SYRIAN ARAB REPUBLIC",
    "TW":  "TAIWAN, PROVINCE OF CHINA",
    "TJ":  "TAJIKISTAN",
    "TZ":  "TANZANIA, UNITED REPUBLIC OF",
    "TH":  "THAILAND",
    "TL":  "TIMOR-LESTE",
    "TG":  "TOGO",
    "TK":  "TOKELAU",
    "TO":  "TONGA",
    "TT":  "TRINIDAD AND TOBAGO",
    "TN":  "TUNISIA",
    "TR":  "TURKEY",
    "TM":  "TURKMENISTAN",
    "TC":  "TURKS AND CAICOS ISLANDS",
    "TV":  "TUVALU",
    "UG":  "UGANDA",
    "UA":  "UKRAINE",
    "AE":  "UNITED ARAB EMIRATES",
    "UK":  "UNITED KINGDOM",
    "GB":  "UNITED KINGDOM",
    "ENGLAND":  "UNITED KINGDOM",
    "US":  "UNITED STATES",
    "UM":  "UNITED STATES MINOR OUTLYING ISLANDS",
    "UY":  "URUGUAY",
    "UZ":  "UZBEKISTAN",
    "VU":  "VANUATU",
    "VE":  "VENEZUELA, BOLIVARIAN REPUBLIC OF",
    "VN":  "VIET NAM",
    "VG":  "VIRGIN ISLANDS, BRITISH",
    "VI":  "VIRGIN ISLANDS, U.S.",
    "WF":  "WALLIS AND FUTUNA",
    "EH":  "WESTERN SAHARA",
    "YE":  "YEMEN",
    "ZM":  "ZAMBIA",
    "ZW":  "ZIMBABWE",
    }
country_name = dict([(v, k) for k, v in country_abbr.items()])


def cszk(line1, line2):
    """
    parses two lines of text into blah, city, state, zip, country

    supported formats:
      line1: city (state)
      line2: zip zip country

      line1: ...
      line2: city state zip zip country

      line1: city state zip zip
      line2: country

      line1: ...
      line2: city, state zip zip

      returns street, city, state, zip, country; but state is only
      populated if country is US or CA
    """
    line1 = re.sub(r'\b[A-Z]\.[A-Z]\.[^A-Z]', lambda s: s.group().replace('.',''), line1)
    line2 = re.sub(r'\b[A-Z]\.[A-Z]\.[^A-Z]', lambda s: s.group().replace('.',''), line2)
    line1, line2 = Sift(line1.replace('.',' ').replace(',',' '), line2.replace('.',' ').replace(',',' '))
    line1 = ' '.join(line1.split())
    line2 = ' '.join(line2.split())
    street = city = state = postal = country = ''
    try:
        pieces, line2 = line2.split(), ''
        k = kountry = ''
        while pieces:
            new_k = pieces.pop().upper()
            if has_digits(new_k):
                city = k
                pieces.append(new_k)
                break
            k = (new_k + ' ' + k).strip()
            if k in country_abbr:
                k, kountry = country_abbr[k], k
            if k in country_name:
                country = k
                if pieces and pieces[-1].upper() == 'THE':
                    pieces.pop()
                break
            else:
                # check for a state
                if k in us_ca_state_abbr:
                    k = us_ca_state_abbr[k]
                if k in us_ca_state_name:
                    state = k
                    break
        else:
            pieces = k.split()
        if not pieces:
            pieces, line1 = line1.split(), ''
        if has_digits(pieces[-1]) or len(pieces[-1]) == 3:  # zip code!
            if len(pieces) > 1 and (has_digits(pieces[-2]) or len(pieces[-2]) == 3):
                postal = PostalCode(' '.join(pieces[-2:]), country=country)
                pieces.pop(); pieces.pop()
            else:
                postal = PostalCode(pieces.pop(), country=country)
        if not pieces:
            pieces, line1 = line1.split(), ''
        if not country and pieces[-1] == 'CANADA' and (len(pieces) == 1 or pieces[-2] != 'OF'):
            country = 'CANADA'
            pieces.pop()
        elif not country and pieces[-1] not in us_ca_state_abbr and (
                pieces[-1] in country_name or pieces[-1] in country_abbr):
            country = country_abbr.get(pieces[-1], pieces[-1])
            pieces.pop()
        if not pieces:
            pieces, line1 = line1.split(), ''
        if country not in ('CANADA', ''):
            city = (' '.join(pieces) + city).strip(' ,')
            pieces = []
        else:
            s = pieces.pop()  # now looking for a state
            while s not in us_ca_state_abbr and s not in us_ca_state_name:
                if s[-1] == ')':
                    if s[0] == '(':
                        s = s[1:-1]
                        continue
                elif pieces and pieces[-1][-1:] == ',':
                    break
                if pieces:
                    s = (pieces.pop() + ' ' + s).strip()
                    if len(s) == 3 and s[1] == ' ':
                        s = s[0] + s[2]
                else:
                    break
            if s in us_ca_state_abbr:
                s = us_ca_state_abbr[s]
            if s in us_ca_state_name:
                state = s
            else:
                city = (s + ' ' + city).strip(', ')
        # see if state is canadian
        if state in ca_province_name and not country:
            country = 'CANADA'
        # if state is empty but we have a country, check that country abbreviation is not a state
        if country and not state:
            if kountry in us_ca_state_abbr:
                state = us_ca_state_abbr[kountry]
                country = ''
        if pieces:
            city = (' '.join(pieces) + ' ' + city).strip(', ')
            pieces[:] = []
        if city : # early bail
            street, line1 = line1, ''
            return street, city, state, postal, country
        else:
            city, line1 = line1.strip(', '), ''
            return street, city, state, postal, country
    except IndexError:
        if line1 or line2 or pieces:
            raise
        return street, city, state, postal, country


usps_street_suffix_common = {
	'ALLEE'      :  'ALLEY',
	'ALLEY'      :  'ALLEY',
	'ALLY'       :  'ALLEY',
	'ALY'        :  'ALLEY',
	'ANEX'       :  'ANNEX',
	'ANNEX'      :  'ANNEX',
	'ANNEX'      :  'ANNEX',
	'ANX'        :  'ANNEX',
	'ARC'        :  'ARCADE',
	'ARCADE'     :  'ARCADE',
	'AV'         :  'AVENUE',
	'AVE'        :  'AVENUE',
	'AVEN'       :  'AVENUE',
	'AVENU'      :  'AVENUE',
	'AVENUE'     :  'AVENUE',
	'AVN'        :  'AVENUE',
	'AVNUE'      :  'AVENUE',
	'BAYOO'      :  'BAYOO',
	'BAYOU'      :  'BAYOO',
	'BCH'        :  'BEACH',
	'BEACH'      :  'BEACH',
	'BEND'       :  'BEND',
	'BND'        :  'BEND',
	'BLF'        :  'BLUFF',
	'BLUF'       :  'BLUFF',
	'BLUFF'      :  'BLUFF',
	'BLUFFS'     :  'BLUFFS',
	'BOT'        :  'BOTTOM',
	'BOTTM'      :  'BOTTOM',
	'BOTTOM'     :  'BOTTOM',
	'BTM'        :  'BOTTOM',
	'BLVD'       :  'BOULEVARD',
	'BOUL'       :  'BOULEVARD',
	'BOULEVARD'  :  'BOULEVARD',
	'BOULV'      :  'BOULEVARD',
	'BR'         :  'BRANCH',
	'BRANCH'     :  'BRANCH',
	'BRNCH'      :  'BRANCH',
	'BRDGE'      :  'BRIDGE',
	'BRG'        :  'BRIDGE',
	'BRIDGE'     :  'BRIDGE',
	'BRK'        :  'BROOK',
	'BROOK'      :  'BROOK',
	'BROOKS'     :  'BROOKS',
	'BURG'       :  'BURG',
	'BURGS'      :  'BURGS',
	'BYP'        :  'BYPASS',
	'BYPA'       :  'BYPASS',
	'BYPAS'      :  'BYPASS',
	'BYPASS'     :  'BYPASS',
	'BYPS'       :  'BYPASS',
	'CAMP'       :  'CAMP',
	'CMP'        :  'CAMP',
	'CP'         :  'CAMP',
	'CANYN'      :  'CANYON',
	'CANYON'     :  'CANYON',
	'CNYN'       :  'CANYON',
	'CYN'        :  'CANYON',
	'CAPE'       :  'CAPE',
	'CPE'        :  'CAPE',
	'CAUSEWAY'   :  'CAUSEWAY',
	'CAUSWAY'    :  'CAUSEWAY',
	'CSWY'       :  'CAUSEWAY',
	'CEN'        :  'CENTER',
	'CENT'       :  'CENTER',
	'CENTER'     :  'CENTER',
	'CENTR'      :  'CENTER',
	'CENTRE'     :  'CENTER',
	'CNTER'      :  'CENTER',
	'CNTR'       :  'CENTER',
	'CTR'        :  'CENTER',
	'CENTERS'    :  'CENTERS',
	'CIR'        :  'CIRCLE',
	'CIRC'       :  'CIRCLE',
	'CIRCL'      :  'CIRCLE',
	'CIRCLE'     :  'CIRCLE',
	'CRCL'       :  'CIRCLE',
	'CRCLE'      :  'CIRCLE',
	'CIRCLES'    :  'CIRCLES',
	'CLF'        :  'CLIFF',
	'CLIFF'      :  'CLIFF',
	'CLFS'       :  'CLIFFS',
	'CLIFFS'     :  'CLIFFS',
	'CLB'        :  'CLUB',
	'CLUB'       :  'CLUB',
	'COMMON'     :  'COMMON',
	'COR'        :  'CORNER',
	'CORNER'     :  'CORNER',
	'CORNERS'    :  'CORNERS',
	'CORS'       :  'CORNERS',
	'COURSE'     :  'COURSE',
	'CRSE'       :  'COURSE',
	'COURT'      :  'COURT',
	'CRT'        :  'COURT',
	'CT'         :  'COURT',
	'COURTS'     :  'COURTS',
	'CT'         :  'COURTS',
	'COVE'       :  'COVE',
	'CV'         :  'COVE',
	'COVES'      :  'COVES',
	'CK'         :  'CREEK',
	'CR'         :  'CREEK',
	'CREEK'      :  'CREEK',
	'CRK'        :  'CREEK',
	'CRECENT'    :  'CRESCENT',
	'CRES'       :  'CRESCENT',
	'CRESCENT'   :  'CRESCENT',
	'CRESENT'    :  'CRESCENT',
	'CRSCNT'     :  'CRESCENT',
	'CRSENT'     :  'CRESCENT',
	'CRSNT'      :  'CRESCENT',
	'CREST'      :  'CREST',
	'CROSSING'   :  'CROSSING',
	'CRSSING'    :  'CROSSING',
	'CRSSNG'     :  'CROSSING',
	'XING'       :  'CROSSING',
	'CROSSROAD'  :  'CROSSROAD',
	'CURVE'      :  'CURVE',
	'DALE'       :  'DALE',
	'DL'         :  'DALE',
	'DAM'        :  'DAM',
	'DM'         :  'DAM',
	'DIV'        :  'DIVIDE',
	'DIVIDE'     :  'DIVIDE',
	'DV'         :  'DIVIDE',
	'DVD'        :  'DIVIDE',
	'DR'         :  'DRIVE',
	'DRIV'       :  'DRIVE',
	'DRIVE'      :  'DRIVE',
	'DRV'        :  'DRIVE',
	'DRIVES'     :  'DRIVES',
	'EST'        :  'ESTATE',
	'ESTATE'     :  'ESTATE',
	'ESTATES'    :  'ESTATES',
	'ESTS'       :  'ESTATES',
	'EXP'        :  'EXPRESSWAY',
	'EXPR'       :  'EXPRESSWAY',
	'EXPRESS'    :  'EXPRESSWAY',
	'EXPRESSWAY' :  'EXPRESSWAY',
	'EXPW'       :  'EXPRESSWAY',
	'EXPY'       :  'EXPRESSWAY',
	'EXT'        :  'EXTENSION',
	'EXTENSION'  :  'EXTENSION',
	'EXTN'       :  'EXTENSION',
	'EXTNSN'     :  'EXTENSION',
	'EXTENSIONS' :  'EXTENSIONS',
	'EXTS'       :  'EXTENSIONS',
	'FALL'       :  'FALL',
	'FALLS'      :  'FALLS',
	'FLS'        :  'FALLS',
	'FERRY'      :  'FERRY',
	'FRRY'       :  'FERRY',
	'FRY'        :  'FERRY',
	'FIELD'      :  'FIELD',
	'FLD'        :  'FIELD',
	'FIELDS'     :  'FIELDS',
	'FLDS'       :  'FIELDS',
	'FLAT'       :  'FLAT',
	'FLT'        :  'FLAT',
	'FLATS'      :  'FLATS',
	'FLTS'       :  'FLATS',
	'FORD'       :  'FORD',
	'FRD'        :  'FORD',
	'FORDS'      :  'FORDS',
	'FOREST'     :  'FOREST',
	'FORESTS'    :  'FOREST',
	'FRST'       :  'FOREST',
	'FORG'       :  'FORGE',
	'FORGE'      :  'FORGE',
	'FRG'        :  'FORGE',
	'FORGES'     :  'FORGES',
	'FORK'       :  'FORK',
	'FRK'        :  'FORK',
	'FORKS'      :  'FORKS',
	'FRKS'       :  'FORKS',
	'FORT'       :  'FORT',
	'FRT'        :  'FORT',
	'FT'         :  'FORT',
	'FREEWAY'    :  'FREEWAY',
	'FREEWY'     :  'FREEWAY',
	'FRWAY'      :  'FREEWAY',
	'FRWY'       :  'FREEWAY',
	'FWY'        :  'FREEWAY',
	'GARDEN'     :  'GARDEN',
	'GARDN'      :  'GARDEN',
	'GDN'        :  'GARDEN',
	'GRDEN'      :  'GARDEN',
	'GRDN'       :  'GARDEN',
	'GARDENS'    :  'GARDENS',
	'GDNS'       :  'GARDENS',
	'GRDNS'      :  'GARDENS',
	'GATEWAY'    :  'GATEWAY',
	'GATEWY'     :  'GATEWAY',
	'GATWAY'     :  'GATEWAY',
	'GTWAY'      :  'GATEWAY',
	'GTWY'       :  'GATEWAY',
	'GLEN'       :  'GLEN',
	'GLN'        :  'GLEN',
	'GLENS'      :  'GLENS',
	'GREEN'      :  'GREEN',
	'GRN'        :  'GREEN',
	'GREENS'     :  'GREENS',
	'GROV'       :  'GROVE',
	'GROVE'      :  'GROVE',
	'GRV'        :  'GROVE',
	'GROVES'     :  'GROVES',
	'HARB'       :  'HARBOR',
	'HARBOR'     :  'HARBOR',
	'HARBR'      :  'HARBOR',
	'HBR'        :  'HARBOR',
	'HRBOR'      :  'HARBOR',
	'HARBORS'    :  'HARBORS',
	'HAVEN'      :  'HAVEN',
	'HAVN'       :  'HAVEN',
	'HVN'        :  'HAVEN',
	'HEIGHT'     :  'HEIGHTS',
	'HEIGHTS'    :  'HEIGHTS',
	'HGTS'       :  'HEIGHTS',
	'HT'         :  'HEIGHTS',
	'HTS'        :  'HEIGHTS',
	'HIGHWAY'    :  'HIGHWAY',
	'HIGHWY'     :  'HIGHWAY',
	'HIWAY'      :  'HIGHWAY',
	'HIWY'       :  'HIGHWAY',
	'HWAY'       :  'HIGHWAY',
	'HWY'        :  'HIGHWAY',
	'HILL'       :  'HILL',
	'HL'         :  'HILL',
	'HILLS'      :  'HILLS',
	'HLS'        :  'HILLS',
	'HLLW'       :  'HOLLOW',
	'HOLLOW'     :  'HOLLOW',
	'HOLLOWS'    :  'HOLLOW',
	'HOLW'       :  'HOLLOW',
	'HOLWS'      :  'HOLLOW',
	'INLET'      :  'INLET',
	'INLT'       :  'INLET',
	'IS'         :  'ISLAND',
	'ISLAND'     :  'ISLAND',
	'ISLND'      :  'ISLAND',
	'ISLANDS'    :  'ISLANDS',
	'ISLNDS'     :  'ISLANDS',
	'ISS'        :  'ISLANDS',
	'ISLE'       :  'ISLE',
	'ISLES'      :  'ISLE',
	'JCT'        :  'JUNCTION',
	'JCTION'     :  'JUNCTION',
	'JCTN'       :  'JUNCTION',
	'JUNCTION'   :  'JUNCTION',
	'JUNCTN'     :  'JUNCTION',
	'JUNCTON'    :  'JUNCTION',
	'JCTNS'      :  'JUNCTIONS',
	'JCTS'       :  'JUNCTIONS',
	'JUNCTIONS'  :  'JUNCTIONS',
	'KEY'        :  'KEY',
	'KY'         :  'KEY',
	'KEYS'       :  'KEYS',
	'KYS'        :  'KEYS',
	'KNL'        :  'KNOLL',
	'KNOL'       :  'KNOLL',
	'KNOLL'      :  'KNOLL',
	'KNLS'       :  'KNOLLS',
	'KNOLLS'     :  'KNOLLS',
	'LAKE'       :  'LAKE',
	'LK'         :  'LAKE',
	'LAKES'      :  'LAKES',
	'LKS'        :  'LAKES',
	'LAND'       :  'LAND',
	'LANDING'    :  'LANDING',
	'LNDG'       :  'LANDING',
	'LNDNG'      :  'LANDING',
	'LA'         :  'LANE',
	'LANE'       :  'LANE',
	'LANES'      :  'LANE',
	'LN'         :  'LANE',
	'LGT'        :  'LIGHT',
	'LIGHT'      :  'LIGHT',
	'LIGHTS'     :  'LIGHTS',
	'LF'         :  'LOAF',
	'LOAF'       :  'LOAF',
	'LCK'        :  'LOCK',
	'LOCK'       :  'LOCK',
	'LCKS'       :  'LOCKS',
	'LOCKS'      :  'LOCKS',
	'LDG'        :  'LODGE',
	'LDGE'       :  'LODGE',
	'LODG'       :  'LODGE',
	'LODGE'      :  'LODGE',
	'LOOP'       :  'LOOP',
	'LOOPS'      :  'LOOP',
	'MALL'       :  'MALL',
	'MANOR'      :  'MANOR',
	'MNR'        :  'MANOR',
	'MANORS'     :  'MANORS',
	'MNRS'       :  'MANORS',
	'MDW'        :  'MEADOW',
	'MEADOW'     :  'MEADOW',
	'MDWS'       :  'MEADOWS',
	'MEADOWS'    :  'MEADOWS',
	'MEDOWS'     :  'MEADOWS',
	'MEWS'       :  'MEWS',
	'MILL'       :  'MILL',
	'ML'         :  'MILL',
	'MILLS'      :  'MILLS',
	'MLS'        :  'MILLS',
	'MISSION'    :  'MISSION',
	'MISSN'      :  'MISSION',
	'MSN'        :  'MISSION',
	'MSSN'       :  'MISSION',
	'MOTORWAY'   :  'MOTORWAY',
	'MNT'        :  'MOUNT',
	'MOUNT'      :  'MOUNT',
	'MT'         :  'MOUNT',
	'MNTAIN'     :  'MOUNTAIN',
	'MNTN'       :  'MOUNTAIN',
	'MOUNTAIN'   :  'MOUNTAIN',
	'MOUNTIN'    :  'MOUNTAIN',
	'MTIN'       :  'MOUNTAIN',
	'MTN'        :  'MOUNTAIN',
	'MNTNS'      :  'MOUNTAINS',
	'MOUNTAINS'  :  'MOUNTAINS',
	'NCK'        :  'NECK',
	'NECK'       :  'NECK',
	'ORCH'       :  'ORCHARD',
	'ORCHARD'    :  'ORCHARD',
	'ORCHRD'     :  'ORCHARD',
	'OVAL'       :  'OVAL',
	'OVL'        :  'OVAL',
	'OVERPASS'   :  'OVERPASS',
	'PARK'       :  'PARK',
	'PK'         :  'PARK',
	'PRK'        :  'PARK',
	'PARKS'      :  'PARKS',
	'PARKWAY'    :  'PARKWAY',
	'PARKWY'     :  'PARKWAY',
	'PKWAY'      :  'PARKWAY',
	'PKWY'       :  'PARKWAY',
	'PKY'        :  'PARKWAY',
	'PARKWAYS'   :  'PARKWAYS',
	'PKWYS'      :  'PARKWAYS',
	'PASS'       :  'PASS',
	'PASSAGE'    :  'PASSAGE',
	'PATH'       :  'PATH',
	'PATHS'      :  'PATH',
	'PIKE'       :  'PIKE',
	'PIKES'      :  'PIKE',
	'PINE'       :  'PINE',
	'PINES'      :  'PINES',
	'PNES'       :  'PINES',
	'PL'         :  'PLACE',
	'PLACE'      :  'PLACE',
	'PLAIN'      :  'PLAIN',
	'PLN'        :  'PLAIN',
	'PLAINES'    :  'PLAINS',
	'PLAINS'     :  'PLAINS',
	'PLNS'       :  'PLAINS',
	'PLAZA'      :  'PLAZA',
	'PLZ'        :  'PLAZA',
	'PLZA'       :  'PLAZA',
	'POINT'      :  'POINT',
	'PT'         :  'POINT',
	'POINTS'     :  'POINTS',
	'PTS'        :  'POINTS',
	'PORT'       :  'PORT',
	'PRT'        :  'PORT',
	'PORTS'      :  'PORTS',
	'PRTS'       :  'PORTS',
	'PR'         :  'PRAIRIE',
	'PRAIRIE'    :  'PRAIRIE',
	'PRARIE'     :  'PRAIRIE',
	'PRR'        :  'PRAIRIE',
	'RAD'        :  'RADIAL',
	'RADIAL'     :  'RADIAL',
	'RADIEL'     :  'RADIAL',
	'RADL'       :  'RADIAL',
	'RAMP'       :  'RAMP',
	'RANCH'      :  'RANCH',
	'RANCHES'    :  'RANCH',
	'RNCH'       :  'RANCH',
	'RNCHS'      :  'RANCH',
	'RAPID'      :  'RAPID',
	'RPD'        :  'RAPID',
	'RAPIDS'     :  'RAPIDS',
	'RPDS'       :  'RAPIDS',
	'REST'       :  'REST',
	'RST'        :  'REST',
	'RDG'        :  'RIDGE',
	'RDGE'       :  'RIDGE',
	'RIDGE'      :  'RIDGE',
	'RDGS'       :  'RIDGES',
	'RIDGES'     :  'RIDGES',
	'RIV'        :  'RIVER',
	'RIVER'      :  'RIVER',
	'RIVR'       :  'RIVER',
	'RVR'        :  'RIVER',
	'RD'         :  'ROAD',
	'ROAD'       :  'ROAD',
	'RDS'        :  'ROADS',
	'ROADS'      :  'ROADS',
	'ROUTE'      :  'ROUTE',
	'ROW'        :  'ROW',
	'RUE'        :  'RUE',
	'RUN'        :  'RUN',
	'SHL'        :  'SHOAL',
	'SHOAL'      :  'SHOAL',
	'SHLS'       :  'SHOALS',
	'SHOALS'     :  'SHOALS',
	'SHOAR'      :  'SHORE',
	'SHORE'      :  'SHORE',
	'SHR'        :  'SHORE',
	'SHOARS'     :  'SHORES',
	'SHORES'     :  'SHORES',
	'SHRS'       :  'SHORES',
	'SKYWAY'     :  'SKYWAY',
	'SPG'        :  'SPRING',
	'SPNG'       :  'SPRING',
	'SPRING'     :  'SPRING',
	'SPRNG'      :  'SPRING',
	'SPGS'       :  'SPRINGS',
	'SPNGS'      :  'SPRINGS',
	'SPRINGS'    :  'SPRINGS',
	'SPRNGS'     :  'SPRINGS',
	'SPUR'       :  'SPUR',
	'SPURS'      :  'SPURS',
	'SQ'         :  'SQUARE',
	'SQR'        :  'SQUARE',
	'SQRE'       :  'SQUARE',
	'SQU'        :  'SQUARE',
	'SQUARE'     :  'SQUARE',
	'SQRS'       :  'SQUARES',
	'SQUARES'    :  'SQUARES',
	'STA'        :  'STATION',
	'STATION'    :  'STATION',
	'STATN'      :  'STATION',
	'STN'        :  'STATION',
	'STRA'       :  'STRAVENUE',
	'STRAV'      :  'STRAVENUE',
	'STRAVE'     :  'STRAVENUE',
	'STRAVEN'    :  'STRAVENUE',
	'STRAVENUE'  :  'STRAVENUE',
	'STRAVN'     :  'STRAVENUE',
	'STRVN'      :  'STRAVENUE',
	'STRVNUE'    :  'STRAVENUE',
	'STREAM'     :  'STREAM',
	'STREME'     :  'STREAM',
	'STRM'       :  'STREAM',
	'ST'         :  'STREET',
	'STR'        :  'STREET',
	'STREET'     :  'STREET',
	'STRT'       :  'STREET',
	'STREETS'    :  'STREETS',
	'SMT'        :  'SUMMIT',
	'SUMIT'      :  'SUMMIT',
	'SUMITT'     :  'SUMMIT',
	'SUMMIT'     :  'SUMMIT',
	'TER'        :  'TERRACE',
	'TERR'       :  'TERRACE',
	'TERRACE'    :  'TERRACE',
	'THROUGHWAY' :  'THROUGHWAY',
	'TRACE'      :  'TRACE',
	'TRACES'     :  'TRACE',
	'TRCE'       :  'TRACE',
	'TRACK'      :  'TRACK',
	'TRACKS'     :  'TRACK',
	'TRAK'       :  'TRACK',
	'TRK'        :  'TRACK',
	'TRKS'       :  'TRACK',
	'TRAFFICWAY' :  'TRAFFICWAY',
	'TRFY'       :  'TRAFFICWAY',
	'TR'         :  'TRAIL',
	'TRAIL'      :  'TRAIL',
	'TRAILS'     :  'TRAIL',
	'TRL'        :  'TRAIL',
	'TRLS'       :  'TRAIL',
	'TUNEL'      :  'TUNNEL',
	'TUNL'       :  'TUNNEL',
	'TUNLS'      :  'TUNNEL',
	'TUNNEL'     :  'TUNNEL',
	'TUNNELS'    :  'TUNNEL',
	'TUNNL'      :  'TUNNEL',
	'TPK'        :  'TURNPIKE',
	'TPKE'       :  'TURNPIKE',
	'TRNPK'      :  'TURNPIKE',
	'TRPK'       :  'TURNPIKE',
	'TURNPIKE'   :  'TURNPIKE',
	'TURNPK'     :  'TURNPIKE',
	'UNDERPASS'  :  'UNDERPASS',
	'UN'         :  'UNION',
	'UNION'      :  'UNION',
	'UNIONS'     :  'UNIONS',
	'VALLEY'     :  'VALLEY',
	'VALLY'      :  'VALLEY',
	'VLLY'       :  'VALLEY',
	'VLY'        :  'VALLEY',
	'VALLEYS'    :  'VALLEYS',
	'VLYS'       :  'VALLEYS',
	'VDCT'       :  'VIADUCT',
	'VIA'        :  'VIADUCT',
	'VIADCT'     :  'VIADUCT',
	'VIADUCT'    :  'VIADUCT',
	'VIEW'       :  'VIEW',
	'VW'         :  'VIEW',
	'VIEWS'      :  'VIEWS',
	'VWS'        :  'VIEWS',
	'VILL'       :  'VILLAGE',
	'VILLAG'     :  'VILLAGE',
	'VILLAGE'    :  'VILLAGE',
	'VILLG'      :  'VILLAGE',
	'VILLIAGE'   :  'VILLAGE',
	'VLG'        :  'VILLAGE',
	'VILLAGES'   :  'VILLAGES',
	'VLGS'       :  'VILLAGES',
	'VILLE'      :  'VILLE',
	'VL'         :  'VILLE',
	'VIS'        :  'VISTA',
	'VIST'       :  'VISTA',
	'VISTA'      :  'VISTA',
	'VST'        :  'VISTA',
	'VSTA'       :  'VISTA',
	'WALK'       :  'WALK',
	'WALKS'      :  'WALKS',
	'WALL'       :  'WALL',
	'WAY'        :  'WAY',
	'WY'         :  'WAY',
	'WAYS'       :  'WAYS',
	'WELL'       :  'WELL',
	'WELLS'      :  'WELLS',
	'WLS'        :  'WELLS',
	}

usps_street_suffix_abbr = {
	'ALLEY'      :  'ALY',
	'ANNEX'      :  'ANX',
	'ARCADE'     :  'ARC',
	'AVENUE'     :  'AVE',
	'BAYOO'      :  'BYU',
	'BEACH'      :  'BCH',
	'BEND'       :  'BND',
	'BLUFF'      :  'BLF',
	'BLUFFS'     :  'BLFS',
	'BOTTOM'     :  'BTM',
	'BOULEVARD'  :  'BLVD',
	'BRANCH'     :  'BR',
	'BRIDGE'     :  'BRG',
	'BROOK'      :  'BRK',
	'BROOKS'     :  'BRKS',
	'BURG'       :  'BG',
	'BURGS'      :  'BGS',
	'BYPASS'     :  'BYP',
	'CAMP'       :  'CP',
	'CANYON'     :  'CYN',
	'CAPE'       :  'CPE',
	'CAUSEWAY'   :  'CSWY',
	'CENTER'     :  'CTR',
	'CENTERS'    :  'CTRS',
	'CIRCLE'     :  'CIR',
	'CIRCLES'    :  'CIRS',
	'CLIFF'      :  'CLF',
	'CLIFFS'     :  'CLFS',
	'CLUB'       :  'CLB',
	'COMMON'     :  'CMN',
	'CORNER'     :  'COR',
	'CORNERS'    :  'CORS',
	'COURSE'     :  'CRSE',
	'COURT'      :  'CT',
	'COURTS'     :  'CTS',
	'COVE'       :  'CV',
	'COVES'      :  'CVS',
	'CREEK'      :  'CRK',
	'CRESCENT'   :  'CRES',
	'CREST'      :  'CRST',
	'CROSSING'   :  'XING',
	'CROSSROAD'  :  'XRD',
	'CURVE'      :  'CURV',
	'DALE'       :  'DL',
	'DAM'        :  'DM',
	'DIVIDE'     :  'DV',
	'DRIVE'      :  'DR',
	'DRIVES'     :  'DRS',
	'ESTATE'     :  'EST',
	'ESTATES'    :  'ESTS',
	'EXPRESSWAY' :  'EXPY',
	'EXTENSION'  :  'EXT',
	'EXTENSIONS' :  'EXTS',
	'FALL'       :  'FALL',
	'FALLS'      :  'FLS',
	'FERRY'      :  'FRY',
	'FIELD'      :  'FLD',
	'FIELDS'     :  'FLDS',
	'FLAT'       :  'FLT',
	'FLATS'      :  'FLTS',
	'FORD'       :  'FRD',
	'FORDS'      :  'FRDS',
	'FOREST'     :  'FRST',
	'FORGE'      :  'FRG',
	'FORGES'     :  'FRGS',
	'FORK'       :  'FRK',
	'FORKS'      :  'FRKS',
	'FORT'       :  'FT',
	'FREEWAY'    :  'FWY',
	'GARDEN'     :  'GDN',
	'GARDENS'    :  'GDNS',
	'GATEWAY'    :  'GTWY',
	'GLEN'       :  'GLN',
	'GLENS'      :  'GLNS',
	'GREEN'      :  'GRN',
	'GREENS'     :  'GRNS',
	'GROVE'      :  'GRV',
	'GROVES'     :  'GRVS',
	'HARBOR'     :  'HBR',
	'HARBORS'    :  'HBRS',
	'HAVEN'      :  'HVN',
	'HEIGHTS'    :  'HTS',
	'HIGHWAY'    :  'HWY',
	'HILL'       :  'HL',
	'HILLS'      :  'HLS',
	'HOLLOW'     :  'HOLW',
	'INLET'      :  'INLT',
	'ISLAND'     :  'IS',
	'ISLANDS'    :  'ISS',
	'ISLE'       :  'ISLE',
	'JUNCTION'   :  'JCT',
	'JUNCTIONS'  :  'JCTS',
	'KEY'        :  'KY',
	'KEYS'       :  'KYS',
	'KNOLL'      :  'KNL',
	'KNOLLS'     :  'KNLS',
	'LAKE'       :  'LK',
	'LAKES'      :  'LKS',
	'LAND'       :  'LAND',
	'LANDING'    :  'LNDG',
	'LANE'       :  'LN',
	'LIGHT'      :  'LGT',
	'LIGHTS'     :  'LGTS',
	'LOAF'       :  'LF',
	'LOCK'       :  'LCK',
	'LOCKS'      :  'LCKS',
	'LODGE'      :  'LDG',
	'LOOP'       :  'LOOP',
	'MALL'       :  'MALL',
	'MANOR'      :  'MNR',
	'MANORS'     :  'MNRS',
	'MEADOW'     :  'MDW',
	'MEADOWS'    :  'MDWS',
	'MEWS'       :  'MEWS',
	'MILL'       :  'ML',
	'MILLS'      :  'MLS',
	'MISSION'    :  'MSN',
	'MOTORWAY'   :  'MTWY',
	'MOUNT'      :  'MT',
	'MOUNTAIN'   :  'MTN',
	'MOUNTAINS'  :  'MTNS',
	'NECK'       :  'NCK',
	'ORCHARD'    :  'ORCH',
	'OVAL'       :  'OVAL',
	'OVERPASS'   :  'OPAS',
	'PARK'       :  'PARK',
	'PARKWAY'    :  'PKWY',
	'PASS'       :  'PASS',
	'PASSAGE'    :  'PSGE',
	'PATH'       :  'PATH',
	'PIKE'       :  'PIKE',
	'PINE'       :  'PNE',
	'PINES'      :  'PNES',
	'PLACE'      :  'PL',
	'PLAIN'      :  'PLN',
	'PLAINS'     :  'PLNS',
	'PLAZA'      :  'PLZ',
	'POINT'      :  'PT',
	'POINTS'     :  'PTS',
	'PORT'       :  'PRT',
	'PORTS'      :  'PRTS',
	'PRAIRIE'    :  'PR',
	'RADIAL'     :  'RADL',
	'RAMP'       :  'RAMP',
	'RANCH'      :  'RNCH',
	'RAPID'      :  'RPD',
	'RAPIDS'     :  'RPDS',
	'REST'       :  'RST',
	'RIDGE'      :  'RDG',
	'RIDGES'     :  'RDGS',
	'RIVER'      :  'RIV',
	'ROAD'       :  'RD',
	'ROADS'      :  'RDS',
	'ROUTE'      :  'RTE',
	'ROW'        :  'ROW',
	'RUE'        :  'RUE',
	'RUN'        :  'RUN',
	'SHOAL'      :  'SHL',
	'SHOALS'     :  'SHLS',
	'SHORE'      :  'SHR',
	'SHORES'     :  'SHRS',
	'SKYWAY'     :  'SKWY',
	'SPRING'     :  'SPG',
	'SPRINGS'    :  'SPGS',
	'SPUR'       :  'SPUR',
	'SQUARE'     :  'SQ',
	'SQUARES'    :  'SQS',
	'STATION'    :  'STA',
	'STRAVENUE'  :  'STRA',
	'STREAM'     :  'STRM',
	'STREET'     :  'ST',
	'STREETS'    :  'STS',
	'SUMMIT'     :  'SMT',
	'TERRACE'    :  'TER',
	'THROUGHWAY' :  'TRWY',
	'TRACE'      :  'TRCE',
	'TRACK'      :  'TRAK',
	'TRAFFICWAY' :  'TRFY',
	'TRAIL'      :  'TRL',
	'TUNNEL'     :  'TUNL',
	'TURNPIKE'   :  'TPKE',
	'UNDERPASS'  :  'UPAS',
	'UNION'      :  'UN',
	'UNIONS'     :  'UNS',
	'VALLEY'     :  'VLY',
	'VALLEYS'    :  'VLYS',
	'VIADUCT'    :  'VIA',
	'VIEW'       :  'VW',
	'VIEWS'      :  'VWS',
	'VILLAGE'    :  'VLG',
	'VILLAGES'   :  'VLGS',
	'VILLE'      :  'VL',
	'VISTA'      :  'VIS',
	'WALK'       :  'WALK',
	'WALL'       :  'WALL',
	'WAY'        :  'WAY',
	'WAYS'       :  'WAYS',
	'WELL'       :  'WL',
	'WELLS'      :  'WLS',
	}

usps_secondary_designator = {
    'APARTMENT'  :  'APT',
    'APT'        :  'APT',
    'BASEMENT'   :  'BSMT',
    'BSMT'       :  'BSMT',
    'BUILDING'   :  'BLDG',
    'BLDG'       :  'BLDG',
    'DEPARTMENT' :  'DEPT',
    'DEPT'       :  'DEPT',
    'FLOOR'      :  'FLOOR',
    'FLR'        :  'FLOOR',
    'FRONT'      :  'FRONT',
    'FRNT'       :  'FRONT',
    'HANGER'     :  'HNGR',
    'HNGR'       :  'HNGR',
    'KEY'        :  'KEY',
    'KEY'        :  'KEY',
    'LOBBY'      :  'LOBBY',
    'LBBY'       :  'LOBBY',
    'LOT'        :  'LOT',
    'LOWER'      :  'LOWER',
    'LOWR'       :  'LOWER',
    'OFFICE'     :  'OFC',
    'OFC'        :  'OFC',
    'PENTHOUSE'  :  'PH',
    'PH'         :  'PH',
    'PIER'       :  'PIER',
    'REAR'       :  'REAR',
    'ROOM'       :  'RM',
    'RM'         :  'RM',
    'SIDE'       :  'SIDE',
    'SLIP'       :  'SLIP',
    'SLIP'       :  'SLIP',
    'SPACE'      :  'SPC',
    'SPC'        :  'SPC',
    'STOP'       :  'STOP',
    'SUITE'      :  'STE',
    'STE'        :  'STE',
    'TRAILER'    :  'TRLR',
    'TRLR'       :  'TRLR',
    'UNIT'       :  'UNIT',
    'UPPER'      :  'UPPER',
    'UPPR'       :  'UPPER',
    '#'          :  '#',
    }

pobox = translator(keep='BOPX')

abbr_ordinal = dict(
    NORTHEAST='NE', NORTH='N',
    NORTHWEST='NW', SOUTH='S',
    SOUTHEAST='SE', EAST='E',
    SOUTHWEST='SW', WEST='W',
    )
full_ordinal = dict([(v, k) for k, v in abbr_ordinal.items()])

all_ordinals = set(full_ordinal.keys() + abbr_ordinal.keys())


class AddressSegment(AutoEnum):
    misc = "not currently tracked"
    ordinal = "N S E W etc"
    secondary = "apt bldg floor etc"
    street = "st ave blvd etc"


def ordinals(text):
    # we want, at most, one ordinal abbreviation in a row (no sequential)
    # if two ordinal type words appear together which one gets abbreviated depends
    # on where they are: if at the end of the address (or just before a Secondary
    # Unit Designator (apt, bldng, flr, etc), then the second one as shortened,
    # otherwise the first one is;
    # if there is only one ordinal, but less than four components (e.g.
    # 823 West St), then we do not shorten it.
    # if two ordinals are separated by more than one non-secondary piece, shorten
    # both

    pieces = text
    if isinstance(pieces, String):
        pieces = pieces.split()
    AS = AddressSegment
    tokens = []
    for i, p in enumerate(pieces):
        if p in all_ordinals:
            tokens.append(AS.ordinal)
        elif p in usps_secondary_designator:
            tokens.append(AS.secondary)
        elif p in usps_street_suffix_common:
            tokens.append(AS.street)
        elif i >= 2 and p.startswith('#'):
            tokens.append(AS.secondary)
        else:
            tokens.append(AS.misc)
    # there should be, at most, one AS.street token, and it should be either
    # the last, or next to last, token in the primary portion (before any
    # AS.secondary token); if we find a AS.street token anywhere else, change
    # it to a AS.misc token
    for i, t in enumerate(tokens):
        if t is AS.secondary:
            secondary = i
            break
    else:
        secondary = -1
    final = len(tokens) - 1
    if secondary != -1:
        final = secondary - 1
    for i, token in enumerate(tokens):
        if token is AS.secondary:
            break
        if token is AS.street:
            if i == final:
                continue
            elif i == final -1 and tokens[final] is AS.ordinal:
                continue
            tokens[i] = AS.misc
    primary = []
    secondary = []
    if AS.secondary in tokens:
        index = tokens.index(AS.secondary)
        for p in pieces[index:]:
            secondary.append(
                    usps_secondary_designator.get(p, 
                        full_ordinal.get(p, p)))
        tokens = tokens[:index]
        pieces = pieces[:index]
    counted_ordinals = tokens.count(AS.ordinal)
    if len(tokens) <= 3:
        for p in pieces:
            if len(p) != 1:
                p = full_ordinal.get(p, p)
            primary.append(p)
    elif counted_ordinals == 1:
        for i, p in enumerate(pieces):
            if tokens[i+1:i+2] != [AS.street]:
                p = abbr_ordinal.get(p, p)
            primary.append(p)
    elif counted_ordinals:
        ending_ordinal = 0
        if tokens[-1] is AS.ordinal:
            ending_ordinal = len(tokens) - 1
        prev_ordinal = False
        for i, (piece, token) in enumerate(zip(pieces, tokens)):
            if token is AS.ordinal:
                if prev_ordinal is True:
                    if len(piece) != 1:
                        piece = full_ordinal.get(piece, piece)
                    primary.append(piece)
                    prev_ordinal = False
                else:
                    if i + 1 == ending_ordinal:
                        if len(piece) != 1:
                            piece = full_ordinal.get(piece, piece)
                        primary.append(piece)
                    else:
                        if tokens[i+1:i+2] != [AS.street]:
                            piece = abbr_ordinal.get(piece, piece)
                        primary.append(piece)
                        prev_ordinal = True
            else:
                prev_ordinal = False
                primary.append(piece)
    else:
        primary = pieces
    pieces, primary = primary, []
    for piece, token in zip(pieces, tokens):
        if token is AS.street:
            piece = usps_street_suffix_abbr[piece]
        primary.append(piece)
    return primary + secondary


def normalize_address(line):
    if not line.strip():
        return line
    orig_line = line
    line = ' '.join(line.replace(',',' ').replace('.',' ').replace('-',' ').upper().split())
    if pobox(line) == 'POBOX':
        index = line.index('X')
        trailer = line[index+1:]
        if trailer and not trailer.isalpha():
            line = ' '.join(['PO BOX', line[index+1:].strip()])
            return line
    pieces = line.split()
    if not has_digits(pieces[0]) and pieces[0].upper() not in spelled_out_numbers:
        return orig_line
    line = []
    for p in pieces:
        line.append(usps_street_suffix_common.get(p, p))
    line = ordinals(line)
    return ' '.join(line)


class PostalCode(object):
    """
    primarily for US and Canadian postal codes (ignores US +4)
    """

    def __init__(yo, postal, country=None):
        alpha2num = {
                'I' : '1',
                'O' : '0',
                'S' : '5',
                }
        num2alpha = {
                '1'   : 'I',
                '0'   : 'O',
                '5'   : 'S',
                }
        postal = postal.strip('-,')
        if len(postal.replace('-', '')) in (5, 9):
            yo.code = postal[:5]
        elif postal[:5].isdigit():
            yo.code = postal[:5]
        elif (has_alpha(postal) and len(postal.replace(' ', '')) == 6
        and   (not country or country == 'CANADA')):
            # alpha-num-alpha num-alpha-num
            postal = list(postal.replace(' ', '').upper())
            for i in (0, 2, 4):
                postal[i] = num2alpha.get(postal[i], postal[i])
            for i in (1, 3, 5):
                postal[i] = alpha2num.get(postal[i], postal[i])
            yo.code = "%s %s" % (''.join(postal[:3]), ''.join(postal[3:]))
        else:
            yo.code = postal

    def __eq__(yo, other):
        if not isinstance(other, (str, unicode, yo.__class__)):
            return NotImplemented
        if isinstance(other, yo.__class__):
            other = other.code
        return yo.code == other

    def __ne__(yo, other):
        return not yo.__eq__(other)

    def __repr__(yo):
        return repr(yo.code)

    def __str__(yo):
        return yo.code



