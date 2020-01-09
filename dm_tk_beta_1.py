
from copy import copy, deepcopy
from tkinter import *
import tkinter.scrolledtext as scrolledtext
from tkinter import filedialog
from midiutil import MIDIFile
from random import randrange, random
import string
import sys
from io import StringIO, BytesIO
import math
import pygame.mixer

# pygame audio context
pygame.mixer.init()

# instrument definitions
Snare    = [40]
BassDrum = [36]
HiHat    = [42]
HiHatp   = [44]
HiHath   = [46]
Tomlow   = 45 # use Toms below
Tomlmid  = 47
Tomhmid  = 48
Tomhigh  = 50
Ride     = [51]
Crash    = [49]
Chinese  = [52]
RideBell = [53]
Splash   = [55]
Crash2   = [57]
Ride2    = [59]

# relevant arrays
Toms          = [Tomlow, Tomlmid, Tomhmid, Tomhigh]
Cymbals       = [51, 49, 52, 53, 55, 57, 59]
# beats
beats         = [1, 1/2, 1/3, 1/4, 1/8, 1/9]
cymbbeats     = [1, 1/2, 1/3]
Tomslim       = [1, 1/2, 1/3, 1/4, 1/8]
snarelimit    = [1, 1/2, 1/3, 1/4]

# random filename
def ranfn():
    strn = string.ascii_letters + string.digits
    return "".join([ strn[randrange(0, len(strn))] for x in range(12)])

# random beat makers
def ranbeat():
    return beats[randrange(0, len(beats))]
def snarebeat():
    return snarelimit[randrange(0, len(snarelimit))]
def tombeat():
    return Tomslim[randrange(0, len(Tomslim))]
def cymbeat():
    return cymbbeats[randrange(0, len(cymbbeats))]

# random cymbal
def randomcymbal():
    if randrange(0,8) == 1:
        return Cymbals
    return [Cymbals[randrange(0, len(Cymbals))]] # [] because is passed to as instr (expects array)

# probability of hit
def hitprob():
    return randrange(0,64) + 1
# pulse through this bar if true:
def pulseit(n):
    return randrange(0,n) + 1

#drum layer 
class DrumCutLayer:
    def __init__(self, beat, track):
        # array holding what was hit
        self.whathit         = []
        # array holding beat of hits
        self.beat            = beat
        # track operating on
        self.track           = track
        # array holding information to help with
        # math to make sure beats are in right place
        self.ntimesbeat      = []
        # volume of hits
        self.volumes         = []
        
# a complete cut is composed of
# drum layers which play concurrently
class CompleteCut:
    def __init__(self):
        self.bassdrumlayer   = None 
        self.snaredrumlayer  = None
        self.tomsdrumlayer   = None
        self.cymbaldrumlayer = None

# main DrumMachine class of Full Metal Drum Kit
class DrumMachine:
    # set global tempo will effect everything - no
    # tempo changes between cuts just one global tempo
    tempo     = 0
    # holds the cuts which are to be rendered to the midi file
    allcuts   = []
    # the print-out version of the cut ids so the user knows which beat is which number
    cutids    = []
    # holds unique cuts for use with the buildFromArray method
    unique    = []
    # holds unique id for each item of array above
    uniqueid  = []
    # counter for number of allcuts - starts at 1 not 0
    globalid  = 1
    # is incremented everytime a unique pattern is pushed and therefore saved in unique
    cutid     = 1
    # If a new unique cut is made store it in unique and then set newcut to False
    # starts at True because first cut is always unique
    newcut    = True
    # temp for patterns being edited
    edpad     = None
    # id for pattern being editing
    editing   = None
    # when editing drum layers
    # we can overwrite or add to the layers (discontinued)
    overwrite = True
    # push copy
    pushc     = False
    # can copy
    cancopy   = False
    
    def __init__(self):
        self.tempo = 120 # default
        self.tempcut = None
        # Create a Midi file
    def createMidi(self):
        self.midif = MIDIFile(3)
        self.midif.addTempo(0,0, self.tempo)
        # make it so midi file is in memory so it can play without having to save to disk
    def createMem(self):
        self.memFile = BytesIO()
        # Write the Midi file to memory
        # and load it into pygame so it can be played
    def writeMidiMem(self):
        self.midif.writeFile(self.memFile)
        self.memFile.seek(0)
        pygame.mixer.music.load(self.memFile)
        # free memory and close files
    def freeMidiMem(self):
##        pygame.mixer.music.unload()
        self.memFile.close()
        self.midif.close()
        # create a drum layer of a given type
    def drumLayer(self, instr, beat, track, prob, pulse = 0, barsin = 0):
        bars = 4
        if self.overwrite == True or self.edpad == None:
            drumcut = DrumCutLayer(beat, track)
        else:
            if instr == Snare and self.edpad.snaredrumlayer != None:
                drumcut = self.edpad.snaredrumlayer
            else:
                drumcut = DrumCutLayer(beat, track)    
            if instr == BassDrum and self.edpad.bassdrumlayer != None:
                drumcut = self.edpad.bassdrumlayer
            else:
                drumcut = DrumCutLayer(beat, track)    
            if instr == Toms and self.edpad.tomsdrumlayer != None:
                drumcut = self.edpad.tomsdrumlayer
            else:
                drumcut = DrumCutLayer(beat, track)    
            if instr != Snare and instr != BassDrum and instr != Toms:
                if self.edpad.cymbaldrumlayer != None:
                    drumcut = self.edpad.cymbaldrumlayer
                else:
                    drumcut = DrumCutLayer(beat, track)
        c = b = 0
        n = 1
        mod4hit = 3
        dec4hit = [1, 0.50, 0.25][randrange(0, 3)]
        addtovol = 0
        if instr == Snare:
            addtovol = 20
        elif instr == BassDrum:
            addtovol = 17
        while b < bars:
            hitit = randrange(0, prob) + 1
            if (pulse != 0 and n % pulse == 0) or (prob > 0 and hitit == 1):
                volu = randrange(100 + addtovol, 128)
                drumcut.ntimesbeat  += [n * beat]
                drumcut.volumes     += [volu]
                drumcut.whathit     += [instr[randrange(0, len(instr))]]
            c += beat
            if c >= 1:
                c = 0
                b += 1
            n += 1
        return drumcut
    # a CompleteCut is made by layering -- calling drumLayer()
    def drumCut(self):
        cc = CompleteCut()
        cc.bassdrumlayer = self.drumLayer(BassDrum, ranbeat(),
        0, hitprob(),pulseit(6), 1)

        cc.snaredrumlayer = self.drumLayer(Snare,snarebeat(),
        1, hitprob(), pulseit(17)-1, 1)

        if randrange(0,2) == 1:
            cc.tomsdrumlayer = self.drumLayer(Toms, tombeat(),
            1, hitprob(), pulseit(7)-1, 1)
        for pc in range(8):
            if randrange(0,8) == 1:
                cc.cymbaldrumlayer = self.drumLayer(randomcymbal(), cymbeat(),
                2, hitprob(), pulseit(7)-1, 1)
        self.tempcut = cc
    # call after creating midi context
    def CreateDrumLayer(self, drumclayer, offset):
        if drumclayer == None:
            return
        for hit in range(len(drumclayer.whathit)):    
            self.midif.addNote(drumclayer.track,
            9, drumclayer.whathit[hit],
            drumclayer.ntimesbeat[hit] + (offset * 4),
            1, drumclayer.volumes[hit])
        # create midi and memory for it
    def createMidiContext(self):
        self.createMidi()
        self.createMem()
        # put midi data into midi file
    def makeDemo(self, offset = 0):
        ccobj = self.tempcut
        self.CreateDrumLayer(ccobj.bassdrumlayer,   offset)
        self.CreateDrumLayer(ccobj.snaredrumlayer,  offset)
        self.CreateDrumLayer(ccobj.tomsdrumlayer,   offset)
        self.CreateDrumLayer(ccobj.cymbaldrumlayer, offset)
        # calls above function but for consecutive drum patterns
    def buildAllCuts(self):
        if len(self.allcuts) < 1:
            return 
        for n, cut in enumerate(self.allcuts):
            self.tempcut = cut
            self.makeDemo((n))
    def playDemo(self):
        pygame.mixer.music.play()
        # stores cut and relevant variables in arrays for later use
    def storeCut(self):
        if self.pushc == True and self.cancopy == True:
            if self.cutid <= len(self.unique):
                self.cutid  += 1
        self.allcuts      += [self.tempcut]
        self.cutids       += [self.cutid]
        self.globalid     += 1
        if self.newcut == True or (self.pushc == True and self.cancopy):
            self.unique   += [deepcopy(self.tempcut)]
            self.uniqueid += [self.cutid]
        self.pushc         = False
        self.newcut        = False
        if self.pushc == True and self.cancopy == True:
            self.newcut = True
        # deletes last added pattern
    def killCut(self):
        if self.globalid > 0:   
            self.globalid -= 1
            del self.allcuts[self.globalid-1]
            del self.cutids[self.globalid-1]
        # saves pattern to disk
    def save(self):
        if (self.allcuts == []):
            return -1
        self.buildAllCuts()
        self.writeMidiMem()
##        try:
        outp = filedialog.asksaveasfile(initialdir="/", mode="wb", defaultextension=".mid")
        if outp is None:
            return -1
        self.midif.writeFile(outp)
##        except:
##            return -1
        return ""
        # format pattern string for output
    def formatfp(self):
        return "".join([str(x)+',' for x in self.cutids])[:-1]
        # print-out for GUI for how many patterns can be used
    def ntoUse(self):
        if len(self.unique) < 1:
            return "0-0"
        else:
            return f"1-{len(self.unique)}"
        # build pattern from array entered by user
    def buildFromArray(self, temp):
        if len(self.unique) < 1:
            return -1
        try:
            temp = [int(x) for x in temp.split(',')]
        except:
            return -1
        for i in temp:
            if i not in self.uniqueid:
                return -1
        self.allcuts = []
        self.cutids  = []
        for c in temp:
            self.allcuts += [self.unique[c-1]]
            self.cutids  += [self.uniqueid[c-1]]
        self.globalid     = len(self.allcuts)
        self.buildAllCuts()
        return 1
    # load a pattern to be edited in the pattern editor
    def loadForEdit(self, pat):
        pat = abs(int(pat))
        if len(self.unique) < 1:
            return -1
        while (pat not in self.uniqueid):
            pat -= 1
        self.edpad = self.unique[pat-1]
        self.editing = pat
        return 1
    def editPattern(self, what):
        if what == "":
            return
        if what == "bass":
            if self.overwrite == True:
                self.edpad.bassdrumlayer   = None
            self.edpad.bassdrumlayer   = self.drumLayer(BassDrum, ranbeat(),
                                                 0, hitprob(),pulseit(4), 1)
        elif what == "snare":
            if self.overwrite == True:
                self.edpad.snaredrumlayer  = None
            self.edpad.snaredrumlayer  = self.drumLayer(Snare,snarebeat(),
                                           1, hitprob(), pulseit(3)-1, 1)
        elif what == "toms":
            if self.overwrite == True:
                self.edpad.tomsdrumlayer   = None
            if randrange(0,4) != 0:
                self.edpad.tomsdrumlayer = self.drumLayer(Toms, tombeat(),
                1, hitprob(), pulseit(7)-1, 1)
        elif what == "cym":
            if self.overwrite == True:
                self.edpad.cymbaldrumlayer = None
            for pc in range(8):
                if randrange(0,5) == 1:
                    self.edpad.cymbaldrumlayer = self.drumLayer(randomcymbal(), cymbeat(),
                    2, hitprob(), pulseit(3)-1, 1)
    def updatePattern(self):
        self.unique[self.editing-1]
        self.tempcut = self.unique[self.editing-1]
drummachine = DrumMachine()

global canreplay
canreplay = 0
##print(drummachine.formatfp())
##print(drummachine.ntoUse())
def nextp():
    global canreplay
    if canreplay:
        pygame.mixer.music.stop()
        drummachine.freeMidiMem()
        canreplay = 0

    if (drummachine.newcut == False):
        drummachine.cutid  += 1
        drummachine.newcut = True
    drummachine.drumCut()
    drummachine.createMidiContext()
    drummachine.makeDemo()
    drummachine.writeMidiMem()
    drummachine.playDemo()
    canreplay = 1
    drummachine.cancopy = False
def load4edit(pat):
    global canreplay
    if (len(drummachine.unique) > 0):
        suc = drummachine.loadForEdit(pat)
def edit(what, pat):
    load4edit(pat)
    global canreplay
    if canreplay:
        pygame.mixer.music.stop()
        drummachine.freeMidiMem()
        canreplay = 0
    drummachine.editPattern(what)
    drummachine.updatePattern()
    drummachine.createMidiContext()
    drummachine.makeDemo()
    drummachine.writeMidiMem()
    drummachine.playDemo()
    canreplay = 1
    drummachine.cancopy = True
def buildfromarray(temp):
    global canreplay
    if canreplay:
        pygame.mixer.music.stop()
        drummachine.freeMidiMem()
        canreplay = 0
    drummachine.createMidiContext()
    suc = drummachine.buildFromArray(temp)
    if suc:
        drummachine.writeMidiMem()
        drummachine.playDemo()
        canreplay = 1
    else:
        drummachine.freeMidiMem()
    drummachine.cancopy = False
def delete():
    if (len(drummachine.cutids) > 0):
        drummachine.killCut()
        putids()
        drummachine.cancopy = False
def replay():
    global canreplay
    if (canreplay):
        drummachine.playDemo()
        
def push():
    global canreplay
    if canreplay and drummachine.tempcut != None:
        drummachine.storeCut()
        putids()
        updaterang()

def pushcopy():
    if len(drummachine.unique) > 0 and drummachine.cancopy == True:
        drummachine.pushc = True
        push()
        drummachine.cancopy = False
    
def build():
    updaterang()
    global canreplay
    if canreplay:
        pygame.mixer.music.stop()
        drummachine.freeMidiMem()
        canreplay = 0
    if (len(drummachine.allcuts) >= 0):
        drummachine.createMidiContext()
        drummachine.buildAllCuts()
        drummachine.writeMidiMem()
        drummachine.playDemo()
        canreplay = 1
def savem():
    global canreplay
    if canreplay:
        drummachine.freeMidiMem()
        drummachine.createMidiContext()
        canreplay = 1
    drummachine.save()

tkmaster = Tk(className="Full Metal Drum Kit")
tkmaster.iconbitmap(default="fmdkd.ico")
tkmaster.geometry("640x262")
tkmaster["bg"] = "#2c2e2c"
tkmaster.resizable(0,0)

rangtxt = StringVar()
rangtxt.set(drummachine.ntoUse())
rang = Label(tkmaster, bg="#2c2e2c", fg="#FFFFFF", textvariable=rangtxt)
rang.place(x=610, y=160)

def updaterang():
    rangtxt.set(drummachine.ntoUse())

##def getoverw():
##    if overwrite.get() == 1:
##        drummachine.overwrite = True
##    elif overwrite.get() == 0:
##        drummachine.overwrite = False
##    print(overwrite.get())
##
##overwrite = IntVar()
##overwrite.set(1)
##
##overw = Checkbutton(tkmaster,bg="#2c2e2c", fg="#FF00FF", text="Overwrite", variable=overwrite, command=getoverw)
##overw.place(x=525, y=160)

dpatbut = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Randomize", command=nextp)
dpatbut.place(x=0,y=0)

dpatbutb = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Play Again", command=replay)
dpatbutb.place(x=0,y=30)

dpatbutb = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Push Copy", command=pushcopy)
dpatbutb.place(x=0,y=60)

dpatbutc = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Push", command=push)
dpatbutc.place(x=0,y=90)

##dpatbutd = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Del", command=delete)
##dpatbutd.place(x=0,y=90)

textbox = scrolledtext.ScrolledText(tkmaster, bg="#202020", fg="#FFFFFF")
textbox.config(insertbackground="#FFFFFF")
textbox.place(x=90, y=0, width=425, height=262)

def putids():
    textbox.delete(1.0, END)
    textbox.insert(1.0, drummachine.formatfp())
def showfn(fn):
    if fn != -1:
        textbox.delete(1.0, END)
        textbox.insert(1.0, fn)

def gettext():
    patdat = textbox.get("1.0", END)
    return "".join([x for x in patdat if x in "1234567890,"])

def dobuild():
    buildfromarray(gettext())


dpatbute = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", text="Demo", width=11, command=dobuild)
dpatbute.place(x=0,y=120)

rbutr = Button(tkmaster, bg="#2c2e2c",fg="#FFFFFF", text="Refresh", width=11, command=putids)
rbutr.place(x=0, y=150)

dpatbutf = Button(tkmaster,bg="#2c2e2c", fg="#FFFFFF", width=11, text="Save", command=savem)
dpatbutf.place(x=0,y=180)

templab = Label(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Tempo")
templab.place(x=0, y=240)

tempoent = Entry(tkmaster, width=5)
tempoent.insert(0, "120")
tempoent.place(x=52, y=240)


def gettempo():
    try:
        tempo = int(tempoent.get())
    except:
        return
    else:
        if tempo != 0 and tempo > 0:
            drummachine.tempo = tempo
        
gett = Button(tkmaster, width=11, bg="#2c2e2c", fg="#FFFFFF", text="Set Tempo", command=gettempo)
gett.place(x=0, y=210)

edt = Label(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Edit Pattern")
edt.place(x=522, y=0)

editpat = Spinbox(tkmaster, width=5, from_=0, to_=1000000)
editpat.place(x=595, y=0)

def isvalpat():
    if len(drummachine.unique) < 1:
        return -1
    p = int(editpat.get())
    if p > len(drummachine.unique):
        return -1
    if p > 0:
        return p
    return -1
def bass4edit():
    p = isvalpat()
    if p != -1:
        edit("bass", p)
def snare4edit():
    p = isvalpat()
    if p != -1:
        edit("snare", editpat.get())
def tomsedit():
    p = isvalpat()
    if p != -1:
        edit("toms", editpat.get())
def cym4edit():
    p = isvalpat()
    if p != -1:
        edit("cym", editpat.get())

def load4copy():
    p = isvalpat()
    if p != -1:
        edit("", editpat.get())

bss = Button(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Bass", width=14, command=bass4edit)
bss.place(x=531, y= 25)

snre = Button(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Snare", width=14, command=snare4edit)
snre.place(x=531, y= 50)

tms = Button(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Toms", width=14, command=tomsedit)
tms.place(x=531, y= 75)

cymsk = Button(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Cymbals", width=14, command=cym4edit)
cymsk.place(x=531, y= 100)

cymsk1 = Button(tkmaster, bg="#2c2e2c", fg="#FFFFFF", text="Play / Copy Enable", width=14, command=load4copy)
cymsk1.place(x=531, y= 125)

# the one and only...
mainloop()




