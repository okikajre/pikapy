import spidev
# Documentation for spidev can be accessed at https://pypi.org/project/spidev/

# The SPI module must be enabled on the Raspberry Pi
# sudo raspi-config
# Select 3 Interface Options
# Select I4 SPI
# Select Yes to enable SPI module
# Press enter for OK
# Arrow keys to select Finish and press enter
# Type sudo reboot to reboot the system and apply the settings

# TODO add I2C support for HAT ID EEPROM

import RPi.GPIO as GPIO
#import pigpio  # needed to enable GPCLK0 at GPIO4, must run "sudo pigpiod" before running this script if used
import time
#import keyboard  # Note using keyboard module since it requires root permissions
import sys

# GPIO Basic initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

FPAA_RESET_B = 26  # Output, drive high to enable FPAA
FPAA_CFGFLG_B = 23  # Input, configurtion status flag
FPAA_ACTIVATE = 24  # Input, pulled low by FPAA until configuration has been loaded
FPAA_ERR_B = 25  # Input, driven low if conifguration error detected
FPAA_ACLK_REF = 4  # Output (set up as GPCLK0 if used)...
FPAA_LCL_ACLK_EN = 14  # Output, enables oscillator on Pi.Ka board
FPAA_ACLK_SEL0 = 5  # Output, LSB of ACLK source selector
FPAA_ACLK_SEL1 = 6  # Output, MSB of ACLK source selector
FPAA_CE0 = 8  # Output, active low chip select common to all FPAAs
FPAA0_IO5P = 16  # Reserved
FPAA0_IO5N = 17  # Reserved
FPAA1_IO5P = 18  # Reserved
FPAA1_IO5N = 19  # Reserved
FPAA2_IO5P = 20  # Reserved
FPAA2_IO5N = 21  # Reserved
FPAA3_IO5P = 12  # Reserved
FPAA3_IO5N = 13  # Reserved

GPIO.setup(FPAA_RESET_B,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(FPAA_CFGFLG_B,GPIO.IN)
GPIO.setup(FPAA_ACTIVATE,GPIO.IN)
GPIO.setup(FPAA_ERR_B,GPIO.IN)
GPIO.setup(FPAA_CE0,GPIO.OUT,initial=GPIO.LOW)  # Constrol chip select separate from SPI
#pi1 = pigpio.pi()
GPIO.setup(FPAA_LCL_ACLK_EN,GPIO.OUT)
GPIO.setup(FPAA_ACLK_SEL0,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(FPAA_ACLK_SEL1,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(FPAA0_IO5P,GPIO.IN)
GPIO.setup(FPAA0_IO5N,GPIO.IN)
GPIO.setup(FPAA1_IO5P,GPIO.IN)
GPIO.setup(FPAA1_IO5N,GPIO.IN)
GPIO.setup(FPAA2_IO5P,GPIO.IN)
GPIO.setup(FPAA2_IO5N,GPIO.IN)
GPIO.setup(FPAA3_IO5P,GPIO.IN)
GPIO.setup(FPAA3_IO5N,GPIO.IN)

spi=spidev.SpiDev()
spi.open(0,0)
spi.mode=0b00
spi.no_cs=True  # Control CE0 as GPIO to prevent toggling between SPI transfers
spi.lsbfirst=False  # This is the default behavior, but set to make it certain
spi.bits_per_word=8
spi.max_speed_hz=32000000

GPIO.output(FPAA_RESET_B,0)  # Start with reset low to force reconfiguration without requiring power-cycle
#pi1.hardware_clock(FPAA_ACLK_REF,16000000)  # must run "sudo pigpiod" before this script if used
GPIO.output(FPAA_LCL_ACLK_EN,1)  # Enable 16MHz oscillator on Pi.Ka
GPIO.output(FPAA_ACLK_SEL0,0)  # Configure Pi.Ka to use the internal oscillator
GPIO.output(FPAA_ACLK_SEL1,0)  # Configure Pi.Ka to use the internal oscillator
GPIO.output(FPAA_CE0,0)  # Permanently drive chip select low per primary configuration timing diagram
# FPAA_ACLK_SEL[1:0] = 00 for local 16MHz oscillator
# FPAA_ACLK_SEL[1:0] = 01 for J11 reference clock from previous staked Pi.Ka
# FPAA_ACLK_SEL[1:0] = 10 for external reference ACLK source from TP1
# FPAA_ACLK_SEL[1:0] = 11 for Raspberry Pi GPIO4 (GPCLK0)
time.sleep(0.02)  # Hold reset low for 20ms
GPIO.output(FPAA_RESET_B,1)
time.sleep(0.1)  # Hold reset high for 100ms

# Send one byte of 0s and check ERR_B state
zero_list=[]
zero_list.append(0)
spi.xfer2(zero_list)  

if(GPIO.input(FPAA_ERR_B) == 0):
    print("ERR_B still low. Check connections and ACLK")

# waiting = False
# waitcount = 0
# if (GPIO.input(FPAA_ERR_B) == 0):
#     print("Waiting for ERR_B to go high")
#     waiting = True
# 
# while waiting:
#     if(GPIO.input(FPAA_ERR_B) == 1):
#         waiting = False
#     elif (waitcount < 100):
#         time.sleep(0.1)
#         waitcount += 1
#     else:
#         print("ERR_B not high after 10 seconds, exiting...")
#         waiting = False
# 
# if (waitcount < 100):
#     errbwait = waitcount*0.1
#     print("ERR_B detected high after ", errbwait, " seconds")

print("Press Enter to continue: ")
waiting = True
while waiting:
    sys.stdin.read(1)
    print("\nContinuing")
    waiting = False

DEBUG = True
def debug_print(printstring):
    if DEBUG:
        print(printstring)
        
ahf_file_name = "4osc.ahf"

primary_config_list=[]  # Create empty list for config bytes

f = open(ahf_file_name, "r")
lines = f.readlines()

for line in lines:
    line = line.replace("\n", "")  # Strip out newline character
    # Interpret each line as a hex integer (base 16) 
    primary_config_list.append(int(line, base=16))
    
debug_print("file read complete")

debug_print(primary_config_list)

spi.xfer2(primary_config_list)  # xfer2 holds chip select between bytes
# See /sys/module/spidev/parameters/bufsiz for maximum list size for xfer2 (default 4096)


# Simple command-line solution for holding the last state until the user decides to exit
print("Press Enter to exit: ")
running = True
while running:
    sys.stdin.read(1)
    print("\nExiting")
    running = False
    
# Clean up before exiting
spi.close()
GPIO.cleanup()