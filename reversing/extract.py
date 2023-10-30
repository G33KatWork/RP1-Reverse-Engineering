#!/usr/bin/env python3

import sys
import struct

VALID_IMAGE_SIZES = [512 * 1024, 2 * 1024 * 1024]

MAGIC = 0x55aaf00f
PAD_MAGIC = 0x55aafeef
MAGIC_MASK = 0xfffff00f
FILE_MAGIC = 0x55aaf11f # id for modifiable files
FILE_HDR_LEN = 20
FILENAME_LEN = 12
TEMP_DIR = None

# Modifiable files are stored in a single 4K erasable sector.
# The max content 4076 bytes because of the file header.
ERASE_ALIGN_SIZE = 4096
MAX_FILE_SIZE = ERASE_ALIGN_SIZE - FILE_HDR_LEN

DEBUG = True
def debug(s):
    if DEBUG:
        sys.stderr.write(s + '\n')

def exit_error(msg):
    """
    Trapped a fatal error, output message to stderr and exit with non-zero
    return code.
    """
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(1)

class ImageSection:
    def __init__(self, magic, offset, length, filename=''):
        self.magic = magic
        self.offset = offset
        self.length = length
        self.filename = filename
        debug("ImageSection %x offset %d length %d %s" % (magic, offset, length, filename))

class BootloaderImage(object):
    def __init__(self, filename, output=None):
        """
        Instantiates a Bootloader image writer with a source eeprom (filename)
        and optionally an output filename.
        """
        self._filename = filename
        self._sections = []
        self._image_size = 0
        try:
            self._bytes = bytearray(open(filename, 'rb').read())
        except IOError as err:
            exit_error("Failed to read \'%s\'\n%s\n" % (filename, str(err)))
        self._out = None
        if output is not None:
            self._out = open(output, 'wb')

        self._image_size = len(self._bytes)
        if self._image_size not in VALID_IMAGE_SIZES:
            exit_error("%s: Expected size %d bytes actual size %d bytes" %
                       (filename, self._image_size, len(self._bytes)))
        self.parse()

    def parse(self):
        """
        Builds a table of offsets to the different sections in the EEPROM.
        """
        offset = 0
        magic = 0
        while offset < self._image_size:
            magic, length = struct.unpack_from('>LL', self._bytes, offset)
            if magic == 0x0 or magic == 0xffffffff:
                break # EOF
            elif (magic & MAGIC_MASK) != MAGIC:
                raise Exception('EEPROM is corrupted %x %x %x' % (magic, magic & MAGIC_MASK, MAGIC))

            filename = ''
            if magic == FILE_MAGIC: # Found a file
                # Discard trailing null characters used to pad filename
                filename = self._bytes[offset + 8: offset + FILE_HDR_LEN].decode('utf-8').replace('\0', '')
            else:
                filename = f"{offset}.bin"
            debug("section at %d length %d magic %08x %s" % (offset, length, magic, filename))
            self._sections.append(ImageSection(magic, offset, length, filename))

            offset += 8 + length # length + type
            offset = (offset + 7) & ~7

    def find_file(self, filename):
        """
        Returns the offset, length and whether this is the last section in the
        EEPROM for a modifiable file within the image.
        """
        offset = -1
        length = -1
        is_last = False

        next_offset = self._image_size - ERASE_ALIGN_SIZE # Don't create padding inside the bootloader scratch page
        for i in range(0, len(self._sections)):
            s = self._sections[i]
            #if s.magic == FILE_MAGIC and s.filename == filename:
            if s.filename == filename:
                is_last = (i == len(self._sections) - 1)
                offset = s.offset
                length = s.length
                break

        # Find the start of the next non padding section
        i += 1
        while i < len(self._sections):
            if self._sections[i].magic == PAD_MAGIC:
                i += 1
            else:
                next_offset = self._sections[i].offset
                break
        ret = (offset, length, is_last, next_offset)
        debug('%s offset %d length %d is-last %d next %d' % (filename, ret[0], ret[1], ret[2], ret[3]))
        return ret

    def update(self, src_bytes, dst_filename):
        """
        Replaces a modifiable file with specified byte array.
        """
        hdr_offset, length, is_last, next_offset = self.find_file(dst_filename)
        update_len = len(src_bytes) + FILE_HDR_LEN

        if hdr_offset + update_len > self._image_size - ERASE_ALIGN_SIZE:
            raise Exception('No space available - image past EOF.')

        if hdr_offset < 0:
            raise Exception('Update target %s not found' % dst_filename)

        if hdr_offset + update_len > next_offset:
            raise Exception('Update %d bytes is larger than section size %d' % (update_len, next_offset - hdr_offset))

        new_len = len(src_bytes) + FILENAME_LEN + 4
        struct.pack_into('>L', self._bytes, hdr_offset + 4, new_len)
        struct.pack_into(("%ds" % len(src_bytes)), self._bytes,
                         hdr_offset + 4 + FILE_HDR_LEN, src_bytes)

        # If the new file is smaller than the old file then set any old
        # data which is now unused to all ones (erase value)
        pad_start = hdr_offset + 4 + FILE_HDR_LEN + len(src_bytes)

        # Add padding up to 8-byte boundary
        while pad_start % 8 != 0:
            struct.pack_into('B', self._bytes, pad_start, 0xff)
            pad_start += 1

        # Create a padding section unless the padding size is smaller than the
        # size of a section head. Padding is allowed in the last section but
        # by convention bootconf.txt is the last section and there's no need to
        # pad to the end of the sector. This also ensures that the loopback
        # config read/write tests produce identical binaries.
        pad_bytes = next_offset - pad_start
        if pad_bytes > 8 and not is_last:
            pad_bytes -= 8
            struct.pack_into('>i', self._bytes, pad_start, PAD_MAGIC)
            pad_start += 4
            struct.pack_into('>i', self._bytes, pad_start, pad_bytes)
            pad_start += 4

        debug("pad %d" % pad_bytes)
        pad = 0
        while pad < pad_bytes:
            struct.pack_into('B', self._bytes, pad_start + pad, 0xff)
            pad = pad + 1

    def update_key(self, src_pem, dst_filename):
        """
        Replaces the specified public key entry with the public key values extracted
        from the source PEM file.
        """
        pubkey_bytes = pemtobin(src_pem)
        self.update(pubkey_bytes, dst_filename)

    def update_file(self, src_filename, dst_filename):
        """
        Replaces the contents of dst_filename in the EEPROM with the contents of src_file.
        """
        src_bytes = open(src_filename, 'rb').read()
        if len(src_bytes) > MAX_FILE_SIZE:
            raise Exception("src file %s is too large (%d bytes). The maximum size is %d bytes."
                            % (src_filename, len(src_bytes), MAX_FILE_SIZE))
        self.update(src_bytes, dst_filename)

    def write(self):
        """
        Writes the updated EEPROM image to stdout or the specified output file.
        """
        if self._out is not None:
            self._out.write(self._bytes)
            self._out.close()
        else:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(self._bytes)
            else:
                sys.stdout.write(self._bytes)

    def get_file(self, filename):
        hdr_offset, length, is_last, next_offset = self.find_file(filename)
        offset = hdr_offset + 4 + FILE_HDR_LEN
        file_bytes = self._bytes[offset:offset+length-FILENAME_LEN-4]
        return file_bytes

    def extract_files(self):
        for i in range(0, len(self._sections)):
            s = self._sections[i]
            #if s.magic == FILE_MAGIC:
            if True:
                file_bytes = self.get_file(s.filename)
                open(s.filename, 'wb').write(file_bytes)

    def read(self):
        config_bytes = self.get_file('bootconf.txt')
        if self._out is not None:
            self._out.write(config_bytes)
            self._out.close()
        else:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(config_bytes)
            else:
                sys.stdout.write(config_bytes)

def main():
    i = BootloaderImage(sys.argv[1])
    i.extract_files()
    
    #for s in i._sections:
    #    if s.magic != PAD_MAGIC and s.magic != FILE_MAGIC:
    #        print("section", s)

if __name__ == "__main__":
    main()
