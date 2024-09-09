# Wczytuje PKL zgodne z asset browser i pokazuje jego obrazki
# {main_folder, screen_path, mrvl_path, thumb_path, owner_path, cloth_name, remap_id, 'pixmaps'}
# Obrazki tworzę z dic['pixmaps'] if pix == QPixmap

import sys,os,pickle
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton,QGridLayout
from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QLineEdit, QTextEdit
from PyQt5.QtGui import QIcon, QPixmap, QFont, QFontMetrics
from PyQt5.QtCore import Qt,QByteArray,QBuffer,QIODevice, QRect, QSize, pyqtSignal

data_path=r'Z:\r6.assets\characters\garment\asset.pkl'
data_path=r'Z:\CP2077D\r6.assets\characters\garment\asset.pkl'
lab_size = QSize(200,150)
win_dim	  = QRect(511, 110, 1000, 800) # win_dim.x(), y(), width(), height()
scroll_width = 20

pixmaps = []
labs 	= []

def SavePkl(data,path):
	try:
		f=open(path,'wb')
		pickle.dump(data,f)
		f.close()
	except Exception as e: print(e)
def LoadPkl(path):      #return data
	f=open(path,'rb')
	data = pickle.load(f)
	f.close()
	return data
#Pixmap 2 QByteArray (pickleable) 
def Pix2Byte(pix):      #return myQByte
	if type(data) == QPixmap:
		myQByte =  QByteArray()
		buffer = QBuffer(myQByte)
		buffer.open(QIODevice.WriteOnly)
		pix.save(buffer, "JPG")
	else: myQByte = 'EMPTY!'
	return myQByte
#QByteArray to Pixmap
def Byte2Pix(data):     #return myPixmap
	if type(data) == QByteArray:
		myPixmap = QPixmap()
		myPixmap.loadFromData(data,"JPEG")
	else: myPixmap = 'EMPTY!'	
	return(myPixmap)
def create_labels(dic): #labels with additional data: lab.name, lab.pic_path
		labels = []
		lab_cnt = len(dic['pixmaps'])
		red_sign = ['??', '???', 'DEL', '!!!', 'XXX']

		for n in range(lab_cnt):
			nazwa 			= dic['cloth_name'][n]
			owner_name		= dic['owner_path'][n]
			is_marvelous  	= dic['mrvl_path'][n]

			lab = myLabel() # tworzę labelkę z nazwą = lista[0][n] czyli lista[name[n]]
			lab.setStyleSheet('background-color: rgba(0, 0, 0, 55);''color: rgb(240,235,255);')  
			lab.setMaximumSize(lab_size)
			lab.setMinimumSize(lab_size)           
			lab.pic_path = dic['main_folder'][n] + '\\' +dic['screen_path'][n]

			#Nazwa							
			lname 		= QLabel(lab)
			lname.resize(lab_size.width(), 20)
			lname.setText(nazwa)

			#owner			
			owner = QLineEdit(lab, placeholderText='??')
			if owner_name not in red_sign:
				owner.setStyleSheet('background-color: rgba(138, 128, 118, 88); border-radius: 5px;')
				owner.setText(owner_name)
			else: owner.setStyleSheet('background-color: rgba(255, 0, 0, 255); border-radius: 5px;')
			owner.resize(25,25)
			owner.move(lab_size.width()-30,lab_size.height()-30)

			#isMarvelous?
			lmrv 			= QLabel(lab)
			lmrv.resize(31,25)
			lmrv.move(5,lab_size.height()-30)
			if is_marvelous != 'EMPTY!': pass
			else: 
				lmrv.setStyleSheet('background-color: rgba(255, 0, 0, 22); border-radius: 5px;')
				lmrv.setText('NoMrv')
			#
			labels.append(lab)
		show_list(is_marvelous)		
		return(labels)     
def labels_2_layout(labels, layout):	#places labels from list into grid layout
		w_szer = (okno.size().width())
		lab_szer = (lab_size.width())
		x, y = 0, 0
		lab_xcnt = (w_szer//lab_szer)

		for lab in labels:
				layout.addWidget(lab, y,x)
				lab.show()
				x = x +1 
				if x == lab_xcnt:
						x=0
						y=y+1
def arrange_labels(labels, layout):		#rearanges labels on layout 2 fit window size
		for i in reversed(range(layout.count())): 
				layout.itemAt(i).widget().setParent(None)
		labels_2_layout(labels, layout)
def show_list(lista,tytul='Lista'):  #pokaż zawartość listy w nowym, skrolowanym oknie
	try:
		text=''
		#print(lista)
		for n in lista: text += str(n)+'\n'
		
		list_window=QWidget()
		list_window.setWindowTitle(tytul + ' : ' + str(len(lista)))
		
		text_ed = QTextEdit()
		text_ed.setText(text)
		textSize = QFontMetrics(text_ed.document().defaultFont()).size(0, text)
		text_ed.setMinimumSize(textSize+ QSize(250,30))


		#   Layouts set
		main_lay    = QVBoxLayout()     
		list_window.setLayout(main_lay)
	
		#   scroll
		scrollArea = QScrollArea()                  #dodaje scroll
		main_lay.addWidget(scrollArea)              #wrzucam scroll do lay12        
		scroll_window = QWidget()                   #dodaje okno
		scrollArea.setWidget(scroll_window)         #podpinam s_okno do scrola
		lay_11 = QVBoxLayout(scroll_window)         #tworze nowy layout podpiety pod scroll window
		lay_11.addWidget(text_ed)
		
		#label.resize(label.sizeHint())
		scroll_window.resize(scroll_window.sizeHint())
		list_window.resize(700,550)
		list_window.show()
	except Exception as e: print('show_list', e)
class myLabel (QLabel):			#Clickable label
		def __init__(self, nazwa='', parent=None):#v = self.id
				QLabel.__init__(self, parent)
				self.id=nazwa
		def mousePressEvent(self, ev): # self.clicked, self.mclicked, self.rclicked
				if ev.button()  == Qt.LeftButton: self.klik()                       
				elif ev.button()== Qt.MidButton:self.mklik()            
				else:self.rklik()

		def mklik(self):    #open 'M:\XENVS\meshes' folder and selects proper file
				print('mklik')               
			  
		def klik(self):     #open screen of model
			try:
				print('klik')
				os.startfile(self.pic_path)
			except Exception as e: print(e)
		def rklik(self):    #open asset folder
				print('Rklik')
class myScroll (QScrollArea): 	#Resizeable scrollwindow rearranging children
		def __init__(self):
				super().__init__()
				self.run()
		def resizeEvent(self, event):
				try: arrange_labels(labs, lay0)
				except: pass
				QScrollArea.resizeEvent(self, event) 
		def run(self):
				self.setWidgetResizable(True)
				self.show()
		def closeEvent(self, evnt):
				print('Bye')
				#save_pkl(characters)
				#save_json(characters)
				#os.startfile(Path_1)

if __name__ == '__main__':
	app 	= QApplication(sys.argv)
	okno	= myScroll()
	canvas  = QWidget()
	okno.setWindowTitle('ASSET VIEWER')
	lay0 	= QGridLayout(canvas)
	okno.setGeometry(win_dim)
	okno.setWidget(canvas)

	asset_info = LoadPkl(data_path)
	labs = create_labels(asset_info)
	labels_2_layout(labs, lay0)				#places labels from list into grid layout

	QBList = asset_info['pixmaps']


	for q in QBList:
		pixmaps.append(Byte2Pix(q))

	for n, val in enumerate(pixmaps):
		if type(val) == QPixmap: labs[n].setPixmap(val)

	nazwa = 'ASSET VIEWER - model count = ' + str(len(asset_info['main_folder'])) + '     Use Asset_Tracker to update database ( Z:\\r6.assets\\characters\\garment\\asset.pkl )'
	okno.setWindowTitle(nazwa)
	okno.show()
	sys.exit(app.exec_())

