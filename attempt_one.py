import pickle
import time

import can
from tkinter import filedialog

from intelhex import IntelHex


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
def fun_can_rev_OneFrame(bus, wt=1.0):
    try:
        # while True:
        Msg_recv = bus.recv(wt)
        if Msg_recv is not None:
            return Msg_recv
        # else:
        #     print('No answer from vmu')
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
                # print(fun_Bytes_To_Hex_InStr(ConsecutiveFrameData))
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


def data_from_hex(hex_list: list) -> (list[int], str):
    final_list, data_str = [], ''
    for strng in hex_list:
        if ':0200000400' in strng:  # название раздела
            continue
        elif ':00000001FF' in strng:  # конец файла
            break
        else:
            data_string = strng[9:-3]
            data_str += data_string
            for byt in range(0, len(data_string), 2):
                final_list.append(int(data_string[byt:byt + 2], 16))
    return final_list, data_str


def list_breaker(full_list: list, byte_in_chunk: int = 66) -> list[list[int]]:
    final_list = []
    for i in range(0, len(full_list), byte_in_chunk):

        final_list.append(full_list[i:i + byte_in_chunk])
    return final_list


def new_list_breaker(full_list: list, byte_in_chunk: int = 66) -> list[list[int]]:
    final_list = []
    for chnk in range(0, len(full_list), PartOfMemoryArea + 1):
        part_list = full_list[chnk:chnk + PartOfMemoryArea + 1]
        # print(len(part_list))
        for i in range(0, len(part_list), byte_in_chunk):
            ch = part_list[i:i + byte_in_chunk]
            final_list.append(ch)
        # print(len(ch), ch[len(ch) - 1])
    return final_list


Error = 0xFE

Next = 0x42
EndOfBlock = 0x1E
EndOfHex = 0x08
SomeAnswer = 0x18  # only in prepare boot, after booting some hex
answer_list = [Next, EndOfBlock, EndOfHex, SomeAnswer]


def fun_can_send_05(can_bus: can.BusABC, can_id: int, data: list[int]):
    for i in range(0, len(data), 6):
        FrameData = []
        FrameData[0:0 + 2] = [0x05, second_byte]
        FrameData[2:2 + 6] = data[i:i + 6]
        fun_can_send_OneFrame(can_bus, can_id, FrameData)
    fun_can_send_OneFrame(can_bus, can_id, [0x02, second_byte])
    FlowControlMsg = fun_can_rev_OneFrame(can_bus, wt=5)
    return FlowControlMsg   # Error


def write_to_file(chunk, file_to_write):
    stri = ''
    for i in chunk:
        stri += hex(i)[2:].upper().zfill(2)
    stri += '\n'
    file_to_write.write(stri)


def next_memory_area(pointer):
    command_0D([0x00, (pointer & 0xFF0000) >> 16, (pointer & 0xFF00) >> 8, pointer & 0xFF])


def first_chunk_send(bytes):
    return command_0B(go + [(bytes & 0xFF00) >> 8, bytes & 0xFF])


def second_chunk_send(bytes):
    return command_0B(run + [(bytes & 0xFF00) >> 8, bytes & 0xFF])


def end_of_memory_area(pointer):
    print(f'{hex(pointer)=}')
    command_0D([0x00, (pointer & 0xFF0000) >> 16, (pointer & 0xFF00) >> 8, pointer & 0xFF])
    command_0B(go + [0xFF, 0xFF])
    pointer += 0x010000
    command_0D([0x00, (pointer & 0xFF0000) >> 16, (pointer & 0xFF00) >> 8, pointer & 0xFF])
    command_0B(run + [0x7F, 0xFF])
    return pointer + 0x8000


def end_of_boot_hex(len_of_data, pointer):
    command_0D([0x00, (pointer & 0xFF0000) >> 16, (pointer & 0xFF00) >> 8, pointer & 0xFF])
    print(f'{hex(len_of_data)=}')
    if len_of_data < 0x70000:
        ln = len_of_data - 0x60000 - 11
        command_0B(go + [(ln & 0xFF00) >> 8, ln & 0xFF])
        return pointer
    command_0B(go + [0xFF, 0xFF])
    pointer += 0x010000
    command_0D([0x00, (pointer & 0xFF0000) >> 16, (pointer & 0xFF00) >> 8, pointer & 0xFF])
    ln = len_of_data - 0x70000 - 1
    command_0B(run + [(ln & 0xFF00) >> 8, ln & 0xFF])
    return pointer


def send_and_answer(data: list[int]) -> bool:
    fun_can_send_OneFrame(bus, CAN_ID_TX, data)
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if FlowControlMsg and list(FlowControlMsg.data)[:2] != data[:2]:
        return False
    return True


def send_and_answer_list(data: list[int]) -> list:
    fun_can_send_OneFrame(bus, CAN_ID_TX, data)
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    if FlowControlMsg and list(FlowControlMsg.data) == data[:2]:
        return FlowControlMsg.data[2:]
    return []


def go_command():
    return command_0D(go)


def byte_list_from_int(check_sum: int) -> list[int]:
    if check_sum <= 0xFF:
        return [check_sum & 0xFF]
    elif check_sum <= 0xFFFF:
        return [(check_sum & 0xFF00) >> 8, check_sum & 0xFF]
    elif check_sum <= 0xFFFFFF:
        return [(check_sum & 0xFF0000) >> 16, (check_sum & 0xFF00) >> 8, check_sum & 0xFF]
    else:
        return [(check_sum & 0xFF000000) >> 24, (check_sum & 0xFF0000) >> 16, (check_sum & 0xFF00) >> 8,
                check_sum & 0xFF]


def int_from_list(byte_list: list[int]) -> int:
    x = 0
    for i, bt in enumerate(byte_list[::-1]):
        x += bt << (8 * i)
    return x


def command_11(data_list_1101: list[int]) -> bool:  # set CRC-int(Encrypted)
    FrameData = [0x11, second_byte] + data_list_1101
    return send_and_answer(FrameData)


def command_17(data_list_1701: list[int]) -> list:
    FrameData = [0x17, second_byte] + data_list_1701
    return send_and_answer_list(FrameData)


def command_18(data_list_1801: list[int]) -> bool:  # set CRC-int(Encrypted)
    FrameData = [0x18, second_byte] + data_list_1801
    return send_and_answer(FrameData)


def command_19(data_list_1901: list[int]) -> bool:
    FrameData = [0x19, second_byte] + data_list_1901
    return send_and_answer(FrameData)


def command_20(SomeData: list[int]) -> bool:
    FrameData = [0x20, second_byte] + SomeData
    return send_and_answer(FrameData)


def command_0B(data_list_0B: list[int]) -> bool:
    FrameData = [0x0B, second_byte] + data_list_0B
    return send_and_answer(FrameData)


def command_0C(data_list_0C: list[int]) -> bool:
    FrameData = [0x0C, second_byte] + data_list_0C
    return send_and_answer(FrameData)


def command_0D(data_list_0D01: list[int]) -> bool:  # set CRC-int(Encrypted)
    FrameData = [0x0D, second_byte] + data_list_0D01
    return send_and_answer(FrameData)


def command_0E(data_list_0E01: list[int]) -> bool:
    FrameData = [0x0E, second_byte] + data_list_0E01
    return send_and_answer(FrameData)


def switch_something_11(sw: int):
    command_11(switch_address + [sw])
    FlowControlMsg = fun_can_rev_OneFrame(bus)


def request_CRC_Table_Checksum() -> list:
    return request_ttc_10(CRC_Table_Checksum_address)


def request_ttc_10(address: list[int]) -> list:
    RequestFrame = [0x10, second_byte]
    request_frame = RequestFrame + address
    fun_can_send_OneFrame(bus, CAN_ID_TX, request_frame)
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    ttc_data_list = list(FlowControlMsg.data)
    if ttc_data_list[:2] != RequestFrame:
        return 0
    return list(ttc_data_list[-4:])


def request_ttc_1F(address: list[int]) -> int:
    RequestFrame = [0x1F, second_byte]
    request_frame = RequestFrame + address
    fun_can_send_OneFrame(bus, CAN_ID_TX, request_frame)
    FlowControlMsg = fun_can_rev_OneFrame(bus)
    ttc_data_list = list(FlowControlMsg.data)
    if ttc_data_list[:2] != RequestFrame:
        return 0
    return int_from_list(ttc_data_list[-4:])


def request_ttc_04(address: list[int], number_of_bytes: int) -> (list[int]):
    RequestFrame = [0x04, second_byte]
    request_frame = RequestFrame + address + [number_of_bytes]
    final_list, data_str = [], ''
    fun_can_send_OneFrame(bus, CAN_ID_TX, request_frame)
    frame_count = number_of_bytes // 6 + (1 if number_of_bytes % 6 else 0)
    for i in range(frame_count):
        Msg_recv = fun_can_rev_OneFrame(bus)
        useful_data = list(Msg_recv.data[2:])
        final_list += useful_data
    return final_list


def check_some_info():
    some_data_tts = request_ttc_04(lst5_for_0401, 0x10)
    unknown_data1 = int_from_list(some_data_tts[8:12])  # D8 58 68 34
    unknown_data2 = int_from_list(some_data_tts[12:16])  # 9D 45 1E E5

    req_unknown_data2 = request_ttc_1F([0x00, 0x00])
    if req_unknown_data2 != unknown_data2:
        print(f'unknown_data2 isn"t matched\n'
              f' from hex {hex(unknown_data2)} != from ttc {hex(req_unknown_data2)}')
        # quit()

    req_unknown_data1 = request_ttc_1F([0x00, 0x01])
    if req_unknown_data1 != unknown_data1:
        print(f'unknown_data1 isn"t matched\n'
              f' from hex {hex(unknown_data1)} != from ttc {hex(req_unknown_data1)}')
        # quit()


def hello_and_switch_on(tm: float = 0.001):
    time.sleep(tm)
    fun_can_send_OneFrame(bus, CAN_ID_TX, hello_frame)
    switch_something_11(1)


def switch_vmu_to_boot(tm=5000000000):
    switch_frame = [0x01, 0xFF]
    start_time = time.perf_counter_ns()
    while time.perf_counter_ns() < start_time + tm:
        fun_can_send_OneFrame(bus, CAN_ID_TX, switch_frame)
        time.sleep(0.005)


def request_ttc_14(sec_byte: int):
    ask_address = [0x14, sec_byte]
    time.sleep(0.005)
    fun_can_send_OneFrame(bus, CAN_ID_TX, ask_address)
    FlowControlMsg = fun_can_rev_OneFrame(bus, wt=0.025)
    return FlowControlMsg


def ask_switch_number() -> (int, list[int]):
    sec_bytes = [0x00, 0x01, 0x05, 0x0A, 0x69]
    ecu_number_list = []
    second_b = 0
    for s_byte in sec_bytes:
        msg = request_ttc_14(s_byte)
        if msg:
            ecu_number_list = msg.data[2:]
            second_b = s_byte
    return second_b, list(ecu_number_list)


def check_CRC_Table_Checksum(crc_Table_Checksum_list: list):
    command_18(CRC_int_Encrypted_list)  # check_sum_list = [0xA9, 0x31, 0xBA, 0x5D]
    # command_18(byte_list_from_int(CRC_int_Encrypted))  # check_sum_list = [0xA9, 0x31, 0xBA, 0x5D]
    command_0D(CRC_Table_Address_list)  # check_sum_list = [0x00, 0x0A, 0x00, 0x80]
    # command_0D(byte_list_from_int(CRC_Table_Address))  # check_sum_list = [0x00, 0x0A, 0x00, 0x80]
    table_checksum = request_CRC_Table_Checksum()
    print(f'give = {" ".join([hex(i) for i in crc_Table_Checksum_list])} ,'
          f' get = {" ".join([hex(i) for i in table_checksum])}')
    if table_checksum != crc_Table_Checksum_list:  # 8B 16 73 6D     old CRC_Table_Checksum = FE D9 6C 12
        print(f'CRC_Table_Checksum isn"t matched\n')
    check_some_info()
    return table_checksum


def set_some_number_and_on():
    command_19(lst1_for_19)  # B9 20 2E E7
    switch_something_11(1)


def set_another_number_and_off():
    command_19(lst2_for_1901)  # B9 20 2E E7
    switch_something_11(0)


def booot_hex(chunks_list: list, point: int):
    counter_send_byte = 0
    for ch in chunks_list:
        answer = fun_can_send_05(bus, CAN_ID_TX, ch)
        counter_send_byte += len(ch)
        if counter_send_byte >= PartOfMemoryArea:
            point = end_of_memory_area(point)
            counter_send_byte = 0
            go_command()
    return point


def info_and_CRC_after_boot():
    # +++++++++++++++++++++это повторяется после загрузки основной прошивки++++++++++++++
    ttc_information = request_ttc_04(lst1_for_0401, 0x80)
    ttc_information += request_ttc_04(lst2_for_0401, 0x80)
    command_18(lst1_for_1801)  # вообще непонятно откуда эта цифра  ok
    command_0D(lst2_for_0D01)  # ????????????   ok
    unknown_CRC1 = request_ttc_10(lst1_for_1001)  # 48 5C 5B 0E     ok
    # это последние 4 байта из ttc_information
    if unknown_CRC1 != ttc_information[-4:]:
        print(f'{unknown_CRC1=} is not {ttc_information[-4:]=}')
    #     на пустом кву не совпадает
    else:
        checksum = CRC_Table_Checksum_list or ttc_information[156:160]
        check_CRC_Table_Checksum(checksum)
    ttc_information += request_ttc_04(lst3_for_0401, 0x80)

    command_18(lst2_for_1801)  # вообще непонятно откуда эта цифра  ok
    command_0D(lst3_for_0D01)  # ????????????   ok
    unknown_CRC2 = request_ttc_10(lst2_for_1001)  # ok 74 01 FB 28

    ttc_information += request_ttc_04(lst4_for_0401, 0x80)
    hello_and_switch_on()
    set_another_number_and_off()  # other number
    # ++++++++++++++++++++ это повторяется после загрузки основной прошивки++++++++++++++
    return ttc_information, unknown_CRC2


def say_good_buy():
    good_buy_frame = [0x11, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x01]
    fun_can_send_OneFrame(bus, CAN_ID_TX, good_buy_frame)
    fun_can_send_OneFrame(bus, CAN_ID_TX, [0x03, 0xFF])


if __name__ == '__main__':
    # загрузчик
    with open('data_for_first_boot_ttc.pickle', 'rb') as fp:
        first_data_list = pickle.load(fp)
    first_list = list_breaker(first_data_list)
    # file_name = filedialog.askopenfilename()
    # ih = IntelHex(file_name)
    # dt_list = list(ih.todict().values())
    # print(f'{hex(len(dt_list)).upper()=}')

    bus = can.Bus(channel=0, receive_own_messages=False, interface='kvaser', bitrate=500000)
    CAN_ID_TX = 0x01
    pointer = 0x0A0000
    counter = 0
    PartOfMemoryArea = 0xFFFF + 0x8000

    CRC_Table_Checksum_address = [0x00, 0x00, 0x00, 0x10]

    hello_frame = [0x11, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00]
    go = [0x08, 0x02, 0x00, 0x00]
    run = [0x08, 0x03, 0x00, 0x00]

    lst1_for_0401 = [0x00, 0x00, 0xFF, 0x80]
    lst2_for_0401 = [0x00, 0x0A, 0x00, 0x00]
    lst3_for_0401 = [0x00, 0x09, 0xFF, 0x80]
    lst4_for_0401 = [0x00, 0x01, 0x80, 0x00]
    lst5_for_0401 = [0x00, 0x0A, 0x00, 0x80]

    lst1_for_0E01 = [0x08, 0x00, 0xCA, 0x00]

    lst1_for_0D01 = [0x08, 0x00, 0x30, 0x00]
    lst2_for_0D01 = [0x00, 0x0A, 0x00, 0x00]
    lst3_for_0D01 = [0x00, 0x02, 0x00, 0x00]

    lst1_for_1001 = [0x00, 0x00, 0x00, 0x7C]
    lst2_for_1001 = [0x00, 0x07, 0xFF, 0x80]

    lst2_for_1701 = [0x5B, 0x5E, 0x46, 0x81]  # lst2_for_1700 = [0xC6, 0xF3, 0xF4, 0x1E, 0x01] C6  F3  F4  1E  01

    lst1_for_1801 = [0xB6, 0xE0, 0xC2, 0xEC]
    lst2_for_1801 = [0x0A, 0xEC, 0xAB, 0x26]

    lst1_for_19 = [0xB9, 0x20, 0x2E, 0xE7]  # [0xCB, 0x26, 0xFE, 0x10]
    lst2_for_1901 = [0xD3, 0xDE, 0xAE, 0x44]  # C6  08  B5  7E
    # switch_address = [0x40, 0xAF, 0x35, 0x9F]

    CRC_int_Encrypted_list = [0xA9, 0x31, 0xBA, 0x5D]   # не факт
    CRC_Table_Address_list = lst5_for_0401.copy()   # не факт
    CRC_Table_Checksum_list = None
    # ======================= из файла connect_to_ttc ==================================
    switch_vmu_to_boot()  # ok
    second_byte, switch_address = ask_switch_number()  # ok

    hello_and_switch_on(0.25)  # ok

    some_list = command_17(lst1_for_19 + [0x00])  # another_list ?????????????
    another_list = command_17(lst2_for_1701 + [0x01])  # another_list ??????????
    if not some_list or not another_list:
        print(f'wrong answer from vmu for 17 01 request')

    time.sleep(0.05)
    fun_can_send_OneFrame(bus, CAN_ID_TX, hello_frame)
    hello_and_switch_on(0.025)  # ok
    command_0D(lst1_for_0D01)  # ok
    booot_hex(first_list, 0)  # ok

    command_0E(lst1_for_0E01)  # ok
    alternative_switch_address = list(request_ttc_14(second_byte).data)[2:]  # ok
    some_list = command_17(lst1_for_19 + [0x00])  # other
    another_list = command_17(lst2_for_1701 + [0x01])  # other
    if not some_list or not another_list:
        print(f'wrong answer from vmu for 17 01 request')
        # quit()

    hello_and_switch_on()  # ok
    set_some_number_and_on()  # ok
    info_before, some_CRC = info_and_CRC_after_boot()  # ng 19 list

    # ==================================== select file ======================================
    file_name = filedialog.askopenfilename()
    # file_name = 'C:\\Users\\timofey.inozemtsev\\PycharmProjects\\sendCAN\\my_boot_580\\full_boot_1.5.0\\vmu_n1_580_1_5_0.hex'
    ih = IntelHex(file_name)
    dt_list = list(ih.todict().values())
    print(f'{len(dt_list)=}')
    Node_Type_list = dt_list[12:16]
    CRC_Table_Address_list = dt_list[16:20]
    CRC_Table_Checksum_list = dt_list[28:32]
    CRC_int_Encrypted_list = dt_list[36:40]
    chunk_list = new_list_breaker(dt_list)

    hello_and_switch_on()
    set_some_number_and_on()
    hello_and_switch_on()
    set_another_number_and_off()

    # =================================== всё, что в файле boot_hex.asc=======================
    hello_and_switch_on()  # ok
    set_some_number_and_on()  # ng 19 list
    # я хрен его знаю что это - хост задаёт какие-то адреса в кву  ok
    sec0A = command_0C([0x00, 0x0A, 0x00, 0x00, 0xFF, 0xFF])
    sec0C = command_0C([0x00, 0x0C, 0x00, 0x00, 0xFF, 0xFF])
    sec0E = command_0C([0x00, 0x0E, 0x00, 0x00, 0xFF, 0xFF])
    sec10 = command_0C([0x00, 0x10, 0x00, 0x00, 0xFF, 0xFF])
    if not sec0A or not sec0C or not sec0E or not sec10:
        print(f'some memory area can"t set')

    go_command()

    # -------------------------- boooooot hex --------------------------

    pointer = booot_hex(chunk_list, pointer)
    pointer = end_of_boot_hex(len(dt_list), pointer)
    if not pointer:
        print('Wrong answer from TTC at the end of hex')
    # --------------------------------------- end of boot hex -------------------

    check_CRC_Table_Checksum(CRC_Table_Checksum_list)

    # я хрен его знаю что это - хост задаёт какие-то адреса в кву
    sec0A = command_20([0x00, 0x0A, 0x00, 0x00, 0x00, 0x00])
    sec0C = command_20([0x00, 0x0C, 0x00, 0x00, 0x00, 0x00])
    sec0E = command_20([0x00, 0x0E, 0x00, 0x00, 0x00, 0x00])
    sec10 = command_20([0x00, 0x10, 0x00, 0x00, 0x00, 0x00])
    if not sec0A or not sec0C or not sec0E or not sec10:
        print(f'some memory area can"t set')
    info_after, new_crc = info_and_CRC_after_boot()
    # ========================================================
    hello_and_switch_on(0.05)
    set_some_number_and_on()
    check_CRC_Table_Checksum(CRC_Table_Checksum_list)
    hello_and_switch_on()
    set_another_number_and_off()
    # ---------------------------------------
    hello_and_switch_on(0.07)
    set_some_number_and_on()
    check_CRC_Table_Checksum(CRC_Table_Checksum_list)
    hello_and_switch_on()
    set_another_number_and_off()
    # ==================================================================================
    say_good_buy()
