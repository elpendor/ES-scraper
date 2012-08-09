import os, urllib, sys, Image, argparse
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

parser = argparse.ArgumentParser(description='TheGamesDB scraper for EmulationStation')
parser.add_argument("-w", metavar="value", help="defines a maximum width (in pixels) for boxarts (anything above that will be resized to that value)", type=int)
parser.add_argument("-noimg", help="disables boxart downloading",action='store_true')
args = parser.parse_args()

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
					
					if imgNode is not None and args.noimg is False:						
						print "Downloading boxart.."
						os.system("wget -q "+imgBaseURL.text+imgNode.text+" --output-document=\""+filename+".jpg\"")				
						image.text=os.path.abspath(filename+".jpg")
						
						if args.w:
							maxWidth= args.w
							img=Image.open(filename+".jpg")							
							if (img.size[0]>maxWidth):
								height = int((float(img.size[1])*float(maxWidth/float(img.size[0]))))								
								img.resize((maxWidth,height), Image.ANTIALIAS).save(filename+".jpg")
						
		KeepSearching = False
	
	indent(gamelist)
	ET.ElementTree(gamelist).write("gamelist.xml")
	print "Done! List saved on "+os.getcwd()+"/gamelist.xml"
  
try:
	config=open(os.environ['HOME']+"/.emulationstation/es_systems.cfg")
except IOError as e:
	sys.exit("Error when reading config file: {0}".format(e.strerror)+"\nExiting..")

print parser.description

if args.w:
    print "Max width set: {}px.".format(str(args.w))
if args.noimg:
	print "Boxart downloading disabled."
	
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
				
config.close()
print "All done!"
