diffname = ["SPNORMAL", "SPHYPER", "SPANOTHER", "DPNORMAL", "DPHYPER", "DPANOTHER", "BEGINNER"]
vername = ["1st style", "substream", "2nd style", "3rd style", "4th style", "5th style",
			"6th style", "7th style", "8th style", "9th style", "10th style", "IIDX RED",
			"HAPPY SKY", "DistorteD", "GOLD", "DJ TROOPERS", "EMPRESS", "SIRIUS", "Resort Anthem",
			"Lincle", "tricoro", "SPADA", "PENDUAL", "copula", "SINOBUZ", "CANNON BALLERS"]
blksize = 64
with open("music_data.bin", "rb") as f:
    byte = f.read(1)
    while byte:
        #if byte != b'\x00' and byte != b'\xff':
            #print(byte, end="")
        byte = f.read(1)