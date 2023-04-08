from tkinter import filedialog

import can

if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    bootloader_log = can.BLFReader(file_name)
    counter = False
    byte_counter = 0
    for line in bootloader_log:
        if line.data == [0x01, 0x00, 0x10, 0x00, 0x00, 0xFF, 0xFF]:
            counter = True
        if line.data == [0x05, 0x01, 0xE5, 0x84, 0x30, 0x10, 0xE5, 0x84]:
            counter = False
        if counter and line.data[:2] == [0x05, 0x01]:
            byte_counter += len(line.data) - 2

    print(byte_counter)
