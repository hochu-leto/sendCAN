import time

import can
from tkinter import filedialog


# import math
# import SecurityAccessAlgrithm as SA


# function name: fun_Bytes_To_Hex_InStr
# Parameter: bytes type
# :str type
# : Convert the list of decimal data elements to hexadecimal and return as a string,
# mainly used for data hexadecimal printing for easy viewing
def fun_Bytes_To_Hex_InStr(bytes):
    l = [('%02x' % i) for i in bytes]
    return "|".join(l)

    # function name: fun_can_send_OneFrame


# Parameter: bus(object),can_id（Number）,can_data（list）,is_extended_id=False
# :None
# : CANMessageDLC<=8When calling this function
def fun_can_send_OneFrame(bus, can_id, can_data, is_extended_id=False):
    # Msg_send = can.Message(extended_id=is_extended_id, arbitration_id=can_id, data=can_data, )
    Msg_send = can.Message(is_extended_id=is_extended_id, arbitration_id=can_id, data=can_data, )
    # print(Msg_send)
    try:
        bus.send(Msg_send)
    except can.CanError:
        pass


# function name: fun_can_rev_OneFrame
# Parameter: bus object
# :CAN  Msg object
# :CANWhen the message is received, the function is called first.
def fun_can_rev_OneFrame(bus):
    Msg_recv = None
    try:
        while True:
            Msg_recv = bus.recv(1)
            if Msg_recv is not None:
                # print(Msg_recv)
                break
    except can.CanError:
        pass
    return Msg_recv


# function name: fun_Get_PCI
# Parameter:CAN Msg.data
# :Number
#       0<->Single frame
#       1<->First frame
#       2<->Continuous frame
#       3<->Flow control frame
def fun_Get_PCI(Msgdata):
    PCIFlag = None
    PCI = Msgdata[0] & 0xF0
    if PCI == 0x00:  #
        PCIFlag = 0
    elif PCI == 0x10:  #
        PCIFlag = 1
    elif PCI == 0x20:  #
        PCIFlag = 2
    elif PCI == 0x30:  #
        PCIFlag = 3
    return PCIFlag


# function name: fun_can_send_MultiFrame
# Parameter: bus(object),can_id（Number）,can_data（list）,data_length（Number）
# :None
# : CANThis function is called when the message sends multi-frame data.
# The function will send multiple frames of data at a time, ignoring the flow control processing.
def fun_can_send_MultiFrame(bus, can_id, can_data, data_length):
    FirstFrameData = []
    if data_length // 256 >= 16:
        pass
    else:
        FirstFrameData[0:0 + 2] = data_length.to_bytes(2, byteorder='big')
        FirstFrameData[0] += 0x10
        FirstFrameData[2:2 + 6] = can_data[0:0 + 6]
        fun_can_send_OneFrame(bus, can_id, FirstFrameData)
        FlowControlMsg = fun_can_rev_OneFrame(bus)

        if (data_length - 6) % 7 == 0:
            ConsecutiveFrameCounter = (data_length - 6) // 7
            for i in range(1, ConsecutiveFrameCounter + 1, 1):
                ConsecutiveFrameData = []
                SN = i % 16
                ConsecutiveFrameData[0:0 + 1] = (SN + 0x20).to_bytes(1, byteorder='big')
                ConsecutiveFrameData[1:1 + 7] = can_data[6 + (i - 1) * 7:6 + 7 * i]
                print(fun_Bytes_To_Hex_InStr(ConsecutiveFrameData))
                fun_can_send_OneFrame(bus, can_id, ConsecutiveFrameData)
        else:
            ConsecutiveFrameCounter = (data_length - 6) // 7 + 1
            remainder = (data_length - 6) % 7
            for i in range(1, ConsecutiveFrameCounter + 1, 1):
                if i < ConsecutiveFrameCounter:
                    ConsecutiveFrameData = []
                    SN = i % 16
                    ConsecutiveFrameData[0:0 + 1] = (SN + 0x20).to_bytes(1, byteorder='big')
                    ConsecutiveFrameData[1:1 + 7] = can_data[6 + (i - 1) * 7:6 + 7 * i]
                    # print(fun_Bytes_To_Hex_InStr(ConsecutiveFrameData))
                    fun_can_send_OneFrame(bus, can_id, ConsecutiveFrameData)
                else:
                    ConsecutiveFrameData = []
                    SN = i % 16
                    ConsecutiveFrameData[0:0 + 1] = (SN + 0x20).to_bytes(1, byteorder='big')
                    ConsecutiveFrameData[1:1 + remainder] = can_data[data_length - remainder:data_length]
                    # print(fun_Bytes_To_Hex_InStr(ConsecutiveFrameData))
                    fun_can_send_OneFrame(bus, can_id, ConsecutiveFrameData)
        # print(fun_Bytes_To_Hex_InStr(FirstFrameData))


# function name: fun_can_recv_MultiFrame
# Parameter: bus object, receiving data length
# Back to list
# : Before calling this function, first call the Get_PCI function to judge the
# received first frame data as the first frame data, and pass the data length parameter of the first frame;
# The data returned in this function does not include the data in the first frame.
def fun_can_recv_MultiFrame(bus, data_length):
    MultiFrame_Recv_Data = []
    RecievedData = []
    if (data_length - 6) % 7 == 0:
        FrameRecvCnter = (data_length - 6) // 7
        for i in range(0, FrameRecvCnter):
            Msg_recv = fun_can_rev_OneFrame(bus)
            MultiFrame_Recv_Data.append(Msg_recv.data)
    else:
        print("Entered CF recieve function...")
        FrameRecvCnter = (data_length - 6) // 7 + 1
        for i in range(0, FrameRecvCnter):
            Msg_recv = fun_can_rev_OneFrame(bus)
            MultiFrame_Recv_Data.append(Msg_recv.data)

    FrameNumber = len(MultiFrame_Recv_Data)

    if (data_length - 6) % 7 == 0:  # SNKeep actual data
        for i in range(0, FrameNumber, 1):
            RecievedData += MultiFrame_Recv_Data[i][1:1 + 7]
    else:
        DataRemainder = (data_length - 6) % 7
        for i in range(0, FrameNumber, 1):
            if i < FrameNumber - 1:
                RecievedData += MultiFrame_Recv_Data[i][1:1 + 7]
            else:
                # RecievedData += MultiFrame_Recv_Data[i][1:1 + remainder]
                RecievedData += MultiFrame_Recv_Data[i][1:1 + DataRemainder]

    return RecievedData


def data_from_hex(hex_list: list) -> list[int]:
    final_list = []
    for strng in hex_list:
        if ':02000004000AF0' in strng:  # название раздела
            continue
        elif ':00000001FF' in strng:  # конец файла
            break
        else:
            data_string = strng[9:-3]
            for byt in range(0, len(data_string), 2):
                final_list.append(int(data_string[byt:byt + 2], 16))
    return final_list


def list_breaker(full_list: list, byte_in_chunk: int = 66) -> list[list[int]]:
    final_list = []
    for i in range(0, len(full_list), byte_in_chunk):
        final_list.append(full_list[i:i + byte_in_chunk])
    return final_list


def fun_can_send_0501(can_bus: can.BusABC, can_id: int, data: list[int]):
    for i in range(0, len(data), 6):
        FrameData = []
        FrameData[0:0 + 2] = [0x05, 0x01]
        FrameData[2:2 + 6] = data[i:i + 6]
        fun_can_send_OneFrame(can_bus, can_id, FrameData)
    fun_can_send_OneFrame(can_bus, can_id, [0x02, 0x01])
    FlowControlMsg = fun_can_rev_OneFrame(can_bus)


def write_str_to_file(frame: list[int], file_for_write):
    stri = ''
    for i in frame:
        stri += hex(i)[2:].upper().zfill(2)
    stri += '\n'
    file_for_write.write(stri)


def just_send_data_list(can_bus: can.BusABC, can_id: int, d_list: list[list[int]], file_for_write=None):
    for frame in d_list:
        if file_for_write is not None:
            write_str_to_file(frame, file_for_write)
        fun_can_send_OneFrame(can_bus, can_id, frame)


def repeat_while(can_bus: can.BusABC, can_id: int, rep_data: list[int], itr=1, file_for_write=None):
    for _ in range(itr):
        if file_for_write is not None:
            write_str_to_file(rep_data, file_for_write)
        fun_can_send_OneFrame(can_bus, can_id, rep_data)


def send_and_answer(can_bus: can.BusABC, can_id: int, d_list: list[list[int]], file_for_write=None):
    just_send_data_list(can_bus, can_id, d_list)
    AnswerMsg = fun_can_rev_OneFrame(can_bus)
    if file_for_write is not None:
        write_str_to_file(AnswerMsg.data, file_for_write)
    return AnswerMsg.data


def from_log_to_can(log, bus, file):
    old_line = None
    for line in log:
        match line.arbitration_id:
            case 0x1:
                timestamp = (line.timestamp - old_line.timestamp) if old_line else 0
                time.sleep(timestamp)
                fun_can_send_OneFrame(bus, line.arbitration_id, line.data)
                old_line = line
                print(timestamp)
            case 0x2:
                AnsMsg = fun_can_rev_OneFrame(bus)
                print(AnsMsg)
                if line.data[0] == 0x4 and line.data[0] == 0x1:
                    write_str_to_file(line.data, file)
            case _:
                fun_can_send_OneFrame(bus, line.arbitration_id, line.data)


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    with open(file_name, 'r') as file:
        data_list = data_from_hex(file.readlines())
    chunk_list = list_breaker(data_list)

    bootloader_log = can.ASCReader('prepare_for_boot.asc')
    finish_log = can.ASCReader('finish_boot.asc')
    bus = can.Bus(channel=0, receive_own_messages=True, interface='kvaser', bitrate=125000)
    CAN_ID_TX = 0x01

    with open('kvu_answer.txt', 'w+') as file:
        from_log_to_can(bootloader_log, bus, file)
        for ch in chunk_list:
            fun_can_send_0501(bus, CAN_ID_TX, ch)
        from_log_to_can(finish_log, bus, file)

    # with open('vmu_n1.hex', 'r') as file:
    # with open('vmu_n3_mirrors_heating.hex', 'r') as file:
    #

    # with open('data_like_log.txt', 'w+') as file:
    #     repeat_while(bus, CAN_ID_TX, [0x01, 0xff], 400, file)
    # for ch in chunk_list:
    #     fun_can_send_0501(bus, CAN_ID_TX, ch)
    #     stri = ''
    #
    #     for i in ch:
    #         stri += hex(i)[2:].upper().zfill(2)
    #     stri += '\n'
    #     print((len(ch), len(stri)))
    #     file.write(stri)
    # print(len(chunk_list))
