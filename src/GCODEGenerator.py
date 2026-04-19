from mido import MidiFile, MidiTrack, Message
import mido
import os

class GCODEGenerator:
    #Configs
    buildPlateWidth = 5
    buildPlateLength = 60
    SafetyMargin = 5
    baseOutput = []

    noteLow = 126
    noteHigh = 0

    ticks_per_beat = 0
    tempo = 0

    def NoteToX(self,noteVal):
        # return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        outmin = self.SafetyMargin
        outmax = self.buildPlateLength - self.SafetyMargin
        val = (((noteVal - self.noteLow) * (outmax - outmin)) / (self.noteHigh - self.noteLow)) + outmax
        return round(val,3)
    


    def __init__(self,trackPacket,tpb,tempo):
        self.baseOutput.append(f'G28 X Y\nG90\n')
        self.ticks_per_beat = tpb
        self.tempo = tempo

        for msgPacket in trackPacket:
            for msg in msgPacket:
                # print(str(msg))
                if(msg.type == 'note_off' or msg.type == 'note_on'):
                    noteVal = msg.note

                    if(noteVal > self.noteHigh):
                        self.noteHigh = noteVal

                    if(noteVal < self.noteLow):
                        self.noteLow = noteVal

        print(f'Track Range\nLow: {self.noteLow}\nHigh: {self.noteHigh}')



    def CreateGCode(self,trackPacket):
        prevMessage = None
        dwellTime = 0
        posX = 0
        posY = 0
        for msgPacket in trackPacket:
            for msg in msgPacket:
                if(prevMessage is None):
                    prevMessage = msg
                else:
                    dwellTime = msg.time
                    dwellTime = mido.tick2second(dwellTime,self.ticks_per_beat,self.tempo) * 1000
                    match prevMessage.type:
                        case 'note_on':
                            # print(f'{prevMessage.note} Note on for {dwellTime} ms')
                            posX = self.NoteToX(prevMessage.note)
                            posY = self.buildPlateWidth
                            gCommand = f'G0 X{posX} Y{posY}\nG4 P{int(dwellTime)}\nM400\n'
                            self.baseOutput.append(gCommand)
                        case 'note_off':
                            # print(f'{prevMessage.note} Note off for {dwellTime} ms')
                            posX = self.NoteToX(prevMessage.note)
                            posY = 0
                            gCommand = f'G0 X{posX} Y{posY}\nG4 P{int(dwellTime)}\nM400\n'
                            self.baseOutput.append(gCommand)
                        case _:
                            print("Other command")

                prevMessage = msg
        
        with open(f'{os.getcwd()}/MidiOut/Output.gcode','w') as f:
            for command in self.baseOutput:
                f.write(command)
            
            f.close()
        
