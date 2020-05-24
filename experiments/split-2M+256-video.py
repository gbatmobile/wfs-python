def extractBits (numb, position, len):
	return (numb >> (position + 1 - len)) & ((1 << len) - 1)

def decodeTimeStamp(ts):
	return	"20{0:02d}-{1:02d}-{2:02d}-{3:02d}-{4:02d}-{5:02d}".format(
				extractBits(ts, 31, 6),
				extractBits(ts, 25, 4),
				extractBits(ts, 21, 5),
				extractBits(ts, 16, 5),
				extractBits(ts, 11, 6),
				extractBits(ts,  5, 6))

def decodeBlockStructure (descBytes):
	struct = {}
	struct['attrib'] = int.from_bytes(descBytes[1:2], byteorder='little')
	if struct['attrib'] == 2 or struct['attrib']  == 3:
		struct['numBlock'] = 0
		struct['totBlocks'] = int.from_bytes(descBytes[2:4], byteorder='little') + 1
	else:
		struct['numBlock'] = int.from_bytes(descBytes[2:4], byteorder='little')
	
	struct['prevBlock'] = int.from_bytes(descBytes[4:8], byteorder='little')
	struct['nextBlock'] = int.from_bytes(descBytes[8:12], byteorder='little')
	struct['begTimeStamp'] = decodeTimeStamp(int.from_bytes(descBytes[12:16], byteorder='little'))
	struct['endTimeStamp'] = decodeTimeStamp(int.from_bytes(descBytes[16:21], byteorder='little'))
	struct['beginBlock'] = int.from_bytes(descBytes[24:28], byteorder='little')
	struct['camera'] = int.from_bytes(descBytes[31:32], byteorder='little')
	return struct
	
def genFileWithBlocks(numblock, descStruct):
	print ("criando ", outfile)	
	fdout = open(dirFile+"\\blocks\\"+
				"{0:04x}-{1:0x04x}-{2:02d}".format(	numBlock, 
													descStruct['totBlocks'],
													descStruct['camera'])
				".txt", "w")
	fdout.write(numBlock)
	
	nextBlock = descStruct['nextBlock']
	while nextBlock != 0:
		fdout.write(nextBlock)
		descStruct = decodeBlockStructure (readBlock(nextBlock))
		nextBlock = descStruct['nextBlock']
	fdout.close()
		
def readBlock(nBlock):
	fdin.seek (0x17600 + 0x20*nBlock)
	return fdin.read(0x20)


dirFile = r"C:\home\galileu.gbs\Projetos\WFS"
inFile = r"\disco_50gb.img"
fdin = open (dirFile+inFile, "rb")


numBlock = 0
while numBlock < 0xDF80:
	descStruct = decodeBlockStructure (readBlock(numBlock))
	if descStruct['attrib'] in [2, 3]:
		genFileWithBlocks(numBlock, descStruct)
	numBlock += 1

fdin.close()