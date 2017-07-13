# JPG files: How do the work?
#
# The file will start with a SOI (Start of Image) Marker [FF D8]
# It will contain "headers" that start with [FF XX] where XX cannot be [00] or [FF]
# The next two bytes after a header are a 16 bit length of the header section
# this length includes the length bits  in the total length, but not the Marker start
# These header sections are called Markers/Marker Segments
# There is a special Marker comes after the other Markers "SOS" (Start Of Stream) [FF DA]
# the compression stream is of unknown length and may contain other "Restart" Markers within it
# any marker in the stream that is not the EOI (End of Image) Marker [FF D9] may be ignored
# the EOI Marker looks like it can be contained in the headers and is a false marker

# In this program we scan over a file containing jpg files looking for the start of a file
# After finding a SOI we loop over Marker segments until we find a valid SOS
# then we look for a valid EOI, print the file and begin again

import os

file_number = 1  # for naming the files (one indexed to line up with pdfminer outputs
iteration_placeholder = 0  # keeps track of our last position in the file

file = open("Thornwatch.pdf", "rb")
f = file.read()

try:
    os.mkdir("Images")
except OSError:
    pass  # can't recreate

while True:
    in_stream = False

    SOI = f.find(b'\xff\xd8', iteration_placeholder)

    # this means we've looped around (SOI<Placeholder) or there were no jpg files (-1)
    if SOI < iteration_placeholder:
        print("No files found after ", iteration_placeholder)
        break
    else:
        print("Image found: %s %s at %d " % (hex(f[SOI]), hex(f[SOI+1]), SOI))

    # start looking just past the marker on the XX [FF D8 XX]
    iteration_placeholder = SOI + 2

    while True:
        # Look for a [FF]
        # marker_byte is the position of the byte f[marker_byte_0] is the value
        marker_byte_0 = f.find(b'\xff', iteration_placeholder)
        if marker_byte_0 == -1:
            print("No more segments")
            break
        elif marker_byte_0 != iteration_placeholder:
            # Segments start back to back if we found [FF] deeper in the file then we are missing something
            # This seems like we could always search the byte right after the start, but if the file randomly has
            # [FF D8 FF Junk] we just want to log this as a false positive and reset tot the next time we find FF
            print("Invalid Marker Segment - not really jpg Look for new Image at ", marker_byte_0)
            # print(''.join(format(x, ' 02x') for x in f[SOI:marker_byte_0]))
            iteration_placeholder = f.find(b'\xff', marker_byte_0)
            break

        # grab the next byte
        marker_byte_1 = marker_byte_0+1

        if f[marker_byte_1] == 218:  # b'\xDA'
            # FF DA is the SOS which we were hoping to find
            print("Stream found: %s %s at %d " % (hex(f[marker_byte_0]), hex(f[marker_byte_1]), marker_byte_0))
            in_stream = True
            break
        elif f[marker_byte_1] == b'\x00' or f[marker_byte_1] == b'\xff':
            print('Invalid Segment - Markers can not have 00 or FF as the second byte')
            break
        elif f[marker_byte_1] == 217:
            print("EOI - You messed up", marker_byte_1)  # b'\xd9'
            # This would mean we are found an EOF before the SOS
            in_stream = False
            break
        elif 208 <= f[marker_byte_1] <= 215:  # b'\xD0'-b'\xD7'
            # This would be a restart marker without a SOS
            print("Restart marker -  You messed up")
            break

        # At this point we know we have a valid segment start, lets get the length and end position
        marker_byte_length_1 = marker_byte_0+2
        marker_byte_length_2 = marker_byte_0+3
        segment_length = f[marker_byte_length_1:marker_byte_length_2+1]
        segment_length_i = int.from_bytes(segment_length, 'big')
        # The length bytes are included in the overall length
        segment_end = marker_byte_length_1 + segment_length_i

        # really useful for debugging, probably too much output for most people
        print("Segment Found: %s %s %s %s at %d with length %d ending %d" % (hex(f[marker_byte_0]), hex(f[marker_byte_1])
              , hex(f[marker_byte_length_1]), hex(f[marker_byte_length_2]), marker_byte_0, segment_length_i,
              segment_end))

        iteration_placeholder = segment_end

    if in_stream:
        # Finally in a compression stream, find the end of file
        EOI = f.find(b'\xff\xd9', marker_byte_0)
        print("End of Stream: %s %s at %d " % (hex(f[EOI]), hex(f[EOI + 1]), EOI))

        iteration_placeholder = EOI
        jpg = f[SOI:EOI]

        # pathlib.Path('/Images').mkdir(parents=False, exist_ok=True)
        jpg_file = open("Images/Im%d.jpg" % file_number, "wb")
        jpg_file.write(jpg)
        jpg_file.close()
        print("Printing Im%d.jpg" % file_number)

        file_number += 1


