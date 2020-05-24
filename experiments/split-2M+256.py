def extractBits (numb, position, len):
	return (numb >> (position + 1 - len)) & ((1 << len) - 1)

def getBasicBlockAndCamera (block):
	fdin.seek(0x17600 + 0x20 * (block-BASE))
	desc = fdin.read(0x20)
	attrib = int.from_bytes(desc[1:2], byteorder='little')
	if attrib == 2 or attrib == 3:
		numblock = 0
	else:
		numblock = int.from_bytes(desc[2:4], byteorder='little')
	camera = int.from_bytes(desc[30:31], byteorder='little')
	basicBlock = int.from_bytes(desc[24:28], byteorder='little')
	return (camera, basicBlock, numblock)
	
def getTimeStamp(block):
	fdin.seek(0x17600 + 0x20 * (block-BASE))
	desc = fdin.read(0x20)
	
	tsb = int.from_bytes(desc[12:16], byteorder='little')
	ts_begin = "20{0:02d}-{1:02d}-{2:02d}-{3:02d}-{4:02d}-{5:02d}".format(
				extractBits(tsb, 31, 6),
				extractBits(tsb, 25, 4),
				extractBits(tsb, 21, 5),
				extractBits(tsb, 16, 5),
				extractBits(tsb, 11, 6),
				extractBits(tsb,  5, 6))
	tse = int.from_bytes(desc[16:20], byteorder='little')
	ts_end = "20{0:02d}-{1:02d}-{2:02d}-{3:02d}-{4:02d}-{5:02d}".format(
				extractBits(tse, 31, 6),
				extractBits(tse, 25, 4),
				extractBits(tse, 21, 5),
				extractBits(tse, 16, 5),
				extractBits(tse, 11, 6),
				extractBits(tse,  5, 6))
	return (ts_begin, ts_end)
				

dirfile = r"C:\home\galileu.gbs\Projetos\WFS"
outdir = dirfile + r"\split"
infile = r"\disco_50gb.img"
fdin = open (dirfile+infile, "rb")

BASE = 0
block = 0x49
fdin.seek(0x200000*block + 0x240000)
buffer = fdin.read(0x200000)

while buffer != '':
	(tsbeg, tsend) = getTimeStamp(block)
	camera, basicBlock, numblock = getBasicBlockAndCamera(block)
	outfile = "{0}\\{1}-{2:06x}-{3:06x}_{4:04d}-{5}-{6}_{7}.h264".format(outdir, infile, 
									basicBlock, block, numblock, camera, tsbeg, tsend)
	print ("criando ", outfile)	
	fdout = open(outfile, "wb")
	fdout.write(buffer)
	fdout.close()
	block += 1
	fdin.seek(0x200000*(block-BASE) + 0x240000)
	buffer = fdin.read(0x200000)
	
fdin.close()