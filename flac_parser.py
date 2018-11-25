#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import operations_with_os as owo
import sys

class Parser():
    def __init__(self, flac_bytes, save_pic):
        self.bytes = flac_bytes
        self.picture_exist = False
        self.save_pic = save_pic
        self.result_dict = {}
        self.pointer = 0

    def parse_flac(self):
        self.parse_metadata_blocks()

    def parse_metadata_blocks(self):
        is_ended = 0
        while(not is_ended):
            current_header = self.bytes[self.pointer:self.pointer + 4]
            is_ended = current_header[0] >> 7
            type_of_block = current_header[0] & 127
            length_of_block = int.from_bytes(current_header[-3:],
                                               byteorder='big')

            if type_of_block == 0:
                self.parse_streaminfo_block(length_of_block)

            if type_of_block == 1:
                self.parse_padding_block(length_of_block)

            if type_of_block == 2:
                self.parse_application_block(length_of_block)

            if type_of_block == 3:
                self.parse_seektable_block(length_of_block)

            if type_of_block == 4:
                self.parse_vorbis_comment(length_of_block)

            if type_of_block == 5:
                self.parse_cuesheet_block(length_of_block)

            if type_of_block == 6:
                self.picture_exist = True
                self.parse_picture_block(length_of_block)

            self.pointer += (length_of_block + 4)

    def parse_application_block(self, length_of_block):
        pass

    def parse_cuesheet_block(self, length_of_block):
        pass

    def parse_picture_block(self, length_of_block):
        self.picture_description = {'Picture type':4,
                                    'MIME type':4,
                                    'Description':4,
                                    'Width':4,
                                    'Height':4,
                                    'Color depth':4,
                                    'Number of used colors':4,
                                    'Picture bytes':4}

        local_pointer = self.pointer + 4

        for key in self.picture_description.keys():
            section_length = self.picture_description[key]
            value = self.bytes[local_pointer:local_pointer + section_length]
            value = int.from_bytes(value, byteorder='big')
            local_pointer += section_length
            if key in ['MIME type', 'Description', 'Picture bytes']:
                length = value
                value = bytearray(self.bytes[local_pointer:local_pointer + value])
                local_pointer += length

                if key in ['MIME type', 'Description']:
                    value = value.decode('utf-8')
                
                else:
                    self.get_pic_name()
                    self.pic_bytes = value
                    if self.save_pic:
                        owo.write_bytes_to_file(value, self.pic_name)

            if not key == 'Picture bytes':
                self.picture_description[key] = value

        self.result_dict['Picture info'] = self.picture_description

    def parse_seektable_block(self, length_of_block):
        pass

    def parse_vorbis_comment(self, length_of_block):
        self.vorbis_tags = {}

        local_pointer = self.pointer + 4
        vendor_length =  int.from_bytes(self.bytes[local_pointer:local_pointer + 4],
                                               byteorder='little')
        local_pointer += 4
        vendor = self.bytes[local_pointer:local_pointer + vendor_length].decode('utf-8')

        local_pointer += vendor_length
        count_of_tags = int.from_bytes(self.bytes[local_pointer:local_pointer + 4],
                                               byteorder='little')

        local_pointer += 4
        for _ in range(count_of_tags):
            length_of_tag = int.from_bytes(self.bytes[local_pointer:local_pointer + 4],
                                               byteorder='little')
            local_pointer += 4

            row_tag = self.bytes[local_pointer:local_pointer + length_of_tag].decode('utf-8')
            tag = row_tag.split('=')
            self.vorbis_tags[tag[0]] = tag[1]

            local_pointer += length_of_tag

        print(vendor)
        print(self.vorbis_tags)
        self.result_dict['Vorbis comments'] = self.vorbis_tags

    def parse_streaminfo_block(self, length_of_block):
        self.streaminfo_dict = {'Minimum block size':16,
                                'Maximum block size':16,
                                'Minimum frame size':24,
                                'Maximum frame size':24,
                                'Sample rate in Hz`s':20,
                                'Count of channels':3,
                                'Bits per sample':5,
                                'Total count of samples':36,
                                'MD5 signature':128}

        bits_string = ''
        for byte in self.bytes[self.pointer + 4:self.pointer + length_of_block + 4]:
            bits_string += bin(byte)[2:].zfill(8)

        local_pointer = 0

        for key in self.streaminfo_dict.keys():
            end_of_range = local_pointer + self.streaminfo_dict[key]
            self.streaminfo_dict[key] = int(bits_string[local_pointer:end_of_range], base=2)
            local_pointer = end_of_range

        print(self.streaminfo_dict)
        self.result_dict['Stream info'] = self.streaminfo_dict

    def parse_padding_block(self, length_of_block):
        pass

    def get_pic_name(self):
        self.extension = self.picture_description['MIME type'].split('/')[1]
        self.pic_name = owo.get_free_name('picture.{}'.format(self.extension))


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--method')
    parser.add_argument('-f', '--flac')
    parser.add_argument('-sp', '--save_pic', default=False, action='store_true')

    return parser


if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    if (namespace.method == 'parse_flac'):
        bytes = owo.read_bytes_from_file(namespace.flac)
        if bytes[:4] == b'fLaC':
            parser = Parser(bytes[4:], namespace.save_pic)
            parser.parse_flac()

        else:
            print('Gived file is not flac')
