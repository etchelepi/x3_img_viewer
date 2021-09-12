import collections
import cv2
import numpy as np
from matplotlib import pyplot as plt

# -----------------------------------------------------------------------------
# CONSTANTS
HEADER_FOVB = b'FOVb'
DIRECTORY_SECI = b'SECi'
IMG_DATA_TYPE_JPG = 2
IMG_DATA_FORMAT_JPG = 18

# -----------------------------------------------------------------------------
def byte_to_int(data):
    temp = 0;
    length = len(data)
    for x in range(0,length):
        temp = temp * 256
        temp = temp + data[x]
    return temp

# -----------------------------------------------------------------------------
def l_endian(data):
    length = len(data)
    temp = bytearray(length);
    for x in range(0,length):
        temp[x] = data[(length-1)-x]
    return temp

# -----------------------------------------------------------------------------
def get_directory_table(fd):
	fd.seek(0, 0)                           # Go to the start of the file
	word_32b = fd.read(4)                 # Read the first 4 bytes for a Header
	if word_32b != HEADER_FOVB:           # Check that it's legit
		print ("NOT VALID X3F FILE")
		exit(0)
	fd.seek(-4, 2)                          # Go to the end to find the Directory OFFSET
	directory_offset = byte_to_int(l_endian(fd.read(4)))
	fd.seek(directory_offset, 0)            # Go to the directory offset
	section_identifer = fd.read(4)
	dir_version = l_endian(fd.read(4))
	num_dir_enteries = byte_to_int(l_endian(fd.read(4)))
	dir_entry = []
	x3f_dir_entry = collections.namedtuple('x3f_dir_entry', ['offset', 'size', 'dirtype','header'])
	for x in range(0, num_dir_enteries):    # Read Each Item and save the details
		OFFSET = byte_to_int(l_endian(fd.read(4)))
		SIZE = byte_to_int(l_endian(fd.read(4)))
		TYPE = fd.read(4)
		entry = x3f_dir_entry(offset = OFFSET,size = SIZE, dirtype = TYPE, header =  dict())
		dir_entry.append(entry)
	for x in range (0,num_dir_enteries):    # Now go save the headers for the dir entries
		fd.seek(dir_entry[x].offset, 0)
		dir_entry[x].header.update({'sec_id': fd.read(4)})
		if( dir_entry[x].header['sec_id'] == DIRECTORY_SECI):
			dir_entry[x].header.update({'img_format': l_endian(fd.read(4))})
			dir_entry[x].header.update({'data_type': byte_to_int(l_endian(fd.read(4)))})
			dir_entry[x].header.update({'data_format': byte_to_int(l_endian(fd.read(4)))})
			dir_entry[x].header.update({'img_cols': byte_to_int(l_endian(fd.read(4)))})
			dir_entry[x].header.update({'img_rows': byte_to_int(l_endian(fd.read(4)))})
			dir_entry[x].header.update({'row_size': l_endian(fd.read(4))})
			#28 is 4 * num entries
			dir_entry[x].header.update({'data_offset' : (dir_entry[x].offset + 28)})
			dir_entry[x].header.update({'data_size' : (dir_entry[x].size - 28)})
	return dir_entry

# -----------------------------------------------------------------------------
#This Returns the file offset for the JPEG data and the size
def file_pointer_jpeg(fd):
	dir_list = get_directory_table(fd)
	for x in range(0, len(dir_list)):
		if(dir_list[x].header['sec_id'] == DIRECTORY_SECI):
			if(dir_list[x].header['data_type'] == IMG_DATA_TYPE_JPG):
				if(dir_list[x].header['data_format']  == IMG_DATA_FORMAT_JPG):
					return (dir_list[x].header['data_offset'],dir_list[x].header['data_size'])

