import numpy as np
from glob import glob
import sys 
 
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

 
def read_roi(fileobj):
    '''
    points = read_roi(fileobj)
 
    Read ImageJ's ROI format
    '''
    # from the work of Luis Pedro Coelho <luis@luispedro.org>, 2012
    # https://gist.github.com/luispedro/3437255
 
 
    SPLINE_FIT = 1
    DOUBLE_HEADED = 2
    OUTLINE = 4
    OVERLAY_LABELS = 8
    OVERLAY_NAMES = 16
    OVERLAY_BACKGROUNDS = 32
    OVERLAY_BOLD = 64
    SUB_PIXEL_RESOLUTION = 128
    DRAW_OFFSET = 256
 
 
    pos = [4]
    def get8():
        pos[0] += 1
        s = fileobj.read(1)
        if not s:
            raise IOError('readroi: Unexpected EOF')
        return ord(s)
 
    def get16():
        b0 = get8()
        b1 = get8()
        return (b0 << 8) | b1
 
    def get32():
        s0 = get16()
        s1 = get16()
        return (s0 << 16) | s1
 
    def getfloat():
        v = np.int32(get32())
        return v.view(np.float32)
 
    magic = fileobj.read(4)
    if magic != 'Iout':
        raise IOError('Magic number not found')
    version = get16()
 
    # It seems that the roi type field occupies 2 Bytes, but only one is used
    roi_type = get8()
    # Discard second Byte:
    get8()
 
    if not (0 <= roi_type < 11):
        raise ValueError('roireader: ROI type %s not supported' % roi_type)
 
    if roi_type != 7:
        #raise ValueError('roireader: ROI type %s not supported (!= 7)' % roi_type)
        pass
 
    top = get16()
    left = get16()
    bottom = get16()
    right = get16()
    n_coordinates = get16()
 
    x1 = getfloat() 
    y1 = getfloat() 
    x2 = getfloat() 
    y2 = getfloat()
    stroke_width = get16()
    shape_roi_size = get32()
    stroke_color = get32()
    fill_color = get32()
    subtype = get16()
    if subtype != 0:
        raise ValueError('roireader: ROI subtype %s not supported (!= 0)' % subtype)
    options = get16()
    arrow_style = get8()
    arrow_head_size = get8()
    rect_arc_size = get16()
    position = get32()
    header2offset = get32()
 
    if options & SUB_PIXEL_RESOLUTION:
        getc = getfloat
        points = np.empty((n_coordinates, 2), dtype=np.float32)
    else:
        getc = get16
        points = np.empty((n_coordinates, 2), dtype=np.int16)
    points[:,1] = [getc() for i in xrange(n_coordinates)]
    points[:,0] = [getc() for i in xrange(n_coordinates)]
    points[:,1] += left
    points[:,0] += top
    points -= 1
    return points
                     
from PIL import Image, ImageDraw
from os import makedirs, getcwd, remove
from shutil import rmtree

def salva_img_crop_rois(image):

    arqs = glob('rois/'+image+'-*.roi')
    
    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    for arq in arqs:
        f = open(arq, 'r')
        pontos = read_roi(f)
        xs = [x for (x,y) in pontos]
        ys = [y for (x,y) in pontos]
        imroi = im.crop((min(ys), min(xs),max(ys),max(xs)))
        arqname = 'roiimgs/'+ '/'.join(arq .split('/')[1:]) +'.jpg'
        imroi.save(arqname)

def mostra_rois_na_imagem(image):

    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    arqs = glob('rois/'+image+'-*.roi')
    for arq in arqs:
        f = open(arq, 'r')
        pontos = read_roi(f)
        xs = [x for (x,y) in pontos]
        ys = [y for (x,y) in pontos]        
        draw_pontos = []
        
        for (x, y) in pontos:
             draw_pontos.append(y)
             draw_pontos.append(x)
        
        draw.polygon(draw_pontos, fill=None)

    im.show()

def salva_mapa_html(image):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    arqs = glob('rois/'+image+'-*.roi')

    html = ''
    html += '<!DOCTYPE html>\n<html>\n<body>'
    html +=  '<img src="%s" usemap="#map" />' % image
    html += '\n<map name="map">\n'


    for arq in arqs:
        f = open(arq, 'r')
        pontos = read_roi(f)
        lpontos = ''
        xs = [x for (x,y) in pontos]
        ys = [y for (x,y) in pontos]
        lpontos =  str(min(ys)) + ',' + str(min(xs)) + ',' + str(max(ys)) + ',' + str(max(xs))
        html +='<area shape="rect" coords="%s" href="http://cenpes.petrobras.com.br" />\n' % lpontos

    html += '</map>\n</body>\n</html>'
    f = open('mapa.html', 'w')
    f.write(html)
    f.close()
    

if __name__ == "__main__":

    try:
        image = sys.argv[1]
        mostra_rois_na_imagem(image)
