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
    try:
        while True:
            Msg_recv = bus.recv(1)
            if Msg_recv is not None:
                return Msg_recv
            else:
                print('Нет ответа от шины')
    except can.CanError:
        print(can.CanError)
    return False


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
        if ':0200000400' in strng:  # название раздела
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


Error = 0xFE

Next = 0x42
EndOfBlock = 0x1E
EndOfHex = 0x08
answer_list = [Next, EndOfBlock, EndOfHex]


def fun_can_send_0501(can_bus: can.BusABC, can_id: int, data: list[int]):
    for i in range(0, len(data), 6):
        FrameData = []
        FrameData[0:0 + 2] = [0x05, 0x01]
        FrameData[2:2 + 6] = data[i:i + 6]
        fun_can_send_OneFrame(can_bus, can_id, FrameData)
    fun_can_send_OneFrame(can_bus, can_id, [0x02, 0x01])
    FlowControlMsg = fun_can_rev_OneFrame(can_bus)
    ans = FlowControlMsg.data[3]
    if ans in answer_list:
        return ans
    # if list(FlowControlMsg.data) == [0x02, 0x01, 0x00, 0x42, 0x00, 0x00]:
    #     return Next
    # elif list(FlowControlMsg.data) == [0x02, 0x01, 0x00, 0x1E, 0x00, 0x00]:
    #     return EndOfBlock
    # elif list(FlowControlMsg.data) == [0x02, 0x01, 0x00, 0x08, 0x00, 0x00]:
    #     return EndOfHex
    # else:
    for bt in FlowControlMsg.data:
        print(hex(bt), end='')
    print()
    return Error


def write_to_file(chunk, file_to_write):
    stri = ''
    for i in chunk:
        stri += hex(i)[2:].upper().zfill(2)
    stri += '\n'
    # print((len(ch), len(stri)))
    file_to_write.write(stri)


def next_memory_area(byte_sent, old_pointer):
    PointerFrameData = [0x0D, 0x01, 0x00]
    fun_can_send_OneFrame(bus, CAN_ID_TX, PointerFrameData +
                          [0x00, (old_pointer & 0xFF0000) >> 16, (old_pointer & 0xFF00) >> 8, old_pointer & 0xFF])
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if FlowControlMsg.data != PointerFrameData:
        return False
    new_pointer = old_pointer + byte_sent + 1
    return new_pointer


def first_chunk_send(bytes):
    ChunkFrameData = [0x0B, 0x01, 0x08, 0x02, 0x00, 0x00]
    fun_can_send_OneFrame(bus, CAN_ID_TX, ChunkFrameData +
                          [(bytes & 0xFF00) >> 8, bytes & 0xFF])
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if list(FlowControlMsg.data) != ChunkFrameData[:2] + [0x01]:
        return False
    return True


def second_chunk_send(bytes):
    ChunkFrameData = [0x0B, 0x01, 0x08, 0x03, 0x00, 0x00]
    fun_can_send_OneFrame(bus, CAN_ID_TX, ChunkFrameData +
                          [(bytes & 0xFF00) >> 8, bytes & 0xFF])
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if list(FlowControlMsg.data) != ChunkFrameData[:2] + [0x01]:
        return False
    return True


def end_of_memory_area(last_chunk, old_pointer):
    first_chunk = 0xFFFF
    new_pointer = next_memory_area(first_chunk, old_pointer)
    if not new_pointer:
        return False
    if not first_chunk_send(first_chunk):
        return False
    second_chunk = last_chunk - first_chunk
    new_pointer = next_memory_area(second_chunk, new_pointer)
    if not new_pointer:
        return False
    if not second_chunk_send(second_chunk):
        return False
    return new_pointer


def send_and_answer(data: list[int]) -> bool:
    fun_can_send_OneFrame(bus, CAN_ID_TX, data)
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if list(FlowControlMsg.data) != data[:2]:
        return False
    return True


def go_command():
    FrameData = [0x0D, 0x01, 0x08, 0x02, 0x00, 0x00]
    return send_and_answer(FrameData)


def alternative_go_command():
    FrameData = [0x0D, 0x01, 0x00, 0x0A, 0x00, 0x80]
    return send_and_answer(FrameData)


def command_1801():
    FrameData = [0x18, 0x01, 0xA9, 0x31, 0xBA, 0x5D]
    return send_and_answer(FrameData)


def end_of_boot_hex(last_chunk, old_pointer):
    first_chunk = 0xFFFF
    new_pointer = next_memory_area(first_chunk, old_pointer)
    if not new_pointer:
        return False

    if last_chunk <= first_chunk:
        if not second_chunk_send(last_chunk):
            return False
        return new_pointer

    if not first_chunk_send(first_chunk):
        return False
    second_chunk = last_chunk - first_chunk
    new_pointer = next_memory_area(second_chunk, new_pointer)
    if not new_pointer:
        return False
    if not second_chunk_send(second_chunk):
        return False
    return new_pointer


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()

    # with open('vmu_n1.hex', 'r') as file:
    # with open('vmu_n3_mirrors_heating.hex', 'r') as file:
    with open(file_name, 'r') as file:
        data_list = data_from_hex(file.readlines())
    size_of_hex = len(data_list)
    chunk_list = list_breaker(data_list)
    bus = can.Bus(channel=0, receive_own_messages=True, interface='kvaser', bitrate=125)
    CAN_ID_TX = 0x01
    pointer = 0x090000
    counter = 0

    # -------------------------- boooooot hex --------------------------
    # with open('data_like_log.txt', 'w+') as file:
    for ch in chunk_list:
        # write_to_file(ch, file)
        matc = fun_can_send_0501(bus, CAN_ID_TX, ch)
        counter += len(ch)
        if matc == Error:
            print('Wrong answer from TTC')
            break
            # continue
        elif matc == Next:
            continue
        elif matc == EndOfBlock:
            pointer = end_of_memory_area(counter, pointer)
            counter = 0
            if not pointer:
                print('Wrong answer from TTC in change pointer')
                break
            go_command()
        elif matc == EndOfHex:
            pointer = end_of_boot_hex(counter, pointer)
            if not pointer:
                print('Wrong answer from TTC at the end of hex')
                break
            command_1801()
            alternative_go_command()
