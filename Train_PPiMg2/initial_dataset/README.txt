				TOT

rep1  -> 44  configurations 	44
rep2  -> 82  configurations  	126
rep3  -> 214 configurations	340  corrupted (WARNING CP2K: atom closer than 0.5 A)
rep4  -> 204 configurations	504  corrupted (WARNING CP2K: atom closer than 0.5 A)
rep5  -> 203 configurations	707  corrupted (WARNING CP2K: atom closer than 0.5 A)
rep6  -> 201 configurations 	908  corrupted (WARNING CP2K: atom closer than 0.5 A)
rep7  -> 187 configurations	1095 corrupted (WARNING CP2K: atom closer than 0.5 A)
rep8  -> 189 configurations	1284 corrupted (WARNING CP2K: atom closer than 0.5 A)
rep9  -  476 configurations     646  not corrupted
rep10 -> 176 configurations     822  not corrupted
rep11 -> 166 configurations     988  not corrupted
rep12 -> 170 configurations	1058 not corrupted
rep13 -> 209 configurations	1267 not corrupted

Corrupted structures refer to those whose structure was signaled as distorted by CP2K, whose convergence either failed or returned energy value far from the labelled one for the non-distorted structure. Thus, such strcutures has been excluded from the dataset

To Adrian:

The Train_PPiMg ontains several 'repX' folder with X={1,2,3,4,5,6,9,10,11,12,13}. Each of the 'repX' folder contains some .txt files which are not of our interest, but ar eobtained by a general script devoted to extract energies. There are then two inputs file that are supposed to be the labelling inputs. I got them from arcann_users file and replaced, case by case, the sysname name, the rest of the scripts are exactly the same as arcann. Inside the folders you can also find two xyz files. The 'PPiMg2-opt-repX.xyz' represents the whole dynamics, while the Â'repX.xyz' is the extracted one obtained by loading the full on vmd and extracting a structure each n intervals. The input of the dynamic is inside the folder as well, named after the rep as 'PPiMg2-MD-repX.inp'. 
Moreover, the executable are working, yu can open and read them, but I guess they're pretty self-explicative by their name. Check_convergence.sh checks each subfolder of repX for the convergence of the labeling calculation, and returns a set of files where are listed the absolute paths of converged, not converged, skipped and error files.
The structure of the repX folders is the very same of Arcann's labelling ones, inside there are the inputs adapted to the specific calculation, the geometry, obtained by the extraction with 'generate.sh' of the configuration from the reduced trajectory. The 'generate.sh' script I got it from the validation one of yours, check it, but I'm pretty sure it works fine. Le tme know about any doubt, and ofc you can reach me whenever.

TO ADRIAN (UPDATE):
The issue is now fixed. The suggestion of Inaki to redo the extraction using a script worked. Indeed, vmd cuts some decimal digits, generating a shitt in the position of the arom, thus rendering a displacement error / low distance error. 
"new_rep" has the same framework as the previous one described, but this time calculations are converging. Yuppi	
