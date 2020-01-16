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
# Lib. It has been modified to if the TurboJPEG lib is not there to use the 
# Python cv2 lib to do the same thing. It is MUCH slower. But should make it
# More portable. An error message should be issued if it fails to find the
# TurboJPEG Lib to let you know the performance will be worse
###############################################################################

from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import cv2
import glob 		#To get files
import os 			#We need this to Change Dirs
import shutil 		#we need this for move
import subprocess 	#we need this for calling other tools

import x3f_tools	#My Lib
try:
	from turbojpeg import TurboJPEG, TJPF_GRAY, TJSAMP_GRAY #From here: https://github.com/lilohuang/PyTurboJPEG
	jpeg = TurboJPEG(r'C:\libjpeg-turbo-gcc64\bin\libturbojpeg.dll')
except:
	print("Turbo JPEG not found. Please install it for much better performance")
	jpeg = None

# Global Defines
BOTTOM_FRAME_COLOR = '#666666'
BTN_COLOR = '#666666'
BTN_TEXT_COLOR = '#FFFFFF'

class ImgViewerGUI:
	def __init__(self,master):
		self.master = master
		master.geometry("860x600") #Default Size
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
		filemenu.add_command(label="Export DNG", command=self.menu_export_dng) #This is because I am ambitious
		filemenu.add_command(label="Export Tiff", command=self.menu_export_tiff)
		filemenu.add_command(label="Export JPG", command=self.donothing)
		filemenu.add_command(label="Export Embed JPG", command=self.menu_export_emd_jpeg)
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
		if(len(self.img_filelist) != 0):
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
		elif(event.keysym == 'r'): #This exports the embedded JPEG
			self.btn_rotate()
		elif(event.keysym == 'j'): #This exports the embedded JPEG
			self.menu_export_emd_jpeg()
		elif(event.keysym == 'd'): #This exports a DNG
			self.menu_export_dng()
		elif(event.keysym == 't'): #This exports a tiff
			self.menu_export_tiff()
	def click(self,event):
		self.coordinates[0]= event.x
		self.coordinates[1]= event.y
	def release(self,event):
		count = 1
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
		delete_folder_check(self.directory)
		src  = self.directory +"/"+ self.img_filelist[self.img_filelist_index]
		dest = self.directory +"/delete/"+ self.img_filelist[self.img_filelist_index]
		shutil.move(src,dest)
		self.update_filelist()
		self.img_filelist_index = (len(self.img_filelist) + self.img_filelist_index -1) % len(self.img_filelist)
		self.load_img(self.img_filelist[self.img_filelist_index])
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
	def menu_export_emd_jpeg(self):
		export_folder_check(self.directory)
		if(len(self.img_filelist) != 0):
			in_file = open(self.img_filelist[self.img_filelist_index], 'rb')
			jpg_pointer,jpg_size = x3f_tools.file_pointer_jpeg(in_file)
			jpeg_dir = self.directory+"/export"
			jpeg_name = jpeg_dir + "/" + os.path.splitext(self.img_filelist[self.img_filelist_index])[0] +".jpg"
			if(os.path.exists(jpeg_name) == 0): #It doesn't already exist
				in_file.seek(jpg_pointer, 0)
				out_file = open(jpeg_name,'wb')
				out_file.write(in_file.read(jpg_size))
				out_file.close()
			else:
				print(os.path.splitext(self.img_filelist[self.img_filelist_index])[0] +".jpg Already Exists")
		in_file.close()
	def menu_export_dng(self): #This is a call to another tool
		export_folder_check(self.directory)
		if(len(self.img_filelist) != 0):
			in_file   = self.directory + "/" + self.img_filelist[self.img_filelist_index]
			out_file  = self.directory + "/export/export_list.txt"
			dng_dir  = self.directory+"/export"
			fd = open(out_file, 'a+')
			fd.write(self.directory +"/"+ self.img_filelist[self.img_filelist_index] + " " +  dng_dir + " " + "dng\n")
			fd.close()
	def menu_export_tiff(self): #We write to a file
		export_folder_check(self.directory)
		if(len(self.img_filelist) != 0):
			in_file   = self.directory + "/" + self.img_filelist[self.img_filelist_index]
			out_file  = self.directory + "/export/export_list.txt"
			tiff_dir  = self.directory+"/export"
			fd = open(out_file, 'a+')
			fd.write(self.directory +"/"+ self.img_filelist[self.img_filelist_index] + " " +  tiff_dir + " " + "tiff\n")
			fd.close()
	#Helper Functions
	def donothing(self):
		print("No functionality Yet")
	def change_dir(self):
		self.directory = filedialog.askdirectory()
		os.chdir(self.directory)
		self.update_filelist()
		self.load_img(self.img_filelist[self.img_filelist_index])
	def load_img(self,filename): #New image is being read from the filesystem
		#print(filename)
		in_file = open(filename, 'rb')
		jpg_pointer = x3f_tools.file_pointer_jpeg(in_file)
		in_file.seek(jpg_pointer[0],0)
		if(jpeg == None): #We use the PIL method.
			#self.full_img = cv2.imdecode(in_file.read(jpg_pointer[1]), 1)
			img_data = np.asarray(bytearray(in_file.read(jpg_pointer[1])), dtype=np.uint8)
			self.full_img = cv2.imdecode(img_data, 1)
		else: #This is the faster TURBO Jpeg method
			self.full_img  = jpeg.decode(in_file.read(jpg_pointer[1]),scaling_factor=(1, 2))
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
			if(is_portrait(reduced_size)): #We need to center it only one dim when it's scaled
				offset[1] = reduced_size.shape[1]/-2 + self.img_space.winfo_width()/2
			else:
				offset[0] = reduced_size.shape[0]/-2 + self.img_space.winfo_height()/2
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

#Non Internal Functions to the GUI that help
def is_portrait(img): #0 is landscape, 1 is portrait
	width  = img.shape[1]
	height = img.shape[0]
	if(width < height):
		return 1
	else:
		return 0

#You provide it image dim, and canvas dim and it tells you how to center it
def center_coords(img_w,img_h,canvas_w,canvas_h): 
	print(img_w/-2 + canvas_w/2)
	print(img_h/-2 + canvas_h/2)
	
def export_folder_check(cur_path):
	if(os.path.exists(cur_path+"\export") == False): #If it doesn'y exist make it
		os.mkdir(cur_path+"\export")
		
def delete_folder_check(cur_path):
	if(os.path.exists(cur_path+"\delete") == False): #If it doesn'y exist make it
		os.mkdir(cur_path+"\delete")
		
			
# Init the application
root = Tk()
application = ImgViewerGUI(root)
root.mainloop()