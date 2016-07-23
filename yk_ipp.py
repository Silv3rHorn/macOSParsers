import argparse
import datetime
import struct

__author__ = 'yk'
__version__ = '.20160611'
__reference1__ = "https://www.ma.rhul.ac.uk/static/techrep/2015/RHUL-MA-2015-8.pdf (Pg 68-69)"
__reference2__ = "https://www.iana.org/assignments/ipp-registrations/ipp-registrations.txt"


def parse(raw_data):
    del result[:]
    result.append("Version        : {}".format(float(struct.unpack('B', raw_data[0:1])[0]) +
                                               float(struct.unpack('B', raw_data[1:2])[0]) * 0.1))
    result.append("Operation ID   : {}".format(struct.unpack('>H', raw_data[2:4])[0]))
    result.append("Request ID     : {}".format(struct.unpack('>I', raw_data[4:8])[0]))
    raw_data = raw_data[8:]

    while True:
        if b'\x01' <= raw_data[0:1] <= b'\x07':  # valid operation attributes
            if raw_data[0:1] == b'\x03':  # end-of-attributes tag
                break
            else:
                raw_data = raw_data[1:]
        elif raw_data[0:1] == b'\x20' or raw_data[0:1] == b'\x21' or raw_data[0:1] == b'\x23':
            bytes_read = _parse_attr(raw_data, True, False, False, False)
            raw_data = raw_data[bytes_read:]
        elif raw_data[0:1] == b'\x22':
            bytes_read = _parse_attr(raw_data, False, True, False, False)
            raw_data = raw_data[bytes_read:]
        elif raw_data[0:1] == b'\x31':
            bytes_read = _parse_attr(raw_data, False, False, True, False)
            raw_data = raw_data[bytes_read:]
        elif b'\x40' <= raw_data[0:1] <= b'\x4a':
            bytes_read = _parse_attr(raw_data, False, False, False, True)
            raw_data = raw_data[bytes_read:]
        else:
            pass

    return result


def _parse_attr(raw_data, is_int, is_bool, is_datetime, is_str):
    bytes_read = 0

    len_name = struct.unpack('B', raw_data[2:3])[0]
    attr_name = struct.unpack(str(len_name) + 's', raw_data[3:3 + len_name])[0].decode('utf-8')
    attr_value = None

    if is_int:
        attr_value = struct.unpack('>I', raw_data[3 + len_name + 2:3 + len_name + 6])[0]
        bytes_read = 3 + len_name + 6
    if is_bool:
        attr_value = struct.unpack('?', raw_data[3 + len_name + 2:3 + len_name + 3])[0]
        bytes_read = 3 + len_name + 3
    if is_datetime:
        dt = raw_data[3 + len_name + 2:3 + len_name + 13]
        attr_value = str(struct.unpack('>H', dt[0:2])[0]) + '-' + str(struct.unpack('B', dt[2:3])[0]).zfill(2) + '-' + \
                     str(struct.unpack('B', dt[3:4])[0]).zfill(2) + ' ' + \
                     str(struct.unpack('B', dt[4:5])[0]).zfill(2) + ':' + \
                     str(struct.unpack('B', dt[5:6])[0]).zfill(2) + ':' + \
                     str(struct.unpack('B', dt[6:7])[0]).zfill(2) + '.' + \
                     str(struct.unpack('B', dt[7:8])[0]) + ' ' + struct.unpack('1s', dt[8:9])[0].decode('utf-8') + \
                     str(struct.unpack('B', dt[9:10])[0]).zfill(2) + ':' + \
                     str(struct.unpack('B', dt[10:11])[0]).zfill(2)
        bytes_read = 3 + len_name + 13
    if is_str:
        len_value = struct.unpack('B', raw_data[3 + len_name + 1:3 + len_name + 2])[0]
        attr_value = struct.unpack(str(len_value) + 's', raw_data[3 + len_name + 2:3 + len_name + 2 + len_value])[0]. \
            decode('utf-8')
        bytes_read = 3 + len_name + 2 + len_value

    # reference: https://raw.githubusercontent.com/moxilo/mac-osx-forensics/master/cups_ipp.py
    if attr_name == 'printer-uri':
        result.append("URI            : {}".format(attr_value))
    elif attr_name == 'job-uuid':
        result.append("Job ID         : {}".format(attr_value))
    elif attr_name == 'copies':
        result.append("Copies         : {}".format(attr_value))
    elif attr_name == 'DestinationPrinterID':
        result.append("Printer ID     : {}".format(attr_value))
    elif attr_name == 'job-originating-user-name':
        result.append("User           : {}".format(attr_value))
    elif attr_name == 'job-name':
        result.append("Job name       : {}".format(attr_value))
    elif attr_name == 'document-format':
        result.append("Document format: {}".format(attr_value))
    elif attr_name == 'job-originating-host-name':
        result.append("Computer name  : {}".format(attr_value))
    elif attr_name == 'com.apple.print.JobInfo.PMApplicationName':
        result.append("Application    : {}".format(attr_value))
    elif attr_name == 'com.apple.print.JobInfo.PMJobOwner':
        result.append("Owner          : {}".format(attr_value))
    elif attr_name == 'date-time-at-creation':
        result.append("Creation Time  : {}".format(attr_value))
    elif attr_name == 'date-time-at-processing':
        result.append("Process Time   : {}".format(attr_value))
    elif attr_name == 'date-time-at-completed':
        result.append("Completed Time : {}".format(attr_value))
    elif attr_name == 'time-at-creation':
        result.append("Creation Time  : {}".format(get_time(attr_value)) + " (Local)")
    elif attr_name == 'time-at-processing':
        result.append("Process Time   : {}".format(get_time(attr_value)) + " (Local)")
    elif attr_name == 'time-at-completed':
        result.append("Completed Time : {}".format(get_time(attr_value)) + " (Local)")

    return bytes_read


def get_time(epoch):
    return datetime.datetime.fromtimestamp(float(epoch)).strftime('%Y-%m-%d %H:%M:%S')


result = []

parser = argparse.ArgumentParser(description="Parse IPP Control file")
parser.add_argument('raw', metavar='ipp', type=str, nargs=1, help="specify path to IPP control file")
args = parser.parse_args()

with open(args.raw[0], 'rb') as raw_alias:
    file_content = raw_alias.read()
    parse(file_content)
print('\r\n'.join(result))
