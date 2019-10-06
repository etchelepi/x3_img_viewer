###############################################################################
# Program Name: ImgViewerGUI
#
# Author: Evan Tchelepi
#
# Create Date: 2-3-2019
#
# Function: This is a python tinker based GUI to view x3f files.
#
# Notes: This version works on JPEGs. It also requires the Turbo JPEG python
# Lib. You can remove all the turbo JPEG code and it works, but it's much
# slower, because the python jpeg decoder doesn't take advantage of any hw
# Acceleration
###############################################################################

from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from turbojpeg import TurboJPEG, TJPF_GRAY, TJSAMP_GRAY #From here: https://github.com/lilohuang/PyTurboJPEG
import numpy as np
import cv2
import glob

#My Required Libs
import x3f_tools

jpeg = TurboJPEG()

# Global Defines
BOTTOM_FRAME_COLOR = '#666666'
BTN_COLOR = '#666666'
BTN_TEXT_COLOR = '#FFFFFF'

class ImgViewerGUI:
	def __init__(self,master):
		self.master = master
		master.geometry("800x600") #Default Size
		master.title("X3F Quick Viewer")
		master.bind_all('<Key>', self.key)
		# ---------------------------------------------------------------------
		# Global vars for the object
		self.coordinates = [0,0] #So we can store and share where some coordinates are
		self.canvas_size = [0,0]
		self.img_handle = 0 #This holds our Image Object so we can modify it
		self.view_btn_text = StringVar()
		self.full_img = None
		self.img_filelist=[]
		self.img_filelist_index=0
		# ---------------------------------------------------------------------
		menubar = Menu(master) # Define the Menu Bar
		filemenu = Menu(menubar, tearoff=0) #Define the File menu
		filemenu.add_command(label="Open Dir", command=self.change_dir)
		filemenu.add_command(label="Export DNG", command=self.donothing) #This is because I am ambitious
		filemenu.add_command(label="Export Tiff", command=self.donothing)
		filemenu.add_command(label="Export JPG", command=self.donothing)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=master.quit)
		menubar.add_cascade(label="File", menu=filemenu)
		helpmenu = Menu(menubar, tearoff=0) #Define the Help Menu
		helpmenu.add_command(label="Help Index", command=self.donothing)
		helpmenu.add_command(label="About...", command=self.donothing)
		menubar.add_cascade(label="Help", menu=helpmenu)
		master.config(menu=menubar) #Add to the root object
		# ---------------------------------------------------------------------
		self.img_space = Canvas(master,bg = '#808080')
		self.img_space.pack(side = TOP, fill = BOTH, expand = True)
		self.img_space.bind('<ButtonPress-1>', self.click)
		self.img_space.bind('<ButtonRelease-1>', self.release)
		self.img_space.bind("<B1-Motion>", self.drag_img) 
		self.img_space.bind("<Configure>", self.canvas_size_change)
		self.img_label = Label(self.img_space)
		# This setups the Bottom Bar which always stays anchored there
		self.bottom_frame = Frame(master,bg=BOTTOM_FRAME_COLOR)
		self.bottom_frame.pack( side = BOTTOM,fill = X)
		self.btn_frame = Frame(self.bottom_frame,bg='green') #This is setup so the BTNs stay centered
		self.btn_frame.pack(side = BOTTOM)

		self.prv_btn = Button(self.btn_frame, bg=BTN_COLOR,fg=BTN_TEXT_COLOR,text="<<",command=self.btn_prev)
		self.prv_btn.pack( side = LEFT)

		self.focus_btn = Button(self.btn_frame, bg=BTN_COLOR,fg=BTN_TEXT_COLOR,text="Display Focus",command=self.show_focus)
		self.focus_btn.pack( side = LEFT)

		self.zoom_btn = Button(self.btn_frame,bg=BTN_COLOR,fg=BTN_TEXT_COLOR,textvariable=self.view_btn_text,command=self.fit_zoom_btn)
		self.zoom_btn.pack(side = LEFT)
		self.view_btn_text.set("1:1")

		self.rotate_btn = Button(self.btn_frame,bg=BTN_COLOR,fg=BTN_TEXT_COLOR,text="Rotate",command=self.btn_rotate)
		self.rotate_btn.pack( side = LEFT )

		self.next_btn = Button(self.btn_frame,bg=BTN_COLOR,fg=BTN_TEXT_COLOR,text=">>",command=self.btn_next)
		self.next_btn.pack( side = LEFT )
		# Init Function Calls--------------------------------------------------
		master.update() #So Canvas Sizes will be updated
		self.update_filelist()
		self.load_img(self.img_filelist[0])
	# -------------------------------------------------------------------------
	#Button and Mouse Event Functions
	def key(self,event):
		if(event.keysym == 'Right'):
			self.btn_next()
		elif(event.keysym == 'Left'):
			self.btn_prev()
		elif(event.keysym == 'Delete'): #This is only a key shortcut. No Btn to press on screen
			self.btn_delete()
		else:
			print ("pressed", repr(event.char))
	def click(self,event):
		self.coordinates[0]= event.x
		self.coordinates[1]= event.y
	def release(self,event):
		print ("release at", event.x ,event.y)
	def canvas_size_change(self,event):
		self.canvas_size[0] = event.width
		self.canvas_size[1] = event.height
		if self.full_img is not None: #This gets called once when first run and updated before an image is set
			self.update_img() #Refresh the image
	def drag_img(self,event): #When in 1:1 view, allow the image to be dragged
		delta = [ event.x-self.coordinates[0],event.y-self.coordinates[1]]
		self.coordinates[0]= event.x
		self.coordinates[1]= event.y
		if(self.view_btn_text.get() == "FIT"): #Move only on 1:1 view
			self.img_space.move(self.img_handle,int(delta[0]*1.5),int(delta[1]*1.5))
	#Button Functions
	def btn_prev(self): #Function to select the Previous Image in the Filelist
		self.img_filelist_index = (len(self.img_filelist) + self.img_filelist_index -1) % len(self.img_filelist)
		self.load_img(self.img_filelist[self.img_filelist_index])		
	def btn_next(self): #Function to select the Next Image in the Filelist
		self.img_filelist_index = (self.img_filelist_index + 1) % len(self.img_filelist)
		self.load_img(self.img_filelist[self.img_filelist_index])
	def btn_rotate(self):
		self.full_img = np.rot90(self.full_img,1)
		self.update_img() #Refresh the image
	def btn_delete(self):
		print("This Function will erase: ",self.img_filelist[self.img_filelist_index])
	def fit_zoom_btn(self): #Function to change the zoom of the display
		if(self.view_btn_text.get() == "1:1"):
			self.view_btn_text.set("FIT")
		else:
			self.view_btn_text.set("1:1")
		self.update_img() #Refresh the image
	def show_focus(self):
		self.full_img = cv2.GaussianBlur(cv2.Canny(self.full_img,10,400),(9,9),0)
		self.update_img() #Refresh the image
	#Helper Functions
	def donothing(self):
		print("No functionality Yet")
	def change_dir(self):
		self.directory = filedialog.askdirectory()
		self.update_filelist()
	def load_img(self,filename): #New image is being read from the filesystem
		print(filename)
		in_file = open(filename, 'rb')
		jpg_pointer = x3f_tools.file_pointer_jpeg(in_file)
		in_file.seek(jpg_pointer[0],0)
		self.full_img  = jpeg.decode(in_file.read(jpg_pointer[1]))
		in_file.close()
		self.update_img() #Refresh the image
	def update_img(self): #The image has not changed, but we want to update it being draw
		offset = [0,0]
		if(self.view_btn_text.get() == "FIT"): #We do opposite because the btn changes it not sets it
			self.img_label.image = ImageTk.PhotoImage(image = Image.fromarray(cv2.cvtColor(self.full_img, cv2.COLOR_BGR2RGBA)))
			#Lets Make sure we center the image in the Canvas
			offset[0] = self.full_img.shape[0]/-2 + self.img_space.winfo_width()/2
			offset[1] = self.full_img.shape[1]/-2 + self.img_space.winfo_height()/2
		else:
			reduced_size = cv2.cvtColor(cv2.resize(self.full_img, self.get_scale_factor(),interpolation=cv2.INTER_NEAREST), cv2.COLOR_BGR2RGBA)
			self.img_label.image = ImageTk.PhotoImage(image = Image.fromarray(reduced_size))
		self.img_handle = self.img_space.create_image(offset[1],offset[0], anchor = NW,image=self.img_label.image)
	def update_filelist(self):
		self.img_filelist = glob.glob("*.X3F")
	def get_scale_factor(self): #This function is gross. Needs to be rewritten
		scale_factor = 1.0
		win_w = self.canvas_size[0] #The Window Dimensions
		win_h = self.canvas_size[1] 
		img_w = self.full_img.shape[1] #The Image Dimensions
		img_h = self.full_img.shape[0]
		if (win_w > win_h): #The Window is wide
			if(img_w > img_h):#The img is also wide
				scale_factor = win_w/img_w
				if(img_h*scale_factor > win_h): #Check and correct if it's too big
					scale_factor= win_h/img_h
			else: #The image is Tall
				scale_factor = win_h/img_h
				if(img_w*scale_factor > win_w): #Check and correct if it's too big
					scale_factor= win_w/img_w
		else: #The window has to be narrow
			if(img_w > img_h):#The img is wide
				scale_factor = win_w/img_w
				if(img_h*scale_factor > win_h): #Check and correct if it's too big
					scale_factor= win_h/img_h
			else: #The image is Tall
				scale_factor = win_h/img_h
				if(img_w*scale_factor > win_w): #Check and correct if it's too big
					scale_factor= win_w/img_w
		width = int(img_w * scale_factor)
		height = int(img_h * scale_factor)
		dim = (width,height)
		return dim


# Init the application
root = Tk()
application = ImgViewerGUI(root)
root.mainloop()