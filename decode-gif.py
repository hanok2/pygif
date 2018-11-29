#!/usr/bin/python3

import gif
import sys

if len (sys.argv) < 2:
    exit (1)

r = gif.Reader ()
r.feed (open (sys.argv[1], 'rb').read ())

if not r.has_header () or not r.is_gif ():
    print ('Not a GIF')
    exit ()

if not r.has_screen_descriptor ():
    print ('Too short')
    exit ()

def color_to_string (color):
    (red, green, blue) = color
    return '#%02x%02x%02x' % (red, green, blue)

def get_color (color_table, index):
    if 0 <= index < len (color_table):
        return color_to_string (color_table[index])
    else:
        return 'INVALID'

def color_table_to_string (color_table):
    colors = []
    for color in r.color_table:
        colors.append (color_to_string (color))
    return ', '.join (colors)

def get_disposal_method_string (disposal_method):
    if disposal_method == 0:
        return 'none'
    elif disposal_method == 1:
        return 'keep'
    elif disposal_method == 2:
        return 'restore background'
    elif disposal_method == 3:
        return 'restore previous'
    else:
        return str (disposal_method)

print ('Size: %dx%d pixels' % (r.width, r.height))
print ('Original Depth: %d bits' % r.original_depth)
if r.pixel_aspect_ratio != 0:
    print ('Pixel Aspect Ratio: %d' % r.pixel_aspect_ratio)
if len (r.color_table) > 0:
    description = '%d' % len (r.color_table)
    if r.color_table_sorted:
        description += ', sorted'
    print ('Colors (%s): %s' % (description, color_table_to_string (r.color_table)))
    print ('Background Color: %s (%d)' % (get_color (r.color_table, r.background_color), r.background_color))

for block in r.blocks:
    if isinstance (block, gif.Image):
        print ('Image:')
        if (block.left, block.top) != (0, 0):
            print ('  Position: %d,%d' % (block.left, block.top))
        print ('  Size: %dx%d' % (block.width, block.height))
        if len (block.color_table) > 0:
            description = '%d' % len (block.color_table)
            if block.color_table_sorted:
                description += ', sorted'
            print ('  Colors (%s): %s' % (description, color_table_to_string (block.color_table)))
        decoder = block.decode_lzw ()
        clear_count = 0
        for code in decoder.codes[1:]:
            if code == decoder.clear_code:
                clear_count += 1
        description = '%d' % len (decoder.values)
        description += ', code-size=%d' % (block.lzw_min_code_size)
        if block.interlace:
            description += ', interlace'
        if clear_count > 0:
            description += ', n-clears=%d' % clear_count
        if decoder.codes[0] != decoder.clear_code:
            description += ', no-clear-at-start'
        if decoder.codes[-1] != decoder.eoi_code:
            description += ', no-end-of-information'
        print ('  Pixels (%s): %s' % (description, decoder.values))
        lzw_data = block.get_lzw_data ()
        if decoder.n_used < len (lzw_data):
            extra_data = lzw_data[decoder.n_used:]
            print ('  Unused data (%d): %s' % (len (extra_data), repr (extra_data)))

    elif isinstance (block, gif.PlainTextExtension):
        print ('Plain Text Extension:')
        print ('  Position: %d,%d' % (block.left, block.top))
        print ('  Grid Size: %dx%d' % (block.width, block.height))
        print ('  Cell Size: %dx%d pixels' % (block.cell_width, block.cell_height))
        print ('  Foreground Color: %s (%d)' % (get_color (r.color_table, block.foreground_color), block.foreground_color))
        print ('  Background Color: %s (%d)' % (get_color (r.color_table, block.background_color), block.background_color))
        print ('  Text: %s' % repr (block.get_text ()))

    elif isinstance (block, gif.GraphicControlExtension):
        print ('Graphic Control Extension:')
        print ('  Delay Time: %d/100 ms' % block.delay_time)
        if block.has_transparent:
            print ('  Transparent Color: %d' % block.transparent_color)
        elif block.transparent_color != 0:
            print ('  Transparent Color: %d (!)' % block.transparent_color)
        print ('  Disposal Method: %s' % get_disposal_method_string (block.disposal_method))
        print ('  User Input: %s' % repr (block.user_input))

    elif isinstance (block, gif.CommentExtension):
        print ('Comment Extension:')
        print ('  Comment: %s' % repr (block.get_comment ()))

    elif isinstance (block, gif.NetscapeExtension):
        print ('Netscape Extension:')
        if block.loop_count is not None:
            print ('  Loop Count: %d' % block.loop_count)
        if block.buffer_size is not None:
            print ('  Buffer Size: %d' % block.buffer_size)
        for (id, data) in block.unused_subblocks:
            print ('  Sub-Block %d: %s' % (id, repr (data)))

    elif isinstance (block, gif.AnimationExtension):
        print ('Animation Extension:')
        if block.loop_count is not None:
            print ('  Loop Count: %d' % block.loop_count)
        if block.buffer_size is not None:
            print ('  Buffer Size: %d' % block.buffer_size)
        for (id, data) in block.unused_subblocks:
            print ('  Sub-Block %d: %s' % (id, repr (data)))

    elif isinstance (block, gif.XMPDataExtension):
        print ('XMP Data Extension:')
        print ('  Metadata: %s' % repr (block.get_metadata ()))

    elif isinstance (block, gif.ICCColorProfileExtension):
        print ('ICC Color Profile Extension:')
        print ('  ICC Profile: %s' % repr (block.get_icc_profile ()))

    elif isinstance (block, gif.ApplicationExtension):
        print ('Application Extension:')
        print ('  Application Identifier: %s' % repr (block.identifier))
        print ('  Application Authentication Code: %s' % repr (block.authentication_code))
        for block in block.get_data ():
            print ('  Data: %s' % repr (block))

    elif isinstance (block, gif.Extension):
        print ('Extension %d:' % block.label)
        for subblock in block.get_subblocks ():
            print ('  Data: %s' % repr (subblock))

    elif isinstance (block, gif.Trailer):
        pass

    else:
        print ('Unknown Block:')
        print ('  Data (%d): %s' % (block.length, repr (block.get_data ())))

if not r.is_complete ():
    print ('No trailer')
