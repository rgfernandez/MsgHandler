class BioSignal:
    """ contains the technical characteristics of a biosignal """
    
    def __init__(self):
        
        # Technical information fields specific for a signal (Header Record)
        self.Label          = ''                           
        self.TransducerType = ''
        self.PhyDimension   = ''
        self.PhyMin         = 0   
        self.PhyMax         = 0
        self.DigMin         = 0                       
        self.DigMax         = 0                       
        self.Prefiltering   = ''
        self.NRsamples      = 0
        self.Reserved       = ''

        self.TechInfolist = [self.Label, self.TransducerType, self.PhyDimension,\
                             self.PhyMin, self.PhyMax, self.DigMin, self.DigMax,\
                             self.Prefiltering, self.NRsamples, self.Reserved]
        
class EDF_File(BioSignal):
    """ manipulates an EDF file """

    def __init__(self, filename):
        """ opens the desired EDF file with the given filename and sets the attributes of the class """

        BioSignal.__init__(self)
        self.filename      = filename
        self.HeaderRecord  = ''
        self.TechnicalInfo = ''
        self.DataRecord    = ''
        self.BioSignals    = []

        # Header Record fields
        self.Version            = 0
        self.LocalPatientID     = ''
        self.LocalRecordingID   = ''
        self.StartDate          = ''
        self.StartTime          = ''
        self.nBytesHeader       = 0
        self.EDFPlus            = ''
        self.nDataRecord        = 0
        self.DurationDataRecord = 0
        self.nSignals           = 0
        
        # open the EDF file with the given filename
        try:
            self.file     = open(self.filename, 'rb')
            self.values   = self.file.read()
            self.file.close()
        except TypeError:
            self.values   = self.filename
        print self.filename, 'opened'

        self.getHeaderRecord()
        self.getTechnicalInfo()
        self.edf_signal = self.plotDataRecords()
        return self.getEdfSignal()
    
    def getEdfSignal(self):
        return self.edf_signal
        
    def getHeaderRecord(self):
        """ gets the Header Record part of the EDF file """

        self.nBytesHeader = int(self.values[184:192])
        self.HeaderRecord = self.values[:self.nBytesHeader]

        self.Version            = int(self.HeaderRecord[0:8])
        self.LocalPatientID     = self.HeaderRecord[8:88]
        self.LocalRecordingID   = self.HeaderRecord[88:168]
        self.StartDate          = self.HeaderRecord[168:176]
        self.StartTime          = self.HeaderRecord[176:184]
        self.EDFPlus            = self.HeaderRecord[192:236]
        self.nDataRecord        = int(self.HeaderRecord[236:244])
        self.DurationDataRecord = float(self.HeaderRecord[244:252])
        self.nSignals           = int(self.HeaderRecord[252:256])
        
        print 'Version              :', self.Version
        print 'Local Patient ID     :', self.LocalPatientID
        print 'Local Recording ID   :', self.LocalRecordingID
        print 'Start Date           :', self.StartDate
        print 'Start Time           :', self.StartTime
        print 'N Header Record      :', self.nBytesHeader
        print 'EDF Plus             :', self.EDFPlus
        print 'N Data Record        :', self.nDataRecord
        print 'Duration Data Record :', self.DurationDataRecord
        print 'N Signals            :', self.nSignals

    def getTechnicalInfo(self):
        """ gets the technical information of each signals """

        self.TechnicalInfo = self.values[256:self.nBytesHeader]
        self.TechInfotext  = ['Signal Label       :',\
                              'Transducer Type    :',\
                              'Physical Dimension :',\
                              'Physical Minimum   :',\
                              'Physical Maximum   :',\
                              'Digital Minimum    :',\
                              'Digital Maximum    :',\
                              'PreFiltering       :',\
                              'Number of Samples  :',\
                              'Reserved           :']    
        Lengthlist = [16, 80, 8, 8, 8, 8, 8, 80, 8, 32]
        Fieldstart = 0
        
        # create a BioSignal object for every biomedical signal
        for i in range(self.nSignals):
            self.BioSignals.append(BioSignal())

        for i in range(len(Lengthlist)):
            FieldLength = self.nSignals * Lengthlist[i]
            Fieldend = Fieldstart + FieldLength
            persignalfield = self.TechnicalInfo[Fieldstart:Fieldend]
            persignalstart = 0
            
            for x in range(len(self.BioSignals)):
                persignalend = persignalstart + Lengthlist[i]
                self.BioSignals[x].TechInfolist[i] = persignalfield[persignalstart:persignalend]
                persignalstart = persignalend

            Fieldstart = Fieldend

        for x in range(len(self.BioSignals)):
            print '-'*100
            for i in range(len(self.TechInfotext)):
                print self.TechInfotext[i] + self.BioSignals[x].TechInfolist[i]

    def plotDataRecords(self):
        """ plots each signal in the data record """
        
        self.DataRecord = self.values[self.nBytesHeader:]
        tempDataRecord = list(self.DataRecord)

        def DecToBin(num):
            BinStr = ''
            if num == 0: return '0'*8
            while num > 0:
                BinStr = str(num % 2) + BinStr
                num = num >> 1
            BinStr = BinStr.zfill(8)
            return BinStr

        for i in range(len(self.DataRecord)):
            intvalue = ord(tempDataRecord[i])
            binvalue = DecToBin(intvalue)
            tempDataRecord.remove(tempDataRecord[i])
            tempDataRecord.insert(i,binvalue)

        DataRecord_int = []

        for i in range(0,len(tempDataRecord),2):
            LSByte = tempDataRecord[i]
            MSByte = tempDataRecord[i+1]
            int_2bytedata = int(MSByte + LSByte,2)

            if int_2bytedata <= 32767:
                DataRecord_int.append(int_2bytedata)

            else:
                negative_num = int_2bytedata - (2**16-1)
                DataRecord_int.append(negative_num)

        return DataRecord_int