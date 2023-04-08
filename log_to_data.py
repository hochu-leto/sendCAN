from tkinter import filedialog

import can

from attempt_one import list_breaker


def data_from_log(log: list[str]) -> list[int]:
    final_list = []
    for strg in log:
        if 'd 8 05 01 ' not in strg:
            continue
        data_chunk = strg.split('d 8 05 01 ')[1]
        for chunk in data_chunk.split(' '):
            try:
                final_list.append(int(chunk, 16))
            except ValueError:
                continue
    return final_list


def data_from_asc(file_asc) -> list[int]:
    data_log = can.ASCReader(file_asc)
    # final_list = [int(bt, 16) for line in data_log if line.data[:2] == [0x05, 0x01] for bt in line.data]
    final_list = []
    for line in data_log:
        if list(line.data[:2]) == [0x05, 0x01]:
            for bt in line.data[2:]:
                final_list.append(int(bt))
    return final_list


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    # with open(file_name, 'r') as file:
    #     data_list = data_from_log(file.readlines())
    data_list = data_from_asc(file_name)
    chunk_list = list_breaker(data_list)
    with open('data_from_log.txt', 'w+') as file:
        for ch in chunk_list:
            stri = ''
            for i in ch:
                stri += hex(i)[2:].upper().zfill(2)
            stri += '\n'
            print((len(ch), len(stri)))
            file.write(stri)
    print(len(chunk_list))
