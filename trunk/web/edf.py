"""
Project LifeLink: edf Module v1.0
Contains classes and methods used in encapsulating acquired raw biomedical signals
into European Data Format (EDF) - a standard used for the exchange and storage of
medical time-series recordings. It produces a .edf file which can be tested using
available edf viewer software.

Authors: Julius Miguel J. Broma
         Charles Hernan DC. Chiong
         Dan Simone M. Cornillez
         Arlan Roie A. Santos
         Luis G. Sison, PhD
         ------------------------------------------------
         Instrumentation, Robotics and Control Laboratory
         University of the Philippines - Diliman
         ------------------------------------------------
         January 2008
"""

class Patient:
    """contains information about the patient"""

    def __init__(self, ID = 0, firstname = 'First Name', middlename = 'Middle Name', \
                 lastname = 'Last Name', maidenname = 'Maiden Name', gender = 'Gender',\
                 birthday = '01.01.01', age = 0):
        # gender = 'Male' or 'Female'
        # birthday = mm.dd.yy
        
        self.ID = str(ID)
        self.FirstName = firstname
        self.MiddleName = middlename
        self.LastName = lastname
        self.MaidenName = maidenname
        self.Gender = gender
        self.Birthday = birthday
        self.Age = str(age)
        self.LocalPatientID = ''
 
        self.createLocalID()
        
    def createLocalID(self):
        """encodes the patient information to the LocalPatientID in the EDF header record field"""

        # ascii-character limit for every patient information (in bytes)
        lenID = 5
        lenFirstName = 20
        lenMiddleName = 12
        lenLastName = 12
        lenMaidenName  = 12
        lenGender = 6
        lenBirthday = 10
        lenAge = 3

        LocalPatientIDlist = [self.ID, self.FirstName, self.MiddleName, self.LastName, self.MaidenName, self.Gender, self.Birthday, self.Age]
        lenLocalPatientID = [lenID, lenFirstName, lenMiddleName, lenLastName, lenMaidenName, lenGender, lenBirthday, lenAge]
        
        for i in range(len(LocalPatientIDlist)):
            maxlen = lenLocalPatientID[i]
            if len(LocalPatientIDlist[i]) > maxlen:
                # truncates the string if length is greater than limit
                LocalPatientIDlist[i] = LocalPatientIDlist[i][:maxlen]      
            else:
                
                LocalPatientIDlist[i] = LocalPatientIDlist[i].ljust(maxlen)
                
        # converts the list to a string with no separator in between elements
        self.LocalPatientID = ''.join(LocalPatientIDlist)

    def get(self):
        """ returns the LocalPatientID attribute """

        return self.LocalPatientID
        
        
class BioSignal:
    """contains the biomedical signals of the patient as well as their technical information"""

    def __init__(self, Label = 'Label', TransducerType = '', PhyDimension = 'Dimension',\
                 PhyMin = -32767, PhyMax = 32767, DigMin = -32767, DigMax = 32767, Prefiltering = '',\
                 NRsamples = 1, RawBioSignal = []):
        # Label = Standard: 'TypeOfSignal Sensor'
        # DigMin > -32767
        # DigMax <  32767
        
        Reserved = ' '*32

        # fields defined in the EDF format
        self.Label = Label                           
        self.TransducerType = TransducerType
        self.PhyDimension = PhyDimension
        self.PhyMin = str(PhyMin)   
        self.PhyMax = str(PhyMax)
        self.DigMin = str(DigMin)                       
        self.DigMax = str(DigMax)                       
        self.Prefiltering = Prefiltering
        self.NRsamples = str(NRsamples)
        self.Reserved = Reserved
        
        self.TechInfo = []                     # list containing 256 bytes of characters describing the technical characteristics of each signal
        self.RawBioSignal = RawBioSignal                # the biomedical signal itself

        self.createTechInfo()
        
    def createTechInfo(self):
        """encodes the biomedical signal technical information to the EDF header record"""

        # ascii-character limit for every biosignal information (in bytes)
        lenLabel = 16
        lenTransducerType = 80
        lenPhyDimension = 8
        lenPhyMin = 8
        lenPhyMax = 8
        lenDigMin = 8
        lenDigMax = 8
        lenPrefiltering = 80
        lenNRsamples = 8
        lenReserved = 32

        self.TechInfo = [self.Label, self.TransducerType, self.PhyDimension, self.PhyMin, self.PhyMax, self.DigMin, self.DigMax, self.Prefiltering,\
                             self.NRsamples, self.Reserved]
        lenTechInfo = [lenLabel, lenTransducerType, lenPhyDimension, lenPhyMin, lenPhyMax, lenDigMin, lenDigMax, lenPrefiltering, lenNRsamples, lenReserved]

        for i in range(len(self.TechInfo)):
            maxlen = lenTechInfo[i]
            if len(self.TechInfo[i]) > maxlen:
                # truncates the string if length is greater than limit
                self.TechInfo[i] = self.TechInfo[i][:maxlen]      
            else:
                
                self.TechInfo[i] = self.TechInfo[i].ljust(maxlen)


class EDF:
    """manipulates the Patient and BioSignal objects to create an EDF file"""

    def __init__(self,  Patient, BioSignals, StartDate = '01.01.01', StartTime = '01.59.59', Location = '',\
                 nDataRecord = -1, DurationDataRecord = 1, ):
        # StartDate = dd.mm.yy
        # StartTime = hh.mm.ss
        
        Reserved = ' '*44

        # fields defined in the EDF format
        self.Version = '0'                                   # 0 is the only version number allowed
        self.LocalPatientID = Patient.get()  
        self.LocalRecordingID = 'Startdate ' + Location      # Location should contain a date (DD-MMM-YYYY) and the location of the patient
        self.StartDate = StartDate
        self.StartTime = StartTime
        self.nSignals = str(len(BioSignals))
        self.nBytesHeader = str(256 + 256*int(self.nSignals))
        self.EDFPlus = Reserved
        self.nDataRecord = str(nDataRecord)                  # if unknown, default value is -1 (prior or during recording)
        self.DurationDataRecord = str(DurationDataRecord)

        self.BioSignals = BioSignals
        self.HeaderRecord = ''                               # contains the header record information of the EDF data
        self.DataRecord = ''                                 # contains the 2-byte ASCII encided data record values of the BioSignals
        self.EDFFile = ''                                    # contains the EDF file of a patient and will be saved as .edf
        
 
        self.createHeaderRecord()
        self.createDataRecord()

        
    def createHeaderRecord(self):
        """creates the header record fields of the EDF file"""

        # ascii-character limit for every header record information (in bytes)
        lenVersion = 8
        lenLocalPatientID = 80
        lenLocalRecordingID = 80
        lenStartDate = 8
        lenStartTime = 8
        lennBytesHeader = 8
        lenEDFPlus = 44
        lennDataRecord = 8
        lenDurationDataRecord = 8
        lennSignals = 4
    
        HeaderInfolist = [self.Version, self.LocalPatientID, self.LocalRecordingID, self.StartDate, self.StartTime, self.nBytesHeader, self.EDFPlus,\
                          self.nDataRecord, self.DurationDataRecord, self.nSignals]
        lenHeaderInfo = [lenVersion, lenLocalPatientID, lenLocalRecordingID, lenStartDate, lenStartTime, lennBytesHeader, lenEDFPlus, lennDataRecord,\
                         lenDurationDataRecord, lennSignals]

        for i in range(len(HeaderInfolist)):
            maxlen = lenHeaderInfo[i]
            if len(HeaderInfolist[i]) > maxlen:
                # truncates the string if length is greater than limit
                HeaderInfolist[i] = HeaderInfolist[i][:maxlen]      
                
            else:
                HeaderInfolist[i] = HeaderInfolist[i].ljust(maxlen)
                
        # converts the list to a string with no separator in between elements
        self.HeaderRecord = ''.join(HeaderInfolist)                 

        # concatenates each BioSignal TechInfo to the Header Record string
        for i in range(len(self.BioSignals[0].TechInfo)):
            for x in range(len(self.BioSignals)):
                self.HeaderRecord = self.HeaderRecord + self.BioSignals[x].TechInfo[i]


    def createDataRecord(self):
        """creates the data record fields of the EDF file"""

        counter = 0
        DataRecordlist = []
        end = []
        offset = []
        start = []
        temp = []

        def DecToBin(num):
            # converts a decimal number to its 16-bit binary representation
            
            BinStr = ''
            if num == 0: return '0'*16
            while num > 0:
                BinStr = str(num % 2) + BinStr
                num = num >> 1                   # right-shift the num by 1 bit
            BinStr = BinStr.zfill(16)            # make BinStr a 16-bit string
            return BinStr

        for i in range(len(self.BioSignals)):
            offset.append(int(self.BioSignals[i].NRsamples))
            start.append(0)
            end.append(0)

        while (counter < int(self.nDataRecord)):
            
            for x in range(len(self.BioSignals)):

                end[x] = start[x] + offset[x]
                temp =  self.BioSignals[x].RawBioSignal[start[x]:end[x]]

                for i in range(len(temp)):
                    intRawValue = temp[i]

                    if intRawValue >= 0:
                        # if positive-valued, convert to binary
                        binRawValue = DecToBin(intRawValue)
                    else:
                        # if negative, get the positive representation by adding (2**16-1)
                        # these are the numbers from 32768-65535
                        negRawValue = intRawValue + (2**16-1)
                        # then convert to binary
                        binRawValue = DecToBin(negRawValue)

                    # divide the 16-bit binary number to two 8-bit binary numbers (MSByte and LSByte)
                    MSByte = binRawValue[:8]
                    LSByte = binRawValue[8:]

                    # convert each byte to decimal then get its ASCII representation 
                    chrMSByte = chr(int(MSByte,2))
                    chrLSByte = chr(int(LSByte,2))

                    # each value in the data record is a 2-byte 2's complement integer represented by its ASCII character
                    # it is arranged as: Value = LSB,MSB
                    DataRecordlist.extend([chrLSByte, chrMSByte])

                # update the pointer for the next set of data records
                start[x] = end[x]

            counter += 1

        # when all BioSignal objects are accessed and encoded, converts the list to a string
        self.DataRecord = ''.join(DataRecordlist)
            
    def get(self):

        self.EDFFile = self.HeaderRecord + self.DataRecord
        return self.EDFFile

class EDFSignal:
    """ extracts signal from an edf file

        This Method extracts a specified ECG signal from InputFile.
            Parameters:
                Lead -> a list of Lead II ECG Signal values
                InputFile -> edf file containing 12-lead ECG signals
                OutputFile -> File where the values are to be printed
                lead_type -> determines which ECG signal to be extracted (ex. "II")
                duration -> number of seconds to be extraced
                start -> determines where to start extracting data

            Duration should be in seconds and should not exceed the total duration
            the ECG signal. start should be an integer greater than zero but less
            than or equal to the total duration minus the desired duration to be
            extracted from the ECG signal.
    """
    def __init__(self, Input, Output='output.csv', lead_type='II', duration=None, start=None):
        """ set parameters and extract information from EDF File's Header File
            Default Parameters:
            Input -> required parameter
            Output - 'output.csv'
            lead_type - 'II'
            duration - whole data recording
            start - beginning of recording """
        self.InputFile = Input
        self.OutputFile = Output
        self.lead_type = lead_type
        if start == None:
            self.start = 0
        else:
            self.start = start
        self.duration = duration
        self.parse_headerfile()

    def parse_headerfile(self):
        """ extract important information contained in the headerfile of an edf file
            self.parse_headerfile() -> set self.HeaderSize, self.HeaderFile,self.rawDataRecord
                                        self.tempDataRecord, self.total_duration, self.signalnum """
        # Read and store the data contained in the input File
        myEDFFile = open(self.InputFile,'rb')
        EDFValues = myEDFFile.read()
        myEDFFile.close()

        # Extract the Header File that contains info about the record
        self.HeaderSize = int(EDFValues[184:192])
        self.HeaderFile = EDFValues[:self.HeaderSize]
        # Extract the actual data in the input file
        self.rawDataRecord = EDFValues[self.HeaderSize:]
        self.tempDataRecord = list(self.rawDataRecord)

        # Extract information from the EDF Header File
        self.total_duration = int(self.HeaderFile[236:244]) # total duration of the signal (in seconds)
        if self.duration == None:
            self.duration = self.total_duration
        self.signalnum = int(self.HeaderFile[252:256]) # number of signals in edf file

    def dec_to_bin(self,num):
        """ dec_to_bin(num) -> binary string of num

            dec_to_bin converts a number to its binary format and returns an
            eight-bit binary string.

            ex. dec_to_bin(10) -> '00001010' """
        BinStr = ''
        if num == 0: return '0'*8
        while num > 0:
            BinStr = str(num % 2) + BinStr
            num = num >> 1                  # right-shift the num by 1 bit
        BinStr = BinStr.zfill(8)            # make BinStr an 8-bit string
        return BinStr

    def extract_labels(self):
        """ extract_labels(HeaderFile,n) -> ECG Lead types, Lead Sampling Rates

            Extracts the 12 lead ECG labels as well as the sampling rate of
            each lead. Valid lead types are:
            I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6            
        """
        self.ECGlabel = {}
        self.ECGsampling = []
        for i in range(self.signalnum):
            label = self.HeaderFile[256+(16*i):272+(16*i)] # extract the lead type i's label
            self.ECGlabel[i] = label.strip()
            sampling = int(self.HeaderFile[2848+(8*i):2854+(8*i)])
            self.ECGsampling.append(sampling) # extract lead type i's sampling rate

    def extract_lead(self):
        """ Extracts a duration of data starting from 'start' from raw data.
            self.duration determines how many seconds will be extracted from
            the edf file. self.lead_type determines what information to be
            extacted. """
        self.lead = []
        for i in range(self.duration):
            self.lead[(i*1000):(i*1000)+1000] = self.tempDataRecord[((i+self.start)*2*self.fs*\
                            self.signalnum)+((self.index+1)*1000):((i+self.start)*2*self.fs*\
                                            self.signalnum)+((self.index+2)*1000)]

    def raw_to_binary(self):
        """ Converts the list of integer data to binary strings """
        count = 0;
        for i in self.lead:
            intvalue = ord(i)
            binvalue = self.dec_to_bin(intvalue)
            self.lead.remove(i)
            self.lead.insert(count,binvalue)
            count = count+1

    def binary_to_mV(self):
        """ Convert the list containing the binary string representation of data
            a list of data in mV. """
        self.DataRecord_Int = []
        for i in range(0,len(self.lead),2):
            LSByte = self.lead[i]
            MSByte = self.lead[i+1]
            int_2bytedata = int(MSByte + LSByte,2)
            if int_2bytedata <= 32767:
                self.DataRecord_Int.append(int_2bytedata)
            else:
                negative_num = int_2bytedata - (2**16-1)
                self.DataRecord_Int.append(negative_num)
        for i in range(len(self.DataRecord_Int)):
            self.DataRecord_Int[i] = self.DataRecord_Int[i]*0.00263

    def write_file(self):
        """ write_file() -> writes the contents of list Data to File

            ex. write_file() -> self.datarecord_int is written to self.outputfile """
        lead_file = open(self.OutputFile,'w')
        for item in self.DataRecord_Int:
            lead_file.write(str(item))
            lead_file.write(',\n')
        lead_file.close()

    def check_label(self):
        """ check_label() -> determine if lead is in tuple ECGlabel

            ex. self.check_label() -> 'True' if self.ECGlabel is a valid lead type """
        for count in self.ECGlabel:
            if self.ECGlabel[count] == self.lead_type:
                return True
        return False

    def get_EDF_parameters(self):
        """ Extracts the index and sampling rate of specified lead_type from ECGlabel """
        for count in self.ECGlabel:
            if self.ECGlabel[count] == self.lead_type:
                self.index = count
                self.fs = self.ECGsampling[count]

    def extract_ECG(self, writeToFile = False):
        """ extract_ECG(writeToFile = False) -> list of ECG data in mV

            ex. extract_ECG(True) -> returns a list of ECG data and
                                        writes to output file
                extract_ECG(False) -> returns a list of ECG data """

        # Determine the signal to be extracted by using the lead_type
        # provided before calling the function
        self.extract_labels() # extract signals from edf file
        self.get_EDF_parameters() # determine the signal and sampling rate

        # Check for possible errors in function call
        # 1. Determine the validity of lead type
        if not self.check_label():
            print "ERROR: ECG Label not found."
            return None
        # 2. Determine if the desired duration to be extracted
        #    is less than the total duration
        elif self.duration > self.total_duration:
            print "ERROR: Duration to be extracted is longer than the signal duration."
            return None
        # 3. Determine if the desired duration to be extracted
        #    is within the signal in the EDF file
        elif self.start > self.total_duration - self.duration:
            print "ERROR: start time will not accomodate specified duration"
            return None

        # Extract the desired portion of signal and store it to output file
        self.extract_lead() # Extract the desired duration of the signal
        self.raw_to_binary() # Convert data readings to 2 Byte, Binary Form
        self.binary_to_mV() # Convert the 2 Byte binary data to mV
        if writeToFile:
            self.write_file() # Write the extracted data to Output File
        return self.DataRecord_Int
