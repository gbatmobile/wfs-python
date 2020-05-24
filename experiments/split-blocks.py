import sys

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
	struct['endTimeStamp'] = decodeTimeStamp(int.from_bytes(descBytes[16:20], byteorder='little'))
	struct['lenLastBlock'] = int.from_bytes(descBytes[20:24], byteorder='little')
	struct['beginBlock'] = int.from_bytes(descBytes[24:28], byteorder='little')
	struct['camera'] = int.from_bytes(descBytes[30:31], byteorder='little')
	return struct

def genFileWithBlocks(numFile, blockDesc, descStruct):
	outFile = dirFile+"\\blocks\\"+\
				"{0:04x}-{1}-{2}-{3:02d}".format(	numFile,
													descStruct['begTimeStamp'],
													descStruct['endTimeStamp'],
													descStruct['camera'])
	print ("criando ", outFile+".txt")
	fdoutBlkDesc = open(outFile+".txt", "w")
	fdoutBlkDesc.write("{0:04x} ({1:10x} -> {1:12d}) {2:02x} -> {3}\n".format
				(numFile, numFile*0x200000 + 0x640000,
				int.from_bytes(readBlockSalt(numFile), byteorder='little'),
				[hex(x) for x in blockDesc]))

	fdoutBlk = open(outFile+".h264", "wb")
	fdoutBlk.write(readBlock(numFile))
	
	nextBlock = descStruct['nextBlock']
	while nextBlock != 0:
		blockData = readBlock(nextBlock)
		blockDesc = readBlockDesc(nextBlock)
		descStruct = decodeBlockStructure (blockDesc)
		lastBlock = int.from_bytes(readBlockSalt(nextBlock), byteorder='little')
		fdoutBlkDesc.write("{0:04x} ({1:10x} -> {1:12d}) {2:02x} {3:10x}-> {4}\n".format
				(nextBlock, nextBlock*0x200000 + 0x640000,
				lastBlock,
				descStruct['lenLastBlock'],
				[hex(x) for x in blockDesc]))
		print(descStruct['lenLastBlock'])
		if descStruct['nextBlock'] == 0:
			lastPos = 0x2000*(lastBlock+1)
			
			fdoutBlk.write(blockData[0:descStruct['lenLastBlock']])
		else:
			fdoutBlk.write(blockData)
		nextBlock = descStruct['nextBlock']
	fdoutBlkDesc.close()
	fdoutBlk.close()
	
def readBlockDesc(nBlock):
	fdin.seek (0x17600 + 0x20*nBlock)
	return fdin.read(0x20)

def readBlockSalt(nBlock):
	fdin.seek (0x620000 + nBlock)
	return fdin.read(0x1)

def readBlock(nBlock):
	fdin.seek (0x40000 + 0x200000*(nBlock+3))
	return fdin.read(0x200000)


if len(sys.argv) == 1:
	print ("uso: python ", sys.argv[0], " #arqInicial [#arqFinal]")
	print ("\t Numeros em hexa, usar 0x antes")
	print ("\t Para recuperar todos, usar: ")
	print ("\t\tpython ", sys.argv[0], "0x0")
	
	sys.exit(1)
elif len(sys.argv) == 2:
	numFile = int(sys.argv[1],16)
	lastFile = 0xDF90
elif len(sys.argv) == 3:
	numFile = int(sys.argv[1], 16)
	lastFile = int(sys.argv[2], 16)

dirFile = r"C:\home\galileu.gbs\Projetos\WFS"
inFile = r"\disco_50gb.img"
fdin = open (dirFile+inFile, "rb")

while numFile <= lastFile:
	fileDesc = readBlockDesc(numFile)
	descStruct = decodeBlockStructure (fileDesc)
	if descStruct['attrib'] in [2, 3]:
		print ("Recuperando o arquivo ", hex(numFile))
		genFileWithBlocks(numFile, fileDesc, descStruct)
	numFile += 1

fdin.close()
