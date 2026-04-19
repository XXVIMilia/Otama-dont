from mido import MidiFile, MidiTrack, Message
import mido
import glob, os
import GCODEGenerator

class OtamatoneCtrl:

    midi_loaded = "None"
    midi_track_selected = 0
    midis = []
    midiData = ''
    status = f'Midi Loaded: {midi_loaded}\nMidi Track: {midi_track_selected}'

    PreProcessedTrackQueue = []
    PostProcessedTrackQueue = []

    def ProcessTrackQueue(self):
        if(len(self.PreProcessedTrackQueue)):
            TempTrackQueue = []
            #note_on processing
            for msgPacket in self.PreProcessedTrackQueue:
                if(str(msgPacket).find('note_on') >= 0):
                    highestNote = 0
                    timeCode = 0
                    tempOnMsg = None
                    for msg in msgPacket:
                        if(msg.time > 0):
                            timeCode = msg.time
                        if(msg.note > highestNote):
                            tempOnMsg = msg
                            if(timeCode):
                                tempOnMsg.time = timeCode
                            highestNote = msg.note
                    TempTrackQueue.append([tempOnMsg])
                else:
                    TempTrackQueue.append(msgPacket)

            #note_off processing
            TempTrackQueue2 = []
            on_note = 0
            for msgPacket in TempTrackQueue:
                if(str(msgPacket).find('note_on') >= 0):
                    on_note = msgPacket[0].note
                    TempTrackQueue2.append(msgPacket)
                elif(str(msgPacket).find('note_off') >= 0):
                    # offCount = 0
                    for msg in msgPacket:
                        if(msg.note == on_note):
                            TempTrackQueue2.append([msg])
                            # if(offCount):
                            #     print(f'Error, Dupe Off Detected: {on_note}')
                            # offCount+=1
                else:
                    TempTrackQueue2.append(msgPacket)
            

            self.PostProcessedTrackQueue = []
            for item in TempTrackQueue2:
                self.PostProcessedTrackQueue.append(item)
                    

    def UpdateStatus(self):
        self.status = f'Midi Loaded: {self.midi_loaded}\nMidi Track: {self.midi_track_selected}'

    def ListAllMidi(self):
        print("Listing")
        self.midis = glob.glob("MidiIn/*")
        count = 0
        for midi in self.midis:
            out = f'[{count}] {midi}'
            print(out)
            count+=1

    def LoadMidi(self,idx):
        print("loading")
        self.midi_loaded = self.midis[idx]
        print(self.midi_loaded)
        self.midiData = MidiFile(os.getcwd() + '/' + self.midi_loaded)
        self.midiData.print_tracks(True)


    def SetTrack(self, idx):
        print("Setting Track")
        self.midi_track_selected = idx

    def TrackToMidi(self):
        mid = MidiFile()
        track = MidiTrack()

        mid.tracks.append(track)

        count = 0
        for msg in self.PostProcessedTrackQueue:
            track.append(msg[0])
            count+=1

        print(f'Wrote {count} messages to new midi')

        mid.save("MidiOut/SelectedTrack.mid")
        


    def GetMidiInfo(self):
        print("Retireved Info")

        
        for idx, track in enumerate(self.midiData.tracks):
            output_file_name = self.midi_loaded
            output_file_name = output_file_name.replace("MidiIn","")
            self.PreProcessedTrackQueue = []

            currentTempo = 500000

            if(idx == self.midi_track_selected):
                with open(f'{os.getcwd()}/MidiOut/TrackEventLog.txt','w') as f:
                    f.write(track.name)
                    f.write('\n')

                    

                    MsgQueue = []
                    QueueType = ''
                    for msg in track:
                        match msg.type:
                            case 'note_on':
                                if(QueueType == 'note_on'):
                                    if(msg.time == 0):
                                        MsgQueue.append(msg)
                                    else:
                                        # f.write(str(MsgQueue))
                                        # f.write('\n')
                                        self.PreProcessedTrackQueue.append(MsgQueue)
                                        MsgQueue = []
                                        MsgQueue.append(msg)
                                else:
                                    if(len(MsgQueue)):
                                        # f.write(str(MsgQueue))
                                        # f.write('\n')
                                        self.PreProcessedTrackQueue.append(MsgQueue)
                                        MsgQueue = []
                                    MsgQueue.append(msg)
                                    QueueType = 'note_on'
                            case 'note_off':
                                if(QueueType == 'note_off'):
                                    if(msg.time == 0):
                                        MsgQueue.append(msg)
                                    else:
                                        # f.write(str(MsgQueue))
                                        # f.write('\n')
                                        self.PreProcessedTrackQueue.append(MsgQueue)
                                        MsgQueue = []
                                        MsgQueue.append(msg)
                                else:
                                    if(len(MsgQueue)):
                                        # f.write(str(MsgQueue))
                                        # f.write('\n')
                                        self.PreProcessedTrackQueue.append(MsgQueue)
                                        MsgQueue = []
                                    MsgQueue.append(msg)
                                    QueueType = 'note_off'
                            case 'set_tempo':
                                currentTempo = msg.tempo
                            case _:
                                if(len(MsgQueue)):
                                    # f.write(str(MsgQueue))
                                    # f.write('\n')
                                    self.PreProcessedTrackQueue.append(MsgQueue)
                                    MsgQueue = []
                                # f.write(str(msg))
                                # f.write('\n')
                                tempList = []
                                tempList.append(msg)
                                self.PreProcessedTrackQueue.append(tempList)
                                QueueType = '_'

                    self.ProcessTrackQueue()

                    if(idx == self.midi_track_selected):
                        self.TrackToMidi()
                        gcodeGen = GCODEGenerator.GCODEGenerator(self.PostProcessedTrackQueue,self.midiData.ticks_per_beat,currentTempo)
                        gcodeGen.CreateGCode(self.PostProcessedTrackQueue)

                    for q in self.PostProcessedTrackQueue:
                        f.write(str(q))
                        f.write('\n')

                    f.close()


    def ParseCommand(self,val):
        match val:
            case "quit":
                return(0)
            case 'load':
                self.ListAllMidi()
                i = input("Choose Index: ")
                i = i.replace('\n','')
                if(i.isdigit()):
                    self.LoadMidi(int(i))
                else:
                    self.LoadMidi(0)
            case 'set':
                if(self.midi_loaded != 'None'):
                    i = input("Choose Index: ")
                    if(i.isdigit()):
                        self.SetTrack(int(i))
                else:
                    print("No Midi Loaded!")
            case 'status':
                print(self.status)
            case 'info':
                self.GetMidiInfo()
            case _:
                print("Unknown Command")

        self.UpdateStatus()

        return(1)

        


if __name__ == "__main__":
    session = 1
    myOtamatone = OtamatoneCtrl()
    print("HackKU Midi Parser V0.1!")
    try:
        while session:
            command = input("Actions: 'load': Load Midi, 'set': Set midi track, 'status': print current status, 'info': Get Midi info, 'quit': exit application\n")
            session = myOtamatone.ParseCommand(command)
    except KeyboardInterrupt:
        print("Exiting via keyboard interrupt")