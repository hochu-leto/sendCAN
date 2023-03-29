import can


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
    print(Msg_send)
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
                print(Msg_recv)
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


def fun_can_send_chunk(can_bus: can.BusABC, can_id: int, data: list[int]):
    for i in range(0, len(data), 6):
        FrameData = []
        FrameData[0:0 + 2] = [0x05, 0x01]
        FrameData[2:2 + 6] = data[i:i + 6]
        fun_can_send_OneFrame(can_bus, can_id, FrameData)
    fun_can_send_OneFrame(can_bus, can_id, [0x02, 0x01])
    FlowControlMsg = fun_can_rev_OneFrame(can_bus)


if __name__ == '__main__':

    # with open('vmu_n1.hex', 'r') as file:
    with open('vmu_n3_mirrors_heating.hex', 'r') as file:
        data_list = data_from_hex(file.readlines())
    chunk_list = list_breaker(data_list)
    bus = can.Bus(receive_own_messages=True, interface='virtual')
    CAN_ID_TX = 0x01
    for ch in chunk_list:
        fun_can_send_chunk(bus, CAN_ID_TX, ch)
    print(len(chunk_list))
