#!/usr/bin/python
# -*- coding: utf-8 -*-
# HD44780 LCD Script for Raspberry Pi
#
# Author : Kamil Porembinski
# Site	 : http://osworld.pl
#
# Based on Matt's Hawkins script
# Site	 : http://www.raspberrypi-spy.co.uk
# 
# Date	 : 23/08/2012

#import
import RPi.GPIO as GPIO
import time
import urllib2
import re

# Script options
settings = {
	# City to monitor (ex. "Lodz", "Warsaw, Cracow", ...)
	'city'					 : 'Lodz',
	# Language of the conditions (ex. en, pl, fr, ...)
	'language'			 : 'pl',
}
GOOGLE_WEATHER_URL = 'http://www.google.com/ig/api?weather=%s&hl=%s&oe=utf-8'

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25 
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18

# Define some device constants
LCD_WIDTH = 16 # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line 

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005
E_TIME	= 5

def lcd_init():
	# Initialise display
	lcd_byte(0x33,LCD_CMD)
	lcd_byte(0x32,LCD_CMD)
	lcd_byte(0x28,LCD_CMD)
	lcd_byte(0x0C,LCD_CMD)	
	lcd_byte(0x06,LCD_CMD)
	lcd_byte(0x01,LCD_CMD)	

def lcd_string(message):
	# Send string to display
	message = message.ljust(LCD_WIDTH,)	

	for i in range(LCD_WIDTH):
		lcd_byte(ord(message[i]),LCD_CHR)

def lcd_byte(bits, mode):
	# Send byte to data pins
	# bits = data
	# mode = True for character
	#		 False for command

	GPIO.output(LCD_RS, mode) # RS

	# High bits
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x10==0x10:
		GPIO.output(LCD_D4, True)
	if bits&0x20==0x20:
		GPIO.output(LCD_D5, True)
	if bits&0x40==0x40:
		GPIO.output(LCD_D6, True)
	if bits&0x80==0x80:
		GPIO.output(LCD_D7, True)

	# Toggle 'Enable' pin
	time.sleep(E_DELAY)		
	GPIO.output(LCD_E, True)	
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, False)	
	time.sleep(E_DELAY)			

	# Low bits
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x01==0x01:
		GPIO.output(LCD_D4, True)
	if bits&0x02==0x02:
		GPIO.output(LCD_D5, True)
	if bits&0x04==0x04:
		GPIO.output(LCD_D6, True)
	if bits&0x08==0x08:
		GPIO.output(LCD_D7, True)

	# Toggle 'Enable' pin
	time.sleep(E_DELAY)		
	GPIO.output(LCD_E, True)	
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, False)	
	time.sleep(E_DELAY)
	
def rmpl(text):
	pl_tab = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ż':'z', u'ź':'z',u'Ą':'A', u'Ć':'C', u'Ę':'E', u'Ł':'L', u'Ń':'N', u'Ó':'O', u'Ś':'S', u'Ż':'Z', u'Ź':'Z'}
	return ''.join( pl_tab.get(char, char) for char in text )
	
def convert_mph(match):
	try:
		mph = int(match.group(0).split(' ')[0])
		kph = mph*1.6
		return "%s kph" % (int(round(kph)),)
	except:
		return match.group(0)

def get_weather_for_city():
	from xml.dom.minidom import parseString
	from xml.etree import ElementTree as ET
	
	url = GOOGLE_WEATHER_URL % (settings["city"].replace(' ', '+'), settings["language"])
	
	try:
		source = urllib2.urlopen(url).read()
		source = source.decode('utf-8', 'ignore')
		source = source.encode('utf-8')
		
		etree = ET.fromstring(source)
		weather = etree.find('weather')
	except:
		return("There was an error while retrieving data from the server.")

	parts = []
	out = {}
	information = weather.find('forecast_information')
	
	city = rmpl(information.find('city').get('data'))
	out["city"] = city

	conditions = weather.find('current_conditions')

	temperature = rmpl(conditions.find('temp_c').get('data') + 'C')
	out["temperature"] = "Temperatura: " + temperature

	humidity = rmpl(conditions.find('humidity').get('data'))
	out["humidity"] = humidity

	wind = rmpl(conditions.find('wind_condition').get('data'))
	wind = re.sub('\d+ mph', convert_mph, wind)
	out["wind"] = wind

	condition = rmpl(conditions.find('condition').get('data'))
	out["condition"] = condition

	return out

def main():
	
	# Main program block
	GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers
	GPIO.setup(LCD_E, GPIO.OUT)	# E
	GPIO.setup(LCD_RS, GPIO.OUT) # RS
	GPIO.setup(LCD_D4, GPIO.OUT) # DB4
	GPIO.setup(LCD_D5, GPIO.OUT) # DB5
	GPIO.setup(LCD_D6, GPIO.OUT) # DB6
	GPIO.setup(LCD_D7, GPIO.OUT) # DB7

	# Initialise display
	lcd_init()
	while 1 == 1:
		out = get_weather_for_city()
		# Send some text
		lcd_byte(LCD_LINE_1, LCD_CMD)
		lcd_string(time.strftime('    %H:%M:%S    '))
		lcd_byte(LCD_LINE_2, LCD_CMD)
		lcd_string(time.strftime('   %d-%m-%Y  '))
		time.sleep(E_TIME)
		lcd_byte(LCD_LINE_1, LCD_CMD)
		lcd_string(out["city"])
		lcd_byte(LCD_LINE_2, LCD_CMD)
		lcd_string(out["temperature"])
		time.sleep(E_TIME)
		lcd_byte(LCD_LINE_1, LCD_CMD)
		lcd_string(out["humidity"])
		lcd_byte(LCD_LINE_2, LCD_CMD)
		lcd_string(out["condition"])
		time.sleep(E_TIME)		

if __name__ == '__main__':
	main()