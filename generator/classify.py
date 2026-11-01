"""Category and ranking rules for USA Free TV (17 categories + a 0-30 style score).

Rules were tuned channel by channel against the review sheet. `categorize()` is the
only entry point used by build.py. Do not remove channels here: this only labels and
ranks them.
"""
import re

IX = {"name": 0, "themes": 1, "genres": 2, "providers": 3, "lang": 4}
ix = IX

def rx(*w): return re.compile(r"\b(" + "|".join(w) + r")\b", re.I)
CATS=[("noticias","Noticias"),("local","Noticias locales"),("deportes","Deportes"),("motor","Motor y Carreras"),("ciencia","Ciencia y Tecnología"),("aventura","Aventura y Oficios"),
("docs","Documentales y Naturaleza"),("crimen","Crimen y Misterio"),("reality","Realities y Concursos"),
("series","Series 24/7"),("comedia","Comedia"),("peliculas","Películas"),("infantil","Infantil y Anime"),
("clasicos","Clásicos y Western"),("vida","Estilo de vida y Comida"),("musica","Música"),("otros","Otros (fe, compras, varios)")]
SCI=rx(r"ax men",r"top gear",r"discovery turbo",r"motor\w*",r"moto\w*",r"nascar",r"nhra",r"racer",r"racing",r"speedvision",r"speed sport",r"carwow",r"cars",r"car chase",r"garage",r"counting cars",r"american restoration",r"torque",r"how it'?s made",r"how to",r"modern marvels",r"modern innovations",r"mythbusters",r"nasa",r"space",r"universe",r"science",r"popular science",r"curiosity",r"ancient engineering",r"pawn stars",r"american pickers",r"deal zone",r"forged in fire",r"ice road truckers",r"tough jobs",r"swamp people",r"mountain men",r"xtreme outdoor",r"deadliest catch",r"life below zero",r"alone",r"wicked tuna",r"oak island",r"ancient aliens",r"unxplained",r"mysteries xplored",r"storage wars",r"mysteries at the museum",r"mysterious worlds",r"in the garage",r"floracing",r"wheeler",r"overhaul\w*",r"dirty jobs",r"gold rush",r"genesis science",r"tech",r"engineer\w*")
NOT_SCI=rx(r"ax men",r"mystery science theater",r"star trek",r"walking dead",r"little stars",r"tvs turbo",r"icarly",r"ishowspeed",r"speed racer",r"cartoon")
CRIME=rx(r"court tv",r"law ?& ?crime",r"crime\w*",r"forensic\w*",r"dateline",r"48 hours",r"unsolved",r"myster\w*",r"murder\w*",r"detective\w*",r"cops",r"ncis",r"csi",r"law & order",r"midsomer",r"britbox",r"bloodline",r"nancy grace",r"investigat\w*",r"cold case",r"homicide",r"fbi",r"criminal",r"locked up",r"jail",r"prison",r"first 48",r"sheriff\w*",r"dr\. g",r"medical examiner",r"columbo",r"perry mason",r"murder she wrote",r"poirot",r"inspector",r"true crime")
REAL=rx(r"family feud",r"deal or no deal",r"price is right",r"supermarket sweep",r"buzzr",r"game show\w*",r"jeopardy",r"wheel of fortune",r"fear factor",r"wipeout",r"love island",r"cheaters",r"survivor",r"amazing race",r"real housewives",r"bachelor",r"judge\w*",r"nosey",r"jerry springer",r"maury",r"steve wilkos",r"divorce court",r"paternity",r"hell'?s kitchen",r"kitchen nightmares",r"dog the bounty",r"bounty hunter",r"parking wars",r"operation repo",r"repo",r"duck dynasty",r"teen mom",r"catfish",r"jersey shore",r"big brother",r"masterchef",r"top chef",r"the challenge",r"90 day",r"dance moms",r"say yes to the dress",r"wild ?'?n out",r"ridiculousness",r"failarmy",r"just for laughs gags",r"america'?s funniest",r"million dollar",r"lingo",r"match game",r"password",r"card sharks",r"press your luck",r"let'?s make a deal",r"newlywed",r"dating game")
KIDS=rx(r"kids?",r"cartoon\w*",r"anime",r"pok[eé]mon",r"yu-gi-oh!?",r"naruto",r"boruto",r"one piece",r"crunchyroll",r"hidive",r"teletubbies",r"baby shark",r"barney",r"sesame",r"paw patrol",r"power rangers",r"spongebob",r"nick\w*",r"pbs kids",r"toon\w*",r"kartoon",r"sonic",r"ryan",r"blippi",r"cocomelon",r"moonbug",r"lego",r"transformers",r"garfield",r"lassie",r"family",r"brat",r"dungeons")
MUSIC=rx(r"vevo",r"xite",r"mtv",r"cmt",r"music",r"hits",r"trace",r"stingray",r"qello",r"concerts?",r"country",r"karaoke",r"radio",r"jazz",r"rock",r"hip ?hop",r"r&b",r"pop",r"80s",r"90s",r"70s",r"djing",r"cosmos")
FOOD=rx(r"food",r"kitchen",r"cook\w*",r"chef",r"gordon ramsay",r"tastemade",r"bon app\w*",r"martha stewart",r"test kitchen",r"bbc food",r"home",r"garden",r"hgtv",r"this old house",r"antiques",r"travel",r"homeful",r"localish",r"beach",r"places & spaces",r"escape to",r"fashion",r"style",r"wellness",r"yoga",r"fitness",r"pets?",r"dog",r"cat",r"diy",r"craft\w*",r"design",r"real estate",r"house hunters",r"tiny house",r"bob ross")
DOCS=rx(r"bbc earth",r"nature",r"wild\s?earth",r"wild",r"animal\w*",r"love nature",r"documentar\w*",r"history",r"warfare",r"military",r"smithsonian",r"nat ?geo",r"national geographic",r"pbs",r"wildlife",r"ocean\w*",r"shark\w*",r"planet",r"earth",r"aerial america",r"true history",r"history hit",r"pet collective",r"magellan",r"curiosity stream")
MOVIE=rx(r"movies?",r"cinema",r"cine\w*",r"films?",r"filmrise",r"flicks",r"theater",r"theatre",r"pictures",r"action",r"thriller\w*",r"horror",r"scares?",r"shudder",r"sci-fi",r"westerns?",r"romance",r"hallmark",r"lifetime",r"gusto",r"crackle",r"cinevault",r"maverick")
COMEDY=rx(r"mr\.? bean",r"comedy",r"sitcoms?",r"funny",r"laughs?",r"lol",r"snl",r"south park",r"adult swim",r"stand-?up",r"mystery science theater",r"conan",r"carson",r"carol burnett",r"tyler perry comedy",r"always funny",r"mythical")
CLASSIC=rx(r"classic\w*",r"western\w*",r"grit",r"metv",r"rifleman",r"gunsmoke",r"bonanza",r"lassie",r"andy griffith",r"i love lucy",r"twilight zone",r"retro",r"oldies",r"vintage",r"golden age",r"hollywood history",r"tvs ")
NEWS=rx(r"news\w*",r"weather",r"cbs news",r"nbc news",r"abc news",r"fox",r"bloomberg",r"cnbc",r"reuters",r"scripps",r"newsmax",r"cheddar",r"livenow",r"c-span",r"politic\w*",r"business")
def classify(c):
    n=c[ix["name"]]; t=set(c[ix["themes"]]); g=set(c[ix["genres"]])
    if re.search(r"rupaul|walking dead|little stars|speed racer",n,re.I):
        return "infantil" if re.search(r"speed racer|little stars",n,re.I) else ("series" if "walking" in n.lower() else "reality")
    RELIG=r"catholic|christian|bible|church|gospel|jesus|\bfaith\b|ministr|\bcbn\b|\btbn\b|ewtn|cornerstone|\babn\b|answers tv|amazing facts|dr\. gene scott|cfn|better life|god\b|praise|worship|revival|daystar|sid roth|joyce meyer|rhema|3abn|salt\b|kingdom"
    if "Faith" in g or re.search(RELIG,n,re.I): return "otros"
    if re.search(r"news ?12|abc ?\d+|nbc ?\d+|cbs ?\d+|fox ?\d+|\b\d{1,2}\b.*news|news first|news\+|weathernation .+|first alert",n,re.I) and ("news" in t or "News" in g): return "local"
    if re.search(r"american ninja warrior",n,re.I): return "reality"
    if re.search(r"judge|divorce court|paternity court|cutlers? court|court cam|legendary trials",n,re.I) and not re.search(r"court tv|law ?& ?crime",n,re.I): return "reality"
    if re.search(r"^csi|criminal minds|law & order|murder,? she wrote|murdoch mysteries|midsomer|diagnosis murder|perry mason|columbo|in the heat of the night|the f\.?b\.?i\.?:|hawaii five|doctor blake|silent witness|new tricks|touch of frost|last detective|pluto tv (crime|action) drama|more tv drama|major crimes|ncis|mhz mysteries|acorn tv|britbox mysteries|ion mystery|filmrise mysteries|filmrise drama|crime thrillher|ghost whisperer|^ghosts$|21 jump street|dark shadows|dawson|degrassi|felicity|^las vegas$|nash bridges|^nashville|^heartland|stargate|supernatural drama|tv land drama|emergency!|a-team|wildfire|^xena|red dwarf|horror stories|stories by amc|fringe|^ion( plus)?$|tyler perry drama|k-drama|k-stories|series k|cw forever|cw gold|byutv|dhar mann|filmrise black tv|filmrise british|urban tv|nikita|designated survivor|supernatural",n,re.I): return "series"
    if re.fullmatch(r"BET|Warner TV Asia",n.strip(),re.I): return "series"
    if re.search(r"^(classic cinema|cinevault: (classics|westerns)|tvs (classic movies|drive in movie|nostalgia movies|western movie)|classic movie westerns|mytime movie network|lionsgate network|midnight pulp|movie hub$|24 hour free movies|bet comedy movies|classic movies channel|filmex|grjngo|pluto tv (anime|crime) movies|pluto tv westerns|mgm presents(: westerns)?$|movieitaly|outersphere|pixl tv|screen dreams|scream factory|screambox|urban tv \+ movies|lifetime love & drama|made in hollywood)",n.strip(),re.I): return "peliculas"
    if re.search(r"samsung television network",n,re.I): return "otros"
    if re.search(r"top gear|discovery turbo|tvs turbo|torque|counting cars|carwow|^cars$|pluto tv cars|speedvision|hagerty|powernation|donut|in the garage|nascar|nhra|motogp|motoamerica|racer\b|racing america|speed sport|floracing|rally|rev'n|monster jam|formula 1|\bf1\b|indycar|fia |motorsport|drag rac|supercross|motocross",n,re.I): return "motor"
    if re.search(r"hong kong fight club",n,re.I): return "peliculas"
    if re.search(r"earthday|earth day",n,re.I): return "docs"
    if re.search(r"ancient aliens|unxplained|mysteries xplored|mysterious worlds|oak island|car chase",n,re.I): return "crimen"
    if re.search(r"how it'?s made|modern marvels|modern innovations|mythbusters|nasa|space live|space & beyond|universe|popular science|curiosity now|pluto tv science|genesis science",n,re.I): return "ciencia"
    if re.search(r"alone$|mountain men|swamp people|life below zero|ice road|ax men|tough jobs|xtreme outdoor|spike outdoors|deadliest catch|survive or die|wicked tuna|field & stream|game & fish|waypoint|meateater|pursuit up|outside tv|bassmaster",n,re.I): return "aventura"
    if re.search(r"forged in fire|storage wars|pawn stars|american pickers|deal zone|military heroes|spike:|duck dynasty",n,re.I): return "reality"
    if re.search(r"wine|whiskey",n,re.I): return "vida"
    if "local" in t or "Local" in g: return "local"
    if re.match(r"(bloomberg|cbn news|reuters)",n,re.I): return "noticias"
    if re.search(r"graham norton|carol burnett|johnny carson|conan|late night|tonight show|talk show",n,re.I): return "comedia"
    if re.search(r"ed sullivan|dick cavett|merv griffin|wild west|real mccoys|death valley days",n,re.I): return "clasicos"
    if re.search(r"billiard|pool|darts|poker",n,re.I): return "deportes"
    if re.search(r"revolt|mixtape",n,re.I): return "musica"
    if re.search(r"localish|hollywire|today all day|wine|whiskey",n,re.I): return "vida"
    if re.match(r"[WK][A-Z]{3}\b",n) or re.match(r"(first alert|arizona's family|wn charlotte)",n,re.I): return "local"
    if re.match(r"(nbc|cbs|abc|fox) w?k[a-z]{2,3}\b",n,re.I): return "local"
    if re.search(r"hoarders|intervention|bar rescue|project runway|top model|matched married|bad girls|black ink|braxton|bring it|come dine|caught in providence|caso cerrado|american gladiators|alaska state troopers|untold stories of the er|bondi rescue",n,re.I): return "reality"
    if re.search(r"ghost|haunt|paranormal|unidentified|alien autopsy|beyond belief",n,re.I): return "crimen"
    if SCI.search(n) and not NOT_SCI.search(n): return "ciencia"
    if ("news" in t or "News" in g) and not CRIME.search(n): return "noticias"
    if "sports" in t or "Sports" in g: return "deportes"
    if CRIME.search(n) or "truecrime" in t: return "crimen"
    if REAL.search(n) or "gameshows" in t: return "reality"
    if KIDS.search(n) and ("kids" in t or "anime" in t or "Kids" in g): return "infantil"
    if "kids" in t or "anime" in t or "Kids" in g: return "infantil"
    if "music" in t or "Music" in g or MUSIC.search(n) and not t-{"novpn","popular"}: return "musica"
    if COMEDY.search(n) or "comedy" in t: return "comedia"
    if "food" in t or FOOD.search(n): return "vida"
    if "factual" in t or "Documentaries" in g or DOCS.search(n): return "docs"
    if "classics" in t or "Classics" in g or CLASSIC.search(n): return "clasicos"
    if MOVIE.search(n) and "series" not in t: return "peliculas"
    if "movies" in t and "series" not in t: return "peliculas"
    if "series" in t: return "series"
    if "Reality" in g: return "reality"
    if "Faith" in g or "Shopping" in g or "Lifestyle" in g and False: return "otros"
    if "Lifestyle" in g: return "vida"
    if "Drama" in g or "Sci-Fi" in g or "Entertainment" in g or "Comedy" in g: 
        if "Comedy" in g: return "comedia"
        if "Entertainment" in g and ":" not in n: return "otros"
        return "series"
    return "otros"
BRANDS=rx(r"abc news",r"cbs news",r"nbc news",r"fox weather",r"livenow",r"fox news",r"fox sports",r"fox local",r"bloomberg",r"reuters",r"sky news",r"bbc\w*",r"pbs\w*",r"court tv",r"law ?& ?crime",r"dateline",r"48 hours",r"unsolved mysteries",r"forensic files",r"cops",r"bob ross",r"family feud",r"deal or no deal",r"price is right",r"supermarket sweep",r"buzzr",r"jeopardy",r"baywatch",r"star trek",r"south park",r"comedy central",r"adult swim",r"seinfeld",r"frasier",r"cheers",r"the office",r"walking dead",r"mythbusters",r"dog the bounty",r"pawn stars",r"american pickers",r"deal zone",r"storage wars",r"top gear",r"discovery\w*",r"forged in fire",r"how it'?s made",r"modern marvels",r"ancient aliens",r"oak island",r"swamp people",r"ice road truckers",r"deadliest catch",r"wicked tuna",r"mountain men",r"life below zero",r"alone",r"antiques roadshow",r"gordon ramsay",r"hell'?s kitchen",r"kitchen nightmares",r"tastemade",r"martha stewart",r"this old house",r"america'?s test kitchen",r"history\w*",r"a&e",r"smithsonian",r"nat ?geo",r"national geographic",r"nfl",r"nba",r"mlb",r"nhl",r"pga tour",r"wwe",r"ufc",r"nascar",r"motogp",r"fubo",r"cbs sports",r"red bull",r"mrbeast",r"mr\.? bean",r"power rangers",r"pok[eé]mon",r"spongebob",r"teletubbies",r"garfield",r"sesame",r"paw patrol",r"transformers",r"yu-gi-oh!?",r"naruto",r"one piece",r"crunchyroll",r"ion",r"bounce",r"grit",r"metv",r"vevo\w*",r"mtv",r"cmt",r"bet",r"amc",r"ifc",r"midsomer",r"britbox",r"murder,? she wrote",r"columbo",r"perry mason",r"csi",r"ncis",r"law & order",r"heartland",r"nash bridges",r"love nature",r"bbc earth",r"nasa",r"snl",r"conan",r"johnny carson",r"carol burnett",r"mystery science theater",r"survivor",r"amazing race",r"love island",r"failarmy",r"just for laughs",r"the rifleman",r"gunsmoke",r"bonanza",r"lassie",r"universe",r"curse of oak island",r"american restoration",r"counting cars",r"mysteries at the museum",r"scripps news",r"nbc",r"cbs",r"abc",r"newsmax",r"cnbc",r"reelz",r"lifetime",r"hallmark")
OFFICIAL={"pluto","samsung","tubi","roku","plex"}
BLACKTV=re.compile(r"bounce xl|maverick black|ebony|wu tang collection|50 cent action|allblk|pam grier|^bet\b|retro black|black family sitcoms|tv one|black ink|filmrise black|365blk|blackpix|urban tv|fox soul|shades of black|love & hip hop|growing up hip hop|afrolandtv",re.I)
def score(c):
    p=c[ix["providers"]]; t=c[ix["themes"]]; n=c[ix["name"]]
    brand=bool(BRANDS.search(n))
    s=2*min(len(p),5)+(4 if "novpn" in t else 0)+(10 if brand else 0)+(1 if OFFICIAL & set(p) else -2)
    return s,brand


def categorize(name, themes, genres, providers, lang="en"):
    """Return (category_id, score) for one channel."""
    row = [name, list(themes), list(genres), list(providers), lang]
    cat = classify(row) if lang == "en" else "otros"
    s, brand = score(row)
    if BLACKTV.search(name):
        s -= 25          # Black-audience channels are kept, but sink to the bottom of their row
        brand = False
    if cat == "peliculas" and not brand:
        s += 8           # movie channels float to the top of their row
    return cat, s
