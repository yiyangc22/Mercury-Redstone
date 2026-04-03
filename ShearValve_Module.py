# -*- coding: utf-8 -*-
"""
Shear valve pump switching function for LabVIEW

First created on Mon Aug 19 14:11:51 2019
Based on work of R.Tushar
"""
import serial
import sys
import time
# from BBSValve_Log_Generator import BB_Formatted_Log

class shear_valve:
    def __init__(self,ValveCommPort):
        try:            
            # define communication port settings
            baudrate = 19200
            bytesize = serial.EIGHTBITS
            parity = serial.PARITY_NONE
            stopbits = serial.STOPBITS_ONE
            timeout = 0.9375
            xonxoff = 0
            rtscts = 0
            dsrdtr = None
            write_timeout = None
            inter_byte_timeout = None
            exclusive = None                
            self.CommPort = serial.Serial(ValveCommPort, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts, dsrdtr, write_timeout, inter_byte_timeout, exclusive)                                
            
            self.number_of_valve_ports=24
            self.Max_movement_duration=5 #secs 

            self.Max_response_databytes=10
            self.valve_status_check_delay=0.1 # secs sleep between consecutive valve status checks
            self.min_valve_response_time=0.005 # Pumps responds to a command within 5 msec according to the manual

            self.additional_log=None                        

        except:
            self.logevent(str(sys.exc_info()[1]),'ERROR') 
            
        
    def move_to_position(self,port_number,move_direction):
        try:
            cmd_status=False # Flag to return indicating success of requested operation
            # Check if port number exists in the list of available ports!
            if port_number<1 or port_number>self.number_of_valve_ports:
                self.logevent('Port number: ' + str(port_number) + ' is not available on this shear valve','ERROR')
                return cmd_status

            # Make sure the valve is ready to take commands before sending the next command
            valve_ready=self.wait_for_move_completion()
            
            if valve_ready:                
                # construct move command 
                if move_direction=='CW' or move_direction=='cw':
                    move_command='-' + format(port_number,'02X') + '\r'  # Use format(number,'02X') to convert integer to a two digit hex number with capital letters
                elif move_direction=='CCW' or move_direction=='ccw':   
                    move_command='+' + format(port_number,'02X') + '\r'
                else:
                    move_command='P' + format(port_number,'02X') + '\r'
                                     
                # Send move command to the valve
                self.CommPort.write(move_command.encode("utf-8"))
                self.logevent('Command sent to shear valve: ' + move_command,'ACTION')

                # Read response from the valve to check for any issues with the command
                valve_response=self.read_valve_response()
                if len(valve_response)==1:
                    self.logevent(valve_response,'ERROR')
                else:
                    [valve_position,error_code,error_code_string]=valve_response
                    if error_code!=0:
                        self.logevent('Encountered Error while completing valve port change operation','ERROR')
                        self.logevent('Error: ' + error_code_string,'ERROR')
                        return cmd_status
                    else:
                        # Wait for move completion
                        [cmd_status,valve_position]=self.wait_for_move_completion()    
                        if cmd_status:
                            if valve_position==port_number:                                
                                self.logevent('Successfully executed last command to change shear valve position','RESULT')
                            else:
                                self.logevent('Successfully executed last command but current valve position doesn''t match commanded valve position','ERROR')
                                return False
                        return cmd_status                    
            else:
                return cmd_status

        except:
            self.logevent(str(sys.exc_info()[1]),'ERROR') 
            return cmd_status                
                
            
    def wait_for_move_completion(self):
        try:
            move_completion_status=False
            # Keep checking valve status periodically to detect end of move completion
            move_start_time=time.time()
            while (time.time()-move_start_time)<self.Max_movement_duration:
                valve_status_check_cmd='S\r'
                self.CommPort.write(valve_status_check_cmd.encode("utf-8"))
                self.logevent('Command sent to shear valve: ' + valve_status_check_cmd,'ACTION')
                
                # Read valve response
                valve_response=self.read_valve_response()
                if len(valve_response)==1:
                    self.logevent(valve_response,'WARNING')
                else:
                    [valve_position,error_code,error_code_string]=valve_response
                    
                    if error_code!=0:
                        self.logevent('Encountered Error while completing valve move','ERROR')
                        self.logevent('Error: ' + error_code_string,'ERROR')
                        # Any error code other than 0 would indicate failure of move which cannot be corrected manual intervention
                        return [move_completion_status,-1] # -1 is a dummy valve position here that is not used in the calling function
                    else:
                        # Check if move is complete
                        if valve_position>=1 and valve_position<=self.number_of_valve_ports:
                            self.logevent('Shear Valve reported current valve position at port: ' + str(valve_position),'RESULT')                            
                            move_completion_status=True
                            return [move_completion_status,valve_position]
                        else:
                            time.sleep(self.valve_status_check_delay) 

            # Control reaches here if move failed to complete in maximum move duration
            self.logevent('Could not finish last shear valve move in maximum move duration allowed: ' + str(self.Max_movement_duration) + ' sec','ERROR')
            return [move_completion_status,-1] # -1 is a dummy valve position here that is not used in the calling function                                                                
        except:
            self.logevent(str(sys.exc_info()[1]),'ERROR') 
            return [move_completion_status,-1] # -1 is a dummy valve position here that is not used in the calling function
                                
    
    def read_valve_response(self):
        try:            
            # Delay to ensure valve response is ready
            time.sleep(self.min_valve_response_time)
            # Read response from the valve
            ValveResponse = ""
            #read_start_time=time.time()

            for databyte in range(self.Max_response_databytes):
                current_byte=self.CommPort.read(1)
                if current_byte.decode("utf-8")=='\r': # Carriage return indicates end of response 
                    break                        
                ValveResponse=ValveResponse+current_byte.decode("utf-8")

            self.logevent('Raw Valve Response: ' + ValveResponse,'RESULT')                
            # Parse response from the valve
                    
            if len(ValveResponse)>0: 
                if ValveResponse[0]=='*': # Valve returns a * if it is busy with a move
                    return ['Valve is busy']
                elif len(ValveResponse)>=2:
                    valve_response_value=int(ValveResponse[0:2],16) # [0:2] = elements 0 and 1 in the list!
                    [valve_position,error_code,error_code_string]=self.decode_shear_valve_error(valve_response_value)                                 
                    return [valve_position,error_code,error_code_string]
                else:
                    return ['error reading valve status']
            else:
                # Valve only returned a carriage return which is just a confirmation for receiving a command
                return [-1,0,0] # Return dummy valve_position, error_code and error_code_string. Only error_code is used in the calling function
                    
        except:
            self.logevent(str(sys.exc_info()[1]),'ERROR') 
                    

    def decode_shear_valve_error(self,valve_response_value):
        try:
            error_strings={99:'valve failure(valve cannot be homed',
                           88:'non-volatile memory error',
                           77: 'valve configuration error or command mode error',
                           66: 'valve positioning error',
                           55: 'data integrity error',
                           44: 'data CRC error'}
    
            # Check if the valve response value is an error code
            if valve_response_value in error_strings.keys():
                error_code=valve_response_value 
                error_code_string=error_strings[error_code]
                valve_position=-1
            else:
                # There was no error in the last move and the valve is at a known port location
                valve_position=valve_response_value
                error_code=0
                error_code_string=''
                                                       
            return [valve_position,error_code,error_code_string]

        except:
            self.logevent(str(sys.exc_info()[1]),'ERROR') 

    def logevent(self,event_string,event_type):
        if self.additional_log==None:
            if event_type=='ERROR' or event_type=='WARNING':
                print(event_type + ' : ' + event_string)
            else:
                print(event_string)
        # else:
        #     BB_Formatted_Log(event_string, event_type, self.additional_log)



def set_shear_valve(position, com_port='COM7', move_direction="CW"): # 'CW' or 'CCW'
    """Move shear valve to a given position, return once the move is finished"""
    try:
        valve=shear_valve(com_port)
        valve.move_to_position(position,move_direction)
        valve.CommPort.close()
    except:
        print(str(sys.exc_info()[1])) 
        valve.CommPort.close()
    return
