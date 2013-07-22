#!/usr/bin/env python
from glob import glob
from os import makedirs, getcwd, remove
from shutil import rmtree
from subprocess import call
import sys
import zipfile
from readroi import salva_img_crop_rois

curdir = getcwd()
imagejdir = 'your_ImageJ_dir'
roi_count = 0

# monta a macro
try:
    limiar = int(sys.argv[1])
    str_limiar = 'setThreshold(0, %d);\n' % limiar
except:
    #limiar =112
    str_limiar = ''
    
macro = """run("Image Sequence...", "open=[%s/tmp/]  increment=1 scale=100 file=[] or=[] sort");
run("8-bit");
"""
macro = macro + str_limiar
macro = macro + """run("Make Binary", "method=Default background=Default thresholded remaining black");
run("Analyze Particles...", "size=0-Infinity circularity=0.00-1.00 show=Nothing display include record add in_situ stack");
saveAs("Results", "Results.xls");
roiManager("Save", "RoiSet.zip");
run("Quit");
"""

def try_int(s):
    "Convert to integer if possible."
    try: return int(s)
    except: return s

def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))

def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))

def natcasecmp(a, b):
    "Natural string comparison, ignores case."
    return natcmp(a.lower(), b.lower())

def natsort(seq, cmp=natcmp):
    "In-place natural string sort."
    seq.sort(cmp)

def natsorted(seq, cmp=natcmp):
    "Returns a copy of seq, sorted by natural string sort."
    import copy
    temp = copy.copy(seq)
    natsort(temp, cmp)
    return temp

def executaImageJ(chunk):
    
    global roi_count

    # move arquivos para dir temp.
    for arq in chunk:
        f1 = open(arq, 'r')
        f2 = open('tmp/'+arq, 'w')
        f2.write(f1.read())
        f2.close()
        f1.close()    
        
    # salva a macro
    cmd = macro % (curdir)
    fm = open('macro.ijm', 'w')
    fm.write(cmd)
    fm.close()
    
    # executa ImageJ
    sr = ['']
    call([imagejdir, '-macro', curdir+'/macro.ijm'])            
    fr = open('Results.xls', 'r')
    sr = fr.readlines()
    fr.close()
    
    zf = zipfile.ZipFile('RoiSet.zip', 'r')
                
    # ajusta rois
    rois = []
    for filename in zf.namelist():
        roi_count +=1
        campos = filename.split('-')
        imagem = chunk[int(campos[0])-1]
        data = zf.read(filename)
        str_roi = '%s-%04d.roi' % (imagem, roi_count)
        rois.append(str_roi)
        froi = open('rois/'+str_roi, 'w')
        froi.write(data)
        froi.close()
    #ajusta resultados
    for numero_linha, linha in enumerate(sr[1:]):
        campos = linha.split('\t')
        ind = int(campos[0])-1
        campos[0] =  rois[ind]
        ind = int(campos[27])-1
        campos[27] = chunk[ind]
        sr[numero_linha+1] = '\t'.join(campos)
    return ''.join(sr[1:])

arquivos = glob('*.jpg')
arquivos = natsorted(arquivos)
results = """   Area	Mean	StdDev	Mode	Min	Max	X	Y	XM	YM	Perim.	BX	BY	Width	Height	Major	Minor	Angle	Circ.	Feret	
"""
try:
    rmtree('rois')
except:
    pass
makedirs('rois')


try:
    rmtree('tmp')
except:
    pass
makedirs('tmp')


for chunk in [arquivos[n:n+50] for n in range(0,len(arquivos),50)]:
        
    #executa imageJ
    results = results + executaImageJ(chunk)
    rmtree('tmp')
    makedirs('tmp')        
    
fr = open('Results.xls', 'w')
fr.write(results)
fr.close()
rmtree('tmp')
remove('macro.ijm')
remove('RoiSet.zip')

try:
    rmtree('roiimgs')
except:
    pass

makedirs('roiimgs') 

for image in glob('*.jpg'):
    salva_img_crop_rois(image)
