import argparse
import ccl_bplist
import construct
import plistlib

"""
An old version of yk_bmdata.py that makes use of construct library.
Limitation: Number of ToCs it can parse
"""

__author__ = 'yukai'

# to reduce code width
_ARRAY = construct.Array
_POINTER = construct.Pointer
_REPEAT = construct.RepeatUntil
_INT = construct.ULInt32('integer')
_INT64 = construct.ULInt64('integer64')

_BOOKMARK_DATA = construct.Struct(
    'bookmark_data',
    construct.String('magic', 4),
    construct.ULInt32('length'),
    construct.UBInt32('version'),
    construct.ULInt32('offset'),  # offset to "FirstToC Offset"
    _POINTER(lambda ctx: ctx.offset,
             construct.Struct(
                'ftoc_offset',
                construct.Anchor('abs_offset'),
                construct.ULInt32('offset'),
                _POINTER(lambda ctx: ctx.abs_offset + ctx.offset,
                         _REPEAT(lambda obj, ctx: obj.offset == 0x00000000,
                                 construct.Struct(
                                     'toc',
                                     construct.ULInt32('length'),
                                     construct.SLInt16('type'),
                                     construct.UBInt16('flag'),
                                     construct.ULInt32('level'),
                                     construct.ULInt32('offset'),  # offset to next ToC (0 if none)
                                     construct.ULInt32('count'),
                                     _ARRAY(lambda ctx: ctx.count,
                                            construct.Struct(
                                                'record',
                                                construct.ULInt16('type'),
                                                construct.ULInt16('flag'),
                                                construct.ULInt64('offset'),  # offset to data record
                                                _POINTER(lambda ctx: ctx._._.abs_offset + ctx.offset,
                                                         construct.Struct(
                                                             'data_record',
                                                             construct.ULInt32('length'),
                                                             construct.ULInt32('type'),
                                                             construct.Field('data', lambda ctx: ctx.length)))))))))))
_DATA = construct.Struct(
    'std_data',
    construct.ULInt32('length'),
    construct.ULInt32('type'),
    construct.Field('data', lambda ctx: ctx.length))


def parse():
    result = {}
    bookmark = _BOOKMARK_DATA.parse(raw_data)

    for table in bookmark.ftoc_offset.toc:
        for record in table.record:
            if record.type == 4100:  # pathComponents
                result['path'] = ''
                offsets = interpret(record.data_record, bookmark)  # obtain absolute offsets
                for offset in offsets:
                    path_component = _DATA.parse(raw_data[offset:])
                    result['path'] += '/' + path_component.data.decode('utf-8')
                print('filePath     : {}'.format(result['path']))

            elif record.type == 4101:  # fileIDs
                result['inodes'] = ''
                offsets = interpret(record.data_record, bookmark)  # obtain absolute offsets
                for offset in offsets:
                    inodes = _DATA.parse(raw_data[offset:])
                    result['inodes'] += '/' + str(_INT64.parse(inodes.data))
                print('inodePath    : {}'.format(result['inodes']))

            elif record.type == 4112:  # resourceProps
                print('resourceProps: {}'.format('?'))

            elif record.type == 4160:  # creationDate
                print('creationDate : {}'.format('?'))

            elif record.type == 8192:  # volInfoDepths
                print('volInfoDepths: {}'.format('?'))

            elif record.type == 8194:  # volPath
                result['volPath'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('volPath      : {}'.format(result['volPath']))

            elif record.type == 8197:  # volURL
                result['volURL'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('volURL       : {}'.format(result['volURL']))

            elif record.type == 8208:  # volName
                result['volName'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('volName      : {}'.format(result['volName']))

            elif record.type == 8209:  # volUUID
                result['volUUID'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('volUUID      : {}'.format(result['volUUID']))

            elif record.type == 8272:  # volMountURL
                print('volMountURL  : {}'.format('?'))

            elif record.type == 49169:  # user
                result['user'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('user         : {}'.format(result['user']))

            elif record.type == 61568:  # sandboxInfo
                result['sandbox'] = interpret(record.data_record, bookmark).decode('utf-8')
                print('sandboxInfo  : {}'.format(result['sandbox']))

            else:
                print('record type {} is currently unknown'.format(record.type))


def interpret(data_record, bookmark):
    count = data_record.length // 4
    if data_record.length % 4 > 0:
        count += 1

    if data_record.type == 1537:  # offsets
        offsets = []
        data = data_record.data
        for offset in range(count):
            offsets.append(bookmark.offset + _INT.parse(data))  # base offset + relative offset
            data = data[4:]
        return offsets

    if data_record.type == 257 or 513 or 2305:
        string_data = construct.String('string', data_record.length).parse(data_record.data)
        return string_data


def _debug():
    bookmark = _BOOKMARK_DATA.parse(raw_data)

    print('Magic           : {}'.format(bookmark.magic))
    print('Length          : {}'.format(bookmark.length))
    print('Version         : {}'.format(bookmark.version))
    print('Data Offset     : {}'.format(bookmark.offset))
    print('Absolute Offset : {}'.format(bookmark.ftoc_offset.abs_offset))
    print('First ToC Offset: {}'.format(bookmark.ftoc_offset.offset))

    for table in bookmark.ftoc_offset.toc:
        print('\t===== ToC =====')
        print('\tLength: {}'.format(table.length))
        print('\tType  : {}'.format(table.type))
        print('\tFlag  : {}'.format(table.flag))
        print('\tLevel : {}'.format(table.level))
        print('\tOffset: {}'.format(table.offset))
        print('\tCount : {}'.format(table.count))
        for record in table.record:
            print('\t\t===== Record =====')
            print('\t\tType  : {}'.format(record.type))
            print('\t\tFlag  : {}'.format(record.flag))
            print('\t\tOffset: {}'.format(record.offset))
        print('\t===== End of ToC =====')


parser = argparse.ArgumentParser(description='Parse bookmark data within plists')
parser.add_argument('plist_path', metavar='plist', type=str, nargs=1, help='specify path to plist file')
args = parser.parse_args()
raw_data = None

with open(args.plist_path[0], 'rb') as plist:
    try:
        pl = plistlib.load(plist)
    except ValueError:
        pl = ccl_bplist.load(plist)

    try:
        for item in pl["RecentDocuments"]["CustomListItems"]:
            raw_data = item['Bookmark']
            # _debug()
            parse()
            print('====================')
    except KeyError:
        pass
