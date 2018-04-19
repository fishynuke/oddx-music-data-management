#include<iostream>
#include<cstdio>
#include<cstdlib>
#include<cstring>
using namespace std;

const char* diffname[] = { "SPNORMAL", "SPHYPER", "SPANOTHER", "DPNORMAL", "DPHYPER", "DPANOTHER", "BEGINNER" };
const char* vername[] = { "1st style", "substream", "2nd style", "3rd style", "4th style", "5th style",
						"6th style", "7th style", "8th style", "9th style", "10th style", "IIDX RED",
						"HAPPY SKY", "DistorteD", "GOLD", "DJ TROOPERS", "EMPRESS", "SIRIUS", "Resort Anthem",
						"Lincle", "tricoro", "SPADA", "PENDUAL", "copula" ,"SINOBUZ"};
char sBuf[1024];	//File buffer
char sBuf2[1024];	//File buffer
const int blk = 64;	//Blocksize

int num_correct(int n) {
	return n < 0 ? 128 + n + 1 + 127 : n;
}
int num_correct2(int n) {
	return n > 32767 ? n - 65536 : n;
}

int main() {
	FILE *fpin = NULL, *fpout = NULL;
	bool run = true;
	char c = '1', fname[15], infobuf[blk], title[blk], talias[blk], genre[blk], artist[blk], bganame[36];
	short firstline[16], slot[2];
	int totalsong, totalslot, counter = 1, *songid, font, version, others, diff[7], musicid, vol, bgadelay;
	cout << "IIDX Music Data Dump Tool\n";
	cout << "Place me in /data/info/ directory and run.\n\n";
	cout << "Please select which file to dump.\n";
	cout << "Default-music_omni.bin\t2-music_data.bin\n";
	if (c = getchar() == '2') {
		strcpy_s(fname, 15, "music_data.bin");
	}
	else {
		strcpy_s(fname, 15, "music_omni.bin");
	}
	fopen_s(&fpin, fname, "rb");
	if (fpin == NULL) {
		cout << "File Not Found!\n\n";
		run = false;
	}
	setvbuf(fpin, sBuf, _IOFBF, 1024);	//Set file buffer
	if (run) {
		fopen_s(&fpout, "music_dumped.txt", "w");
		setvbuf(fpout, sBuf2, _IOFBF, 1024);	//Set file buffer
		for (int i = 0; i < 16; i++) {	//Get first line
			firstline[i] = fgetc(fpin);
		}
		cout << "Dumping IIDX" << int(firstline[4]) << " music data.\n\n";	//IIDX version
		totalsong = firstline[9] * 16 * 16 + firstline[8];	//Calc total songs
		totalslot = firstline[11] * 16 * 16 + firstline[10];	//Calc total slots
		cout << "Total Songs: " << totalsong << "\tTotal ID Slots: " << totalslot << endl;
		fprintf(fpout, "Total Songs: %d\tTotal ID Slots: %d\n", totalsong, totalslot);
		songid = new int[totalsong];	//Hold song IDs
		songid[0] = 1000;	//Have to set the first song
		for (int i = 0; i < totalslot; i++) {	//Read slots
			slot[1] = fgetc(fpin);
			slot[0] = fgetc(fpin);
			if ((slot[0] == 255 && slot[1] == 255) || (slot[0] == 0 && slot[1] == 0)) {
				continue;	//If no song, skip
			}
			songid[counter] = i;	//Record ID
			counter++;
		}
		fprintf(fpout, "MusicID\tTitle\tAlias\tGenre\tArtist\tVersion\tSPNORMAL\tSPHYPER\tSPANOTHER\tDPNORMAL\tDPHYPER\tDPANOTHER\tBEGINNER\tVolume\tBGAdelay\tBGAname\tTitleFont\tOthersFolder\n");
		for (int i = 0; i < totalsong; i++) {	//Read song infos
			for (int j = 0; j < 13; j++) {	//13 info blocks
				int k = 0;
				for (k = 0; k < blk; k++) {	//Blocksize=64
					infobuf[k] = fgetc(fpin);
				}
				switch (j) {
				case 0: {	//Title
					for (k = 0; k < blk; k++) {
						if (infobuf[k] == 0) {
							break;
						}
						title[k] = infobuf[k];
					}
					title[k] = '\0';
					break;
				}
				case 1: {	//Title alias
					for (k = 0; k < blk; k++) {
						if (infobuf[k] == 0) {
							break;
						}
						talias[k] = infobuf[k];
					}
					talias[k] = '\0';
					break;
				}
				case 2: {	//Genre
					for (k = 0; k < blk; k++) {
						if (infobuf[k] == 0) {
							break;
						}
						genre[k] = infobuf[k];
					}
					genre[k] = '\0';
					break;
				}
				case 3: {	//Artist
					for (k = 0; k < blk; k++) {
						if (infobuf[k] == 0) {
							break;
						}
						artist[k] = infobuf[k];
					}
					artist[k] = '\0';
					break;
				}
				case 4: {	//Basic info
					font = infobuf[20];	//Title font No.
					version = infobuf[24];	//Song version
					others = infobuf[26];	//Others folder
					for (k = 0; k < 7; k++) {
						diff[k] = infobuf[32 + k];	//Difficulties
					}
					break;
				}
				case 7: {	//More info
					musicid = num_correct(infobuf[9]) * 16 * 16 + num_correct(infobuf[8]); //Music ID, should be the same as Song ID
					vol = num_correct(infobuf[12]);	//Music Volume
					bgadelay = num_correct2(num_correct(infobuf[25]) * 16 * 16 + num_correct(infobuf[24]));	//BGA Delay Time
					for (k = 28; k < blk; k++) {
						if (infobuf[k] == 0) {
							break;
						}
						bganame[k - 28] = infobuf[k];
					}
					bganame[k - 28] = '\0';
					break;
				}
				default: {
					//Do nothing
					break;
				}
				}
			}
			if (songid[i] != musicid) {
				cout << "Music ID Wrong! Title is: " << title << endl;
				cout << "Music ID Wrong! songid[] is: " << songid[i] << endl;
				cout << "Music ID Wrong! musicid is: " << musicid << endl;
			}
			fprintf(fpout, "%05d\t%s\t%s\t%s\t%s\t%s\t", musicid, title, talias, genre, artist, vername[version]);
			for (int k = 0; k < 7; k++) {
				fprintf(fpout, "%d\t", diff[k]);
			}
			fprintf(fpout, "%d\t%d\t%s\t%d\t", vol, bgadelay, bganame, font);
			fprintf(fpout, others ? "Yes\n" : "No\n");
			title[0] = '\0'; talias[0] = '\0'; genre[0] = '\0'; artist[0] = '\0'; bganame[0] = '\0';
			fflush(fpout);
		}
		delete[]songid;
		fclose(fpin);
		fclose(fpout);
		fpin = NULL;
		fpout = NULL;
		cout << "\nDump Complete!\n";
	}
	system("pause");
	return 0;
}
