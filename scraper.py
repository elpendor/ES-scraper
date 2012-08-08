import os, urllib, sys
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
           		
def getPlatformName(id):
	platform_data = ET.parse(urllib.urlopen("http://thegamesdb.net/api/GetPlatform.php?id="+id))
	return platform_data.find('Platform/Platform').text

def getGameData(folder,extension,platformID):	
	KeepSearching = True
	gamelist = Element('gameList')	
	while KeepSearching:        
		print "Scanning folder..("+folder+")"
		os.chdir(os.path.expanduser(folder))		
		for files in os.listdir("./"):
			if files.endswith(extension):			
				filename = os.path.splitext(files)[0]
				platform= getPlatformName(platformID)
				URL = "http://thegamesdb.net/api/GetGame.php?name="+filename+"&platform="+platform
				tree = ET.parse(urllib.urlopen(URL))
				for node in tree.getiterator('Data'):				
																		
					titleNode=node.find("Game/GameTitle")
					descNode=node.find("Game/Overview")
					imgBaseURL=node.find("baseImgUrl")
					imgNode=node.find("Game/Images/boxart[@side='front']")
																																		
					if titleNode is not None:
						game = SubElement(gamelist, 'game')
						path = SubElement(game, 'path')	
						name = SubElement(game, 'name')	
						desc = SubElement(game, 'desc')
						image = SubElement(game, 'image')																	
						
						path.text=os.path.abspath(files)
						name.text=titleNode.text
						
						print "Game Found: "+titleNode.text
					else:
						break
	
					if descNode is not None:						
						desc.text=descNode.text	
					else:
						desc.text=""
					
					if imgNode is not None:						
						print "Downloading boxart.."
						os.system("wget -q "+imgBaseURL.text+imgNode.text+" --output-document=\""+filename+".jpg\"")				
						image.text=os.path.abspath(filename+".jpg")
					else:
						image.text=""

		KeepSearching = False
	
	ET.ElementTree(gamelist).write("gamelist.xml")
	print "Done! List saved on "+os.getcwd()+"/gamelist.xml"

try:
	config=open(os.environ['HOME']+"/.emulationstation/es_systems.cfg")
except IOError as e:
	sys.exit("Error when reading config file: {0}".format(e.strerror)+"\nExiting..")

print "TheGamesDB scraper for EmulationStation"
lines=config.read().splitlines()
for line in lines:
	if not line.strip() or line[0]=='#':
		continue
	else:
		if "PATH=" in line:
			path =line.split('=')[1]		
		elif "EXTENSION" in line:
			ext=line.split('=')[1]
		elif "PLATFORMID" in line:
			pid=line.split('=')[1]
			if not pid:
				continue
			else:				
				getGameData(path,ext,pid)
print "All done!"