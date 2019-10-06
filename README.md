# x3_img_viewer
This is a img viewer for x3f files

This is a Tkinker Framework for being able to view and cull images.

Supported OS:
1. Windows 10
2. Linux 

Notes:

1. This requires the Turbo Jpeg Python Wrapper. It will work without it, but decoding JPEGs is slow with the default python libs, so it's worth while to take advantage of the lib. If you don't want to use it. You need to comment out the lines and just read them with the openCV type functions.

2. This works on the embedded JPEGs, the x3f_tools has some ability to parse, but extracting the raw files is too slow. There is a C version of the tools, which should be a drop in replacement whenever I finish it.

3. There are lots of things laid out, but that don't do anything. It's really a frame work for a easy to edit and update x3f viewer. It's limited in use as it exists.

