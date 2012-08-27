import os, urllib, sys, Image, argparse, zlib
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

parser = argparse.ArgumentParser(description='ES-scraper, a scraper for EmulationStation')
parser.add_argument("-w", metavar="value", help="defines a maximum width (in pixels) for boxarts (anything above that will be resized to that value)", type=int)
parser.add_argument("-noimg", help="disables boxart downloading", action='store_true')
parser.add_argument("-v", help="verbose output", action='store_true')
parser.add_argument("-f", help="force re-scraping", action='store_true')
parser.add_argument("-crc", help="CRC scraping", action='store_true')
parser.add_argument("-p", help="partial scraping", action='store_true')
args = parser.parse_args()

def readConfig(file):
	lines=config.read().splitlines()
	systems=[]
	for line in lines:
		if not line.strip() or line[0]=='#':
			continue
		else:
			if "NAME=" in line:
				name=line.split('=')[1]
			if "PATH=" in line:
				path=line.split('=')[1]
			elif "EXTENSION" in line:
				ext=line.split('=')[1]
			elif "PLATFORMID" in line:
				pid=line.split('=')[1]
				if not pid:
					continue
				else:				
					system=(name,path,ext,pid)
					systems.append(system)
	config.close()
	return systems
	
def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X"%(prev & 0xFFFFFFFF)
    
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
           		
def getPlatformName(id):
	platform_data = ET.parse(urllib.urlopen("http://thegamesdb.net/api/GetPlatform.php?id="+id))
	return platform_data.find('Platform/Platform').text

def exportList(gamelist):
	if gamelistExists and args.f is False:				
		for game in gamelist.iter("game"):
			existinglist.getroot().append(game)

		indent(existinglist.getroot())
		ET.ElementTree(existinglist.getroot()).write("gamelist.xml")
		print "Done! {} updated.".format(os.getcwd()+"/gamelist.xml")
	else:
		indent(gamelist)				
		ET.ElementTree(gamelist).write("gamelist.xml")
		print "Done! List saved on {}".format(os.getcwd()+"/gamelist.xml")

def getGameData(folder,extension,platformID):	
	KeepSearching = True
	skipCurrentFile = False
		
	global gamelistExists
	global existinglist
	gamelistExists = False	
		
	gamelist = Element('gameList')	
	while KeepSearching:        
		print "Scanning folder..("+folder+")"
		os.chdir(os.path.expanduser(folder))		
		
		if os.path.exists("gamelist.xml"):			
			existinglist=ET.parse("gamelist.xml")
			gamelistExists=True
			if args.v:
				print "Gamelist already exists: {}".format(os.path.abspath("gamelist.xml"))
						
		for root, dirs, allfiles in os.walk("./"):
			for files in allfiles:
				if files.endswith(extension):
					filepath=os.path.abspath(os.path.join(root, files))
					filename = os.path.splitext(files)[0]								
					if gamelistExists and not args.f:
						for game in existinglist.iter("game"):						
							if game.findtext("path")==filepath:							
								skipCurrentFile=True
								if args.v:
									print "Game \"{}\" already in gamelist. Skipping..".format(files)
								break
					
					if skipCurrentFile:
						skipCurrentFile=False
						continue
															
					if args.crc:	
						if args.v:
							try:
								print "CRC for {0}: ".format(files)+crc(filepath)
							except zlib.error as e:
								print e.strerror						
						URL = "http://api.archive.vg/2.0/Game.getInfoByCRC/xml/7TTRM4MNTIKR2NNAGASURHJOZJ3QXQC5/"+crc(filepath)
					else:
						platform= getPlatformName(platformID)
						URL = "http://thegamesdb.net/api/GetGame.php?name="+filename+"&platform="+platform
					
					tree = ET.parse(urllib.urlopen(URL))
					
					if args.v:
						print "Trying to identify {}..".format(files)				
					
					if len(tree.getroot()) > 1: 														
						nodes=tree.getroot()						
						if args.crc:
							if nodes.findtext("games"):
								titleNode=nodes[2][0].find("title")
								descNode=nodes[2][0].find("description")
								imgNode=nodes[2][0].find("box_front")
								releaseDateNode=None
								publisherNode=None
								devNode=nodes[2][0].find("developer")
								genreNode=nodes[2][0].find("genre")
							else:
								break
						else:
							titleNode=nodes[1].find("GameTitle")
							descNode=nodes[1].find("Overview")
							imgBaseURL=nodes.find("baseImgUrl")
							imgNode=nodes[1].find("Images/boxart[@side='front']")
							releaseDateNode=nodes[1].find("ReleaseDate")
							publisherNode=nodes[1].find("Publisher")
							devNode=nodes[1].find("Developer")
							genreNode=nodes[1].find("Genres")
											
						if titleNode is not None:
							game = SubElement(gamelist, 'game')
							path = SubElement(game, 'path')	
							name = SubElement(game, 'name')	
							desc = SubElement(game, 'desc')
							image = SubElement(game, 'image')
							releasedate = SubElement(game, 'releasedate')														
							publisher=SubElement(game, 'publisher')
							developer=SubElement(game, 'developer')
							genres=SubElement(game, 'genres')
																						
							path.text=filepath
							name.text=titleNode.text						
							print "Game Found: "+titleNode.text
							
						else:
							break
		
						if descNode is not None:						
							desc.text=descNode.text	
																
						if imgNode is not None and args.noimg is False:													
							imgpath=os.path.abspath(os.path.join(root, filename+".jpg"))
							
							print "Downloading boxart.."
							if args.crc:
								os.system("wget -q "+imgNode.text+" --output-document=\""+imgpath+"\"")
							else:
								os.system("wget -q "+imgBaseURL.text+imgNode.text+" --output-document=\""+imgpath+"\"")							
							image.text=imgpath
							
							if args.w:
								maxWidth= args.w
								img=Image.open(imgpath)							
								if (img.size[0]>maxWidth):
									print "Boxart over {}px. Resizing boxart..".format(maxWidth)
									height = int((float(img.size[1])*float(maxWidth/float(img.size[0]))))							
									img.resize((maxWidth,height), Image.ANTIALIAS).save(imgpath)	
						
						if releaseDateNode is not None:
							releasedate.text=releaseDateNode.text
						
						if publisherNode is not None:
							publisher.text=publisherNode.text	
							
						if devNode is not None:
							developer.text=devNode.text				
							
						if genreNode is not None:
							if args.crc:
								for item in genreNode.text.split('>'):
									newgenre = SubElement(genres, 'genre')
									newgenre.text=item.strip()
							else:
								for item in genreNode.iter("genre"):
									newgenre = SubElement(genres, 'genre')
									newgenre.text=item.text

		KeepSearching = False
	
	if gamelist.find("game") is None:
		print "No new games added."
	else:
		print "{} games added.".format(len(gamelist))
		exportList(gamelist)
  
try:
	if os.getuid()==0:
		os.environ['HOME']="/home/"+os.getenv("SUDO_USER")
	config=open(os.environ['HOME']+"/.emulationstation/es_systems.cfg")
except IOError as e:
	sys.exit("Error when reading config file: {0}".format(e.strerror)+"\nExiting..")

ES_systems=readConfig(config)	
print parser.description

if args.w:
	print "Max width set: {}px.".format(str(args.w))
if args.noimg:
	print "Boxart downloading disabled."
if args.f:
	print "Re-scraping all games.."
if args.v:
	print "Verbose mode enabled."
if args.crc:
	print "CRC scraping enabled."
if args.p:
	print "Partial scraping enabled. Systems found:"			
	for i,v in enumerate(ES_systems):
		print "[{0}] {1}".format(i,v[0])	
	var = int(raw_input("System ID: "))
	getGameData(ES_systems[var][1],ES_systems[var][2],ES_systems[var][3])
else:
	for i,v in enumerate(ES_systems):
		getGameData(ES_systems[i][1],ES_systems[i][2],ES_systems[i][3])
		
print "All done!"
