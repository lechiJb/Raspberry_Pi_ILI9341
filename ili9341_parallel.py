# Derived from - the library by Tony DiCola
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import numbers
import time
import RPi.GPIO as GPIO
#import spidev as SPI

from PIL import Image, ImageDraw, ImageFont



# Constants for interacting with display registers.
ILI9341_TFTWIDTH    = 240
ILI9341_TFTHEIGHT   = 320

ILI9341_NOP         = 0x00
ILI9341_SWRESET     = 0x01
ILI9341_RDDID       = 0x04
ILI9341_RDDST       = 0x09

ILI9341_SLPIN       = 0x10
ILI9341_SLPOUT      = 0x11
ILI9341_PTLON       = 0x12
ILI9341_NORON       = 0x13

ILI9341_RDMODE      = 0x0A
ILI9341_RDMADCTL    = 0x0B
ILI9341_RDPIXFMT    = 0x0C
ILI9341_RDIMGFMT    = 0x0A
ILI9341_RDSELFDIAG  = 0x0F

ILI9341_INVOFF      = 0x20
ILI9341_INVON       = 0x21
ILI9341_GAMMASET    = 0x26
ILI9341_DISPOFF     = 0x28
ILI9341_DISPON      = 0x29

ILI9341_CASET       = 0x2A
ILI9341_PASET       = 0x2B
ILI9341_RAMWR       = 0x2C
ILI9341_RAMRD       = 0x2E

ILI9341_PTLAR       = 0x30
ILI9341_MADCTL      = 0x36
ILI9341_PIXFMT      = 0x3A

ILI9341_FRMCTR1     = 0xB1
ILI9341_FRMCTR2     = 0xB2
ILI9341_FRMCTR3     = 0xB3
ILI9341_INVCTR      = 0xB4
ILI9341_DFUNCTR     = 0xB6

ILI9341_PWCTR1      = 0xC0
ILI9341_PWCTR2      = 0xC1
ILI9341_PWCTR3      = 0xC2
ILI9341_PWCTR4      = 0xC3
ILI9341_PWCTR5      = 0xC4
ILI9341_VMCTR1      = 0xC5
ILI9341_VMCTR2      = 0xC7

ILI9341_RDID1       = 0xDA
ILI9341_RDID2       = 0xDB
ILI9341_RDID3       = 0xDC
ILI9341_RDID4       = 0xDD

ILI9341_GMCTRP1     = 0xE0
ILI9341_GMCTRN1     = 0xE1

ILI9341_PWCTR6      = 0xFC

ILI9341_BLACK       = 0x0000
ILI9341_BLUE        = 0x001F
ILI9341_RED         = 0xF800
ILI9341_GREEN       = 0x07E0
ILI9341_CYAN        = 0x07FF
ILI9341_MAGENTA     = 0xF81F
ILI9341_YELLOW      = 0xFFE0
ILI9341_WHITE       = 0xFFFF

# for the rotation definition
ILI9341_MADCTL_MY = 0x80
ILI9341_MADCTL_MX = 0x40
ILI9341_MADCTL_MV = 0x20
ILI9341_MADCTL_ML = 0x10
ILI9341_MADCTL_RGB = 0x00
ILI9341_MADCTL_BGR = 0x08
ILI9341_MADCTL_MH = 0x04


def color565(r, g, b):
	"""Convert red, green, blue components to a 16-bit 565 RGB value. Components
	should be values 0 to 255.
	"""
	return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def color_rgb(color):
	"""Convert 565 color format to rgb - return tuple"""
	r = (color >> 8) & 0xf8
	g = ((color >> 5) & 0x3f) << 2
	b = (color & 0x1f) << 3
	return (r,g,b)

class ili9341(object):
	"""Representation of an ILI9341 TFT LCD."""

	def __init__(self, rs, rd, wr, cs, db8, db9, db10, db11, db12, db13, db14, db15, rst, width=ILI9341_TFTWIDTH, height=ILI9341_TFTHEIGHT):
		
		self._gpio = GPIO
		self._gpio.setmode(GPIO.BCM)

		self._rs = rs		#Select command / data
		self._gpio.setup(rs, GPIO.OUT)

		self._rst = rst		#Reset
		self._gpio.setup(rst, GPIO.OUT)

		self._rd = rd		#Read
		self._gpio.setup(rd, GPIO.OUT)

		self._wr = wr		#Write
		self._gpio.setup(wr, GPIO.OUT)

		self._cs = cs		#Write
		self._gpio.setup(cs, GPIO.OUT)

		self._db8 = db8		#Data-outputs
		self._db9 = db9
		self._db10 = db10
		self._db11 = db11
		self._db12 = db12
		self._db13 = db13
		self._db14 = db14
		self._db15 = db15

		self._gpio.setup(db8, GPIO.OUT)
		self._gpio.setup(db9, GPIO.OUT)
		self._gpio.setup(db10, GPIO.OUT)
		self._gpio.setup(db11, GPIO.OUT)
		self._gpio.setup(db12, GPIO.OUT)
		self._gpio.setup(db13, GPIO.OUT)
		self._gpio.setup(db14, GPIO.OUT)
		self._gpio.setup(db15, GPIO.OUT)

			
		self.width = width
		self.height = height
		
		
		# Create an image buffer.
		self.buffer = bytearray(width*height*2)
		self._row = 0
		self._col = 0
		self._color = 0
		self._bground = 0xf100
		self._font = ImageFont.truetype('/home/pi/python/OpenSans-Regular.ttf', 60)



	def LCD_Writ_COLORBus(self, VH, VL):

		#LCD_DataPortH=VH;
		self._gpio.output(self._db8, VH & 0x01)
		self._gpio.output(self._db9, VH & 0x02)
		self._gpio.output(self._db10, VH & 0x04)
		self._gpio.output(self._db11, VH & 0x08)
		self._gpio.output(self._db12, VH & 0x10)
		self._gpio.output(self._db13, VH & 0x20)
		self._gpio.output(self._db14, VH & 0x40)
		self._gpio.output(self._db15, VH & 0x80)
	
		#LCD_WR=0;
		self._gpio.setup(self._wr, GPIO.LOW)
		#LCD_WR=1; 
		self._gpio.setup(self._wr, GPIO.HIGH)

		#LCD_DataPortH=VL;	
		self._gpio.output(self._db8, VL & 0x01)
		self._gpio.output(self._db9, VL & 0x02)
		self._gpio.output(self._db10, VL & 0x04)
		self._gpio.output(self._db11, VL & 0x08)
		self._gpio.output(self._db12, VL & 0x10)
		self._gpio.output(self._db13, VL & 0x20)
		self._gpio.output(self._db14, VL & 0x40)
		self._gpio.output(self._db15, VL & 0x80)
		
		#LCD_WR=0;
		self._gpio.setup(self._wr, GPIO.LOW)
		#LCD_WR=1; 
		self._gpio.setup(self._wr, GPIO.HIGH)


	def LCD_Writ_COMBus(self, da):

	  	#LCD_DataPortH=da;
		self._gpio.output(self._db8, VH & 0x01)
		self._gpio.output(self._db9, VH & 0x02)
		self._gpio.output(self._db10, VH & 0x04)
		self._gpio.output(self._db11, VH & 0x08)
		self._gpio.output(self._db12, VH & 0x10)
		self._gpio.output(self._db13, VH & 0x20)
		self._gpio.output(self._db14, VH & 0x40)
		self._gpio.output(self._db15, VH & 0x80)

		#LCD_WR=0;
		self._gpio.setup(self._wr, GPIO.LOW)
		#LCD_WR=1; 
		self._gpio.setup(self._wr, GPIO.HIGH)	


	def LCD_WR_DATA8(self, VH,VL):

	  	#LCD_RS=1;
		self._gpio.setup(self._rs, GPIO.HIGH)
		self.LCD_Writ_COLORBus(VH,VL)


	def LCD_WR_DATA(self, da):

		#LCD_RS=1;
		self._gpio.setup(self._rs, GPIO.HIGH)
		self.LCD_Writ_COLORBus(da>>8,da)


	def LCD_WR_COMDATA(self, da):

		#LCD_RS=1;
		self._gpio.setup(self._rs, GPIO.HIGH)
		self.LCD_Writ_COMBus(da)


	def LCD_WR_REG(self, da):
	
  		#LCD_RS=0;
		self._gpio.setup(self._rs, GPIO.LOW)
		self.LCD_Writ_COMBus(da)


	def LCD_WR_REG_DATA(self, reg, da):

		self.LCD_WR_REG(reg)
		self.LCD_WR_COMDATA(da)


	def Address_set(self, x1, y1, x2, y2)

		self.LCD_WR_REG(0x2A)
		self.LCD_WR_COMDATA(x1>>8)
		self.LCD_WR_COMDATA(x1)
		self.LCD_WR_COMDATA(x2>>8)
		self.LCD_WR_COMDATA(x2)

		self.LCD_WR_REG(0x2B)
		self.LCD_WR_COMDATA(y1>>8)
		self.LCD_WR_COMDATA(y1)
		self.LCD_WR_COMDATA(y2>>8)
		self.LCD_WR_COMDATA(y2)
		self.LCD_WR_REG(0x2c)						 


	def _init(self):
		# Initialize the display.  Broken out as a separate function so it can
		# be overridden by other displays in the future.
		
		self._gpio.setup(self._cs, GPIO.HIGH)
		#if(LCD_CS==0)
		#{
		#   LCD_WR_REG_DATA(0,0);
		#   LCD_ShowString(0,0," ");
		#   LCD_ShowNum(0,0,0,0);
		#   LCD_Show2Num(0,0,0,0);
		#   LCD_DrawPoint_big(0,0);
		#   LCD_DrawRectangle(0,0,0,0);
		#   Draw_Circle(0,0,0);
	 	# }
		self._gpio.setup(self._rd, GPIO.HIGH)
		self._gpio.setup(self._wr, GPIO.HIGH)
		self._gpio.setup(self._rst, GPIO.LOW)
		time.sleep(0.02)
		self._gpio.setup(self._rst, GPIO.HIGH)
		time.sleep(0.02)	
		self._gpio.setup(self._cs, GPIO.LOW)


		#Start Initial Sequence
		self.LCD_WR_REG(0xcf)
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0xc1)
		self.LCD_WR_COMDATA(0x30)

		self.LCD_WR_REG(0xed)
		self.LCD_WR_COMDATA(0x64)
		self.LCD_WR_COMDATA(0x03)
		self.LCD_WR_COMDATA(0x12)
		self.LCD_WR_COMDATA(0x81)

		self.LCD_WR_REG(0xcb)
		self.LCD_WR_COMDATA(0x39)
		self.LCD_WR_COMDATA(0x2c)
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0x34)
		self.LCD_WR_COMDATA(0x02)

		self.LCD_WR_REG(0xea)
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0x00)

		self.LCD_WR_REG(0xe8)
		self.LCD_WR_COMDATA(0x85)
		self.LCD_WR_COMDATA(0x10)
		self.LCD_WR_COMDATA(0x79)

		self.LCD_WR_REG(0xC0) #Power control
		self.LCD_WR_COMDATA(0x23) #VRH[5:0]

		self.LCD_WR_REG(0xC1) #Power control
		self.LCD_WR_COMDATA(0x11) #SAP[2:0];BT[3:0]

		self.LCD_WR_REG(0xC2)
		self.LCD_WR_COMDATA(0x11)

		self.LCD_WR_REG(0xC5) #VCM control
		self.LCD_WR_COMDATA(0x3d)
		self.LCD_WR_COMDATA(0x30)

		self.LCD_WR_REG(0xc7) 
		self.LCD_WR_COMDATA(0xaa)

		self.LCD_WR_REG(0x3A) 
		self.LCD_WR_COMDATA(0x55)

		self.LCD_WR_REG(0x36) #Memory Access Control
		self.LCD_WR_COMDATA(0x08)

		self.LCD_WR_REG(0xB1) #Frame Rate Control
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0x11)

		self.LCD_WR_REG(0xB6) #Display Function Control
		self.LCD_WR_COMDATA(0x0a)
		self.LCD_WR_COMDATA(0xa2)

		self.LCD_WR_REG(0xF2) #3Gamma Function Disable
		self.LCD_WR_COMDATA(0x00)

		self.LCD_WR_REG(0xF7)
		self.LCD_WR_COMDATA(0x20)

		self.LCD_WR_REG(0xF1)
		self.LCD_WR_COMDATA(0x01)
		self.LCD_WR_COMDATA(0x30)

		self.LCD_WR_REG(0x26) #Gamma curve selected
		self.LCD_WR_COMDATA(0x01)

		self.LCD_WR_REG(0xE0) #Set Gamma
		self.LCD_WR_COMDATA(0x0f)
		self.LCD_WR_COMDATA(0x3f)
		self.LCD_WR_COMDATA(0x2f)
		self.LCD_WR_COMDATA(0x0c)
		self.LCD_WR_COMDATA(0x10)
		self.LCD_WR_COMDATA(0x0a)
		self.LCD_WR_COMDATA(0x53)
		self.LCD_WR_COMDATA(0xd5)
		self.LCD_WR_COMDATA(0x40)
		self.LCD_WR_COMDATA(0x0a)
		self.LCD_WR_COMDATA(0x13)
		self.LCD_WR_COMDATA(0x03)
		self.LCD_WR_COMDATA(0x08)
		self.LCD_WR_COMDATA(0x03)
		self.LCD_WR_COMDATA(0x00)

		self.LCD_WR_REG(0xE1) #Set Gamma
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0x00)
		self.LCD_WR_COMDATA(0x10)
		self.LCD_WR_COMDATA(0x03)
		self.LCD_WR_COMDATA(0x0f)
		self.LCD_WR_COMDATA(0x05)
		self.LCD_WR_COMDATA(0x2c)
		self.LCD_WR_COMDATA(0xa2)
		self.LCD_WR_COMDATA(0x3f)
		self.LCD_WR_COMDATA(0x05)
		self.LCD_WR_COMDATA(0x0e)
		self.LCD_WR_COMDATA(0x0c)
		self.LCD_WR_COMDATA(0x37)
		self.LCD_WR_COMDATA(0x3c)
		self.LCD_WR_COMDATA(0x0F)
		self.LCD_WR_REG(0x11) #Exit Sleep
		time.sleep(0.08)
		self.LCD_WR_REG(0x29) #display on

		

	def begin(self):
		"""Initialize the display.  Should be called once before other calls that
		interact with the display are called.
		"""
		#self.reset()
		self._init()



	def LCD_Clear(self, Color)
	
		VH=Color>>8;
		VL=Color;	
		self.Address_set(0,0,self.width-1,self.height-1);
		for i in range(self.width):
			for j in range(self.height):
				self.LCD_WR_DATA8(VH,VL);
	


	def set_window(self, x0=0, y0=0, x1=None, y1=None):
		"""Set the pixel address window for proceeding drawing commands. x0 and
		x1 should define the minimum and maximum x pixel bounds.  y0 and y1
		should define the minimum and maximum y pixel bound.  If no parameters
		are specified the default will be to update the entire display from 0,0
		to 239,319.
		"""
		if x1 is None:
			x1 = self.width-1
		if y1 is None:
			y1 = self.height-1
		
		self.Address_set(x0,y0,x1,y1);

		
	def pixel(self, x, y, color):
		"""Set an individual pixel to color"""
		if(x < 0) or (x >= self.width) or (y < 0) or (y >= self.height):
			return
		self.set_window(x,y,x+1,y+1)
		#b=[color>>8, color & 0xff]
		#self.data(b)		
		self.LCD_WR_DATA(color)		
		
		
	def draw_block(self,x,y,w,h,color):
		"""Draw a solid block of color"""
		if((x >= self.width) or (y >= self.height)):
			return
		if (x + w - 1) >= self.width:
			w = self.width  - x
		if (y + h - 1) >= self.height:
			h = self.height - y
		self.set_window(x,y,x+w-1,y+h-1)
		#b=[color>>8, color & 0xff]*w*h
		#self.data(b)
		self.LCD_WR_DATA(color)	

	def draw_bmp(self,x,y,w,h,buff):
		"""Draw the contents of buff on the screen"""
		# self.dump(buff)

		if((x >= self.width) or (y >= self.height)):
			return
		if (x + w - 1) >= self.width:
			w = self.width  - x
		if (y + h - 1) >= self.height:
			h = self.height - y
			
		self.set_window(x,y,x+w-1,y+h-1)
		#self.data(buff)
		for i in range(w):
			for j in range(h):
				self.LCD_WR_DATA(buff[i + j*w])


	def fill_screen(self,color):
		"""Fill the whole screen with color"""
		self.draw_block(0,0,self.width,self.height,color)
		

	def p_char(self, ch):
		"""Print a single char at the location determined by globals row and col
			row and col will be auto incremented to wrap horizontally and vertically"""
		fp = (ord(ch)-0x20) * 5
		f = open('/home/pi/python/lib/font5x7.fnt','rb')
		f.seek(fp)
		b = f.read(5)
		char_buf = bytearray(b)
		char_buf.extend([0])

		# make 8x6 image
		char_image = []
		for bit in range(8):
			for x in range (6):
				if ((char_buf[x]>>bit) & 1)>0:
					char_image.extend([self._color >> 8])
					char_image.extend([self._color & 0xff])
				else:
					char_image.extend([self._bground >> 8])
					char_image.extend([self._bground & 0xff])
		x = self._col*6+1
		y = self._row*8+1
		
		self.set_window(x,y,x+5,y+7)
		#self.data(char_image)
		for i in range(5):
			for j in range(7):
				self.LCD_WR_DATA(buff[i + j*5])		

		self._col += 1
		if (self._col>30):
			self._col = 0
			self._row += 1
			if (self._row>40):
				self._row = 0

	def p_string(self, str):
		"""Print a string at the location determined by row and char"""
		for ch in (str):
			self.p_char(ch)
				
	def p_image(self, x, y, img):
		img = img.convert('RGB')
		w, h = img.size
		z = img.getdata()
		img_buf = []
		for pixel in (z):
			r,g,b = pixel
			rgb = color565(r,g,b)
			img_buf.extend([rgb >> 8])
			img_buf.extend([rgb & 0xff])
			
		self.draw_bmp(x,y,w,h,img_buf)
		
	def text(self, text, align='left', angle=0):
		# make a new square image the size of the largest
		# dislay dimension to support rotated text
		limit = max(self.height,self.width)
		# img = Image.new('RGB', (limit, limit), color_rgb(self._bground))
		img = Image.new('RGBA', (limit, limit))
		# make the draw object
		draw = ImageDraw.Draw(img)
		# get the width and height of the text image
		width, height = draw.textsize(text, font=self._font)
		# draw the text into the image
		draw.text((0,0),text,font=self._font,fill=color_rgb(self._color))
		# crop the image to the size of the text
		img=img.crop((0,0,width,height))
		# rotate the image
		img = img.rotate(angle)
		# return the image object and the width and height
		return img, width, height
			
		
