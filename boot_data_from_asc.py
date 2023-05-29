from tkinter import filedialog

import can


def data_from_asc_my(file_asc) -> list[str]:
    data_log = can.ASCReader(file_asc)
    final_list = []
    for line in data_log:
        if line.data[0] == 0x01 and line.data[1] == 0xFF:
            continue
        data_str = str(line.arbitration_id) + '   '
        for n, i in enumerate(line.data):
            if n == 1:
                continue
            data_str += hex(i)[2:].upper().zfill(2) + ' '
        final_list.append(data_str + '\n')
    return final_list


def blf_to_asc_convert(blf_file: str) -> str:
    with open(blf_file, 'rb') as f_in:
        log_in = can.io.BLFReader(f_in)
        asc_file = blf_file.replace('.blf', '.asc')
        with open(asc_file, 'w') as f_out:
            log_out = can.io.ASCWriter(f_out)
            for msg in log_in:
                log_out.on_message_received(msg)
            log_out.stop()
    return asc_file


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    if '.blf' in file_name:
        file_name = blf_to_asc_convert(file_name)
    data_list = data_from_asc_my(file_name)

    with open(file_name.replace('.asc', '.txt'), 'w+') as file:
        for ch in data_list:
            file.write(ch)
