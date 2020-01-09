# coding=utf-8
import datetime
import os
import configparser
from bs4 import BeautifulSoup
import requests
import shutil
import numpy as np
from PIL import Image
from PIL import ImageOps
from astropy.io import fits
from astropy.table import Table as tb
import sys
from astropy.io.votable import parse,writeto
from astropy.io.votable.tree import Param,Info
from astropy.io.votable.table import from_table
from astropy.io.fits import Header
import gzip

#########################################
###      VARIABLES CONFIGURACION      ###
#########################################

diaExtraido = sys.argv[1]
directorio = "./Extraidos/" + diaExtraido
directorioLogs = "./Logs/" + diaExtraido + ".log"
flogs = open(directorioLogs, "a")

try:
    config = configparser.ConfigParser()
    config.read('configuracion.properties')
    
    raiz = config.get('URLs', 'raiz')
    screenshots_overdense = config.get('URLs', 'screenshots_overdense')
    screenshots_underdense = config.get('URLs', 'screenshots_underdense')
    gnuplot_overdense = config.get('URLs', 'gnuplot_overdense')
    gnuplot_underdense = config.get('URLs', 'gnuplot_underdense')
    stats = config.get('URLs', 'stats')
    proyecto_meteoros = config.get('URLs', 'proyecto_meteoros')
    
    nombreFicheros = config.get('Ficheros', 'nombreFicheros')
    permisos = config.get('Ficheros', 'permisos')
    DescripcionVOTable = config.get('Ficheros', 'DescripcionVOTable')
    
    dirGuardados = config.get('Directorios', 'dirGuardados')
    datsYscreenshots = config.get('Directorios', 'datsYscreenshots')
    fitsOverdense = config.get('Directorios', 'fitsOverdense')
    fitsUnderdense = config.get('Directorios', 'fitsUnderdense')
    votableOverdense = config.get('Directorios', 'votableOverdense')
    votableUnderdense = config.get('Directorios', 'votableUnderdense')
    
    directorioTransformadosFitsOverdense = directorio + fitsOverdense
    directorioTransformadosFitsUnderdense = directorio + fitsUnderdense
    directorioTransformadosVOTableOverdense = directorio + votableOverdense
    directorioTransformadosVOTableUnderdense = directorio + votableUnderdense
    
    col1 = config.get('ColumnasTabla', 'col1')
    col2 = config.get('ColumnasTabla', 'col2')
    col3 = config.get('ColumnasTabla', 'col3')
    col4 = config.get('ColumnasTabla', 'col4')
    col5 = config.get('ColumnasTabla', 'col5')
    col6 = config.get('ColumnasTabla', 'col6')
    
    umbralBajada = config.get('Umbrales', 'umbralBajada')
    umbralSubida = config.get('Umbrales', 'umbralSubida')
    
    durOverdenseEco = config.get('EcoOverdense', 'durOverdenseEco')
    duracionEco = int((int(durOverdenseEco)/1000)*10)
    
    recogerDatosDe = config.get('RecogerDatos', 'recogerDatosDe')
    recogerPrimaryDe = config.get('RecogerDatos', 'recogerPrimaryDe')
    
    cabeceras = config.get(recogerDatosDe, 'cabeceras')
    cabeceras = cabeceras.split(",")
    
    cabecerasPrimaryHDU = config.get(recogerPrimaryDe, 'cabecerasPrimaryHDU')
    cabecerasPrimaryHDU = cabecerasPrimaryHDU.split(",")
    
    parametros = []
    valores = []
    descripciones = []
    
    for i in range(len(cabeceras)):
        parametros.append(config.get(recogerDatosDe, cabeceras[i]))
    
    for n in range(len(parametros)):
        dato = parametros[n].split(",")
        valores.append(dato[0])
        descripciones.append(dato[1])
    
    paramsPrimaryHDU = []
    valsPrimaryHDU = []
    desPrimaryHDU = []
    
    for i2 in range(len(cabecerasPrimaryHDU)):
        paramsPrimaryHDU.append(config.get(recogerPrimaryDe, cabecerasPrimaryHDU[i2]))
    
    for n2 in range(len(paramsPrimaryHDU)):
        dato = paramsPrimaryHDU[n2].split(",")
        valsPrimaryHDU.append(dato[0])
        desPrimaryHDU.append(dato[1])
    
    totalCabeceras = cabecerasPrimaryHDU + cabeceras
    totalValores = valsPrimaryHDU + valores
    totalDescripciones = desPrimaryHDU + descripciones
    
    c1 = fits.Card('EXTNAME', 'ImagenHDU', 'nombre de la extension')
    c2 = fits.Card('EXTNAME', 'DatosHDU', 'nombre de la extension')
    c3 = fits.Card('EXTNAME', 'PrimaryHDU', 'nombre de la extension')
    c4 = fits.Card('DATE', diaExtraido, 'fecha de la deteccion')
    
    imgHeaders = [c1,c4]
    dataHeaders = [c2,c4]
    primaryHeaders = [c3,c4]
    
    for p in range(len(cabeceras)):
        if(cabeceras[p][0:7] == "COMMENT" or cabeceras[p][0:7] == "HISTORY"):
            imgHeaders.append(fits.Card(cabeceras[p][0:7],valores[p],descripciones[p]))
            dataHeaders.append(fits.Card(cabeceras[p][0:7],valores[p],descripciones[p]))
        else:
            imgHeaders.append(fits.Card(cabeceras[p],valores[p],descripciones[p]))
            dataHeaders.append(fits.Card(cabeceras[p],valores[p],descripciones[p]))            
    
    for p1 in range(len(cabecerasPrimaryHDU)):
        if(cabecerasPrimaryHDU[p1][0:7] == "COMMENT" or cabecerasPrimaryHDU[p1][0:7] == "HISTORY"):
            primaryHeaders.append(fits.Card(cabecerasPrimaryHDU[p1][0:7],valsPrimaryHDU[p1],desPrimaryHDU[p1]))
        else:
            primaryHeaders.append(fits.Card(cabecerasPrimaryHDU[p1],valsPrimaryHDU[p1],desPrimaryHDU[p1]))            
    
    ih = Header(imgHeaders)
    dh = Header(dataHeaders)
except:
    flogs.write("LOG: ERROR en la lectura del fichero de configuración\n")
    flogs.close()
    sys.exit(1)

#Inicializacion de Arrays
ficherosFITS = []
enlaces = []
array_screenshots = []
array_dats = []
array_ficheros = []

# Funcion que lee los datos del dat y los escribe en otro fichero
def manejodats(archivos,flag):
    try:
        for i in range(len(archivos)):
            array_lineas = []
            
            if(flag == "overdense"):
                f = open(datsYscreenshots + diaExtraido + gnuplot_overdense + archivos[i] , "r")
            else:
                f = open(datsYscreenshots + diaExtraido + gnuplot_underdense + archivos[i] , "r")
            
            leido = f.readlines()
            f.close()
            for n in range(len(leido)):
                linea = str(leido[n])
                linea = linea.replace('\n','')
                lineas = linea.split(" ")
                final = [p for p in lineas if p ]
                if(final):
                    array_lineas.append(final)

            if(flag == "overdense"): 
                t = 967
                while t < len(array_lineas):
                    if(float(array_lineas[t][6]) > float(umbralBajada)):
                        tamIn = t
                        break
                    t += 968
            
                d = tamIn+968
                while d < len(array_lineas):
                    c = 0
                    resultado = 0
                    if(float(array_lineas[d][6]) < float(umbralBajada)):
                        k = d+968
                        while c < duracionEco and k < len(array_lineas):
                            if(float(array_lineas[k][6]) > float(umbralBajada)):
                                resultado = -1
                                break
                            c += 1
                            k += 968
                        if(resultado == 0):
                            tamFin = d
                            break
                    d += 968
            else:
            
                t = 967
                resultado2 = 0
                while t < len(array_lineas):
                    if(float(array_lineas[t][6]) > float(umbralBajada)):
                        tamIn = t
                        resultado2 = -1
                        break
                    t += 968
                 
                if(resultado2 == 0):
                    tamIn = 967
                    
                d = tamIn+968
                while d < len(array_lineas):
                    if(float(array_lineas[d][6]) < float(umbralBajada)):
                        tamFin = d
                        break
                    d += 968        
                    
            sinRuido = array_lineas[tamIn-967:tamFin-967]
            file2 = open(directorio + "/" + archivos[i].replace('.dat','.txt'),"w")
            for l in range(len(sinRuido)):
                t = datetime.datetime.fromtimestamp(float(sinRuido[l][0])).strftime('%Y/%m/%d-%H:%M:%S.%f')
                t = t[:-3]
                if(len(sinRuido[l]) == 7):
                    file2.write(t + ' ' + sinRuido[l][1] + ' ' + sinRuido[l][2] + ' ' + sinRuido[l][4] + ' ' + sinRuido[l][5] + ' ' + sinRuido[l][6] + '\n')
                else:
                    file2.write(t + ' ' + sinRuido[l][1] + ' ' + sinRuido[l][2] + ' ' + "N/A" + ' ' + "N/A" + ' ' + "N/A" + '\n')
            file2.close()
    except:
        flogs.write("LOG: ERROR en la lectura de los .dat o en la eliminacion del ruido en los " + flag + "\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)
        

# Funcion que convierte los archivos a fits
def conversionfits(archivosscreenshots,archivosdat,flag):
    try:
        if(flag == "overdense"):
            os.makedirs(directorioTransformadosFitsOverdense)
        else:
            os.makedirs(directorioTransformadosFitsUnderdense)
        
        for i in range(len(archivosscreenshots)):
        
            test_input = directorio + "/" + archivosdat[i].replace('.dat','.txt')
            table = tb.read(test_input, format='ascii')
            os.remove(test_input)
            
            nombre = archivosdat[i][32:]
            nombreFits = nombre.replace('.dat','')
            
            if(flag == "overdense"):
                screenshot_input = datsYscreenshots + diaExtraido + screenshots_overdense + archivosscreenshots[i]
                screenshot_output = directorioTransformadosFitsOverdense +  nombreFicheros + nombreFits + '.fits'
            else:
                screenshot_input = datsYscreenshots + diaExtraido + screenshots_underdense + archivosscreenshots[i]
                screenshot_output = directorioTransformadosFitsUnderdense + nombreFicheros + nombreFits + '.fits'
            
            fichero = nombreFicheros + nombreFits + '.fits'
            
            c5 = fits.Card('TITLE', fichero, 'Nombre del fichero')
            primaryHeaders.append(c5)
            ph = Header(primaryHeaders)
            
            im = Image.open(screenshot_input)
            im = ImageOps.flip(im)
            im.save("temporal.png")
    
            image = Image.open('temporal.png')
            xsize, ysize = image.size
            r, g, b = image.split()
            r_data = np.array(r.getdata())
            r_data = r_data.reshape(ysize, xsize)
            g_data = np.array(g.getdata())
            g_data = g_data.reshape(ysize, xsize)
            b_data = np.array(b.getdata())
            b_data = b_data.reshape(ysize, xsize)
            datos = [r_data,g_data,b_data]
            os.remove('temporal.png')
            
            hdu1 = fits.PrimaryHDU(header=ph)
            hdu2 = fits.ImageHDU(data=datos,header=ih)
            hdu3 = fits.BinTableHDU(data=np.array(table),header=dh)
            hdul = fits.HDUList([hdu1,hdu2,hdu3])
            hdul.writeto(screenshot_output)
            
            hdulist = fits.open(screenshot_output, mode='update')
            header2 = hdulist[2].header
            
            header2.set('TTYPE1',col1.split(",")[0],col1.split(",")[1])
            header2.set('TTYPE2',col2.split(",")[0],col2.split(",")[1])
            header2.set('TTYPE3',col3.split(",")[0],col3.split(",")[1])
            header2.set('TTYPE4',col4.split(",")[0],col4.split(",")[1])
            header2.set('TTYPE5',col5.split(",")[0],col5.split(",")[1])
            header2.set('TTYPE6',col6.split(",")[0],col6.split(",")[1])
                
            hdulist.flush()
            hdulist.close()
            primaryHeaders.pop()
            with open(screenshot_output, 'rb') as f_in:
                with gzip.open(screenshot_output + ".gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    ficherosFITS.append(fichero + ".gz")
    except:
        flogs.write("LOG: ERROR en la conversion  de los " + flag + " a FITS\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)

# Funcion que sube los ficheros FITS comprimidos via FTP
def moverArchivosFITS(ficherosFITS,flag):
    try:
        actual = os.getcwd()
        if(flag == "overdense"):
            os.chdir(dirGuardados)
            os.mkdir(diaExtraido)
            os.chmod(diaExtraido,int(permisos,8))
            os.chdir(diaExtraido)
            os.mkdir("Overdense")
            os.chmod("Overdense",int(permisos,8))
            os.chdir(actual + directorioTransformadosFitsOverdense.replace(".",""))
            for n in range(len(ficherosFITS)):
                os.chmod(ficherosFITS[n],int(permisos,8))
                shutil.move(ficherosFITS[n], dirGuardados + diaExtraido + "/Overdense/" + ficherosFITS[n])
            os.chdir(actual)
        else:
            os.chdir(dirGuardados)
            os.chdir(diaExtraido)
            os.mkdir("Underdense")
            os.chmod("Underdense",int(permisos,8))
            os.chdir(actual + directorioTransformadosFitsUnderdense.replace(".",""))
            for n in range(len(ficherosFITS)):
                os.chmod(ficherosFITS[n],int(permisos,8))
                shutil.move(ficherosFITS[n], dirGuardados + diaExtraido + "/Underdense/" + ficherosFITS[n])
            os.chdir(actual)
    except:
        flogs.write("LOG: ERROR al mover los FITS de los " + flag + "\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)        

# Funcion que obtiene los enlaaces para los VOTable
def enlacesVOTable(flag):
    try:
        if(flag == "overdense"):
            r  = requests.get(proyecto_meteoros + diaExtraido + "/Overdense")
            data = r.text
            soup = BeautifulSoup(data,'html.parser')
            for link in soup.find_all('a'):
                if(link.get('href').find("gz") != -1):
                    url = proyecto_meteoros + diaExtraido +"/Overdense/" + link.get('href')
                    enlaces.append(url)
        else:
            r  = requests.get(proyecto_meteoros + diaExtraido + "/Underdense")
            data = r.text
            soup = BeautifulSoup(data,'html.parser')
            for link in soup.find_all('a'):
                if(link.get('href').find("gz") != -1):
                    url = proyecto_meteoros + diaExtraido +"/Underdense/" + link.get('href')
                    enlaces.append(url)
    except:
        flogs.write("LOG: ERROR en la obtencion de los enlaces para los VOTable de los " + flag + "\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)      


# Funcion que convierte los fits a VOTable
def conversionVOTable(archivosdat,flag):
    try:
        if(flag == "overdense"):
            os.makedirs(directorioTransformadosVOTableOverdense)
        else:
            os.makedirs(directorioTransformadosVOTableUnderdense)
        
        for i in range(len(archivosdat)):
    
            nombre = archivosdat[i][32:]
            nombreFits = nombre.replace('.dat','')
            nombreVOTable = nombre.replace('.dat','')
            if(flag == "overdense"):
                fichero_fits = directorioTransformadosFitsOverdense + nombreFicheros + nombreFits + '.fits'
                votable_output =  directorioTransformadosVOTableOverdense + nombreFicheros + nombreVOTable + '.xml'
            else:
                fichero_fits = directorioTransformadosFitsUnderdense + nombreFicheros + nombreFits + '.fits'
                votable_output =  directorioTransformadosVOTableUnderdense + nombreFicheros + nombreVOTable + '.xml'
           
            fichero = nombreFicheros + nombreFits + '.fits'
        
            t = tb.read(fichero_fits)
            os.remove(fichero_fits)
            votable = from_table(t[0:1])
            writeto(votable,  votable_output)
            
            votable = parse(votable_output)
            resource = votable.resources[0]
            resource.description = "Fichero " + fichero + " " + DescripcionVOTable
            
            param = Param(votable,name="TITLE", datatype="char", arraysize=str(len(fichero)), value=fichero)
            param.description = "nombre del fichero"
            resource.params.append(param)
            
            param = Param(votable,name="DATE", datatype="char", arraysize=str(len(diaExtraido)), value=diaExtraido)
            param.description = "fecha de la deteccion"
            resource.params.append(param)
            
            for n in range(len(totalValores)):
                    if(totalValores[n].isdigit() or (totalValores[n].startswith('-') and totalValores[n][1:].isdigit())):
                        param = Param(votable,name=totalCabeceras[n], datatype="int",value=totalValores[n])
                        param.description = totalDescripciones[n]
                        resource.params.append(param)
                    elif(totalValores[n] == "True" or totalValores[n] == "False"):
                        param = Param(votable,name=totalCabeceras[n], datatype="boolean",value=totalValores[n])
                        param.description = totalDescripciones[n]
                        resource.params.append(param)
                    else:
                        try:
                            if(float(totalValores[n])):
                                param = Param(votable,name=totalCabeceras[n], datatype="float",value=totalValores[n])
                                param.description = totalDescripciones[n]
                                resource.params.append(param)
                        except:
                            if(totalCabeceras[n][0:7] == "COMMENT" or totalCabeceras[n][0:7] == "HISTORY"):
                                info = Info(name=totalCabeceras[n][0:7], value=totalValores[n])
                                resource.infos.append(info)                           
                            else:
                                param = Param(votable,name=totalCabeceras[n], datatype="char", arraysize=str(len(totalValores[n])), value=totalValores[n])
                                param.description = totalDescripciones[n]
                                resource.params.append(param)                                
    
            votable.to_xml(votable_output)
            stri = '    <FITS>\n     <STREAM encoding="gzip" href="'+enlaces[i]+'"/>\n    </FITS>\n'
            
            f = open(votable_output, "r")
            leido = f.readlines()
            f.close()
            os.remove(votable_output)
    
            for n in range(len(leido)):
                if(leido[n][4:8] == "DATA"):
                    Ini = n+1
                if(leido[n][5:9] == "DATA"):
                    Fin = n
    
            parte1 = leido[:Ini]
            parte2 = leido[Fin:]
    
            file2 = open(votable_output,"w")
            for p1 in range(len(parte1)):
                if(parte1[p1][3:10] == "TABLE n"):
                    file2.write("  <TABLE nrows=\"" + str(len(t)) + "\">" + "\n") 
                else:
                    file2.write(parte1[p1]) 
            file2.write(stri)
            for p2 in range(len(parte2)):
                file2.write(parte2[p2]) 
            file2.close()    
    except:
        flogs.write("LOG: ERROR en la conversion a  VOTable de los " + flag + "\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)   

# Funcion que sube los ficheros VOTable via FTP
def moverArchivosVOTable(ficherosFITS,flag):
    try:
        actual = os.getcwd()
        if(flag == "overdense"):
            os.chdir(directorioTransformadosVOTableOverdense)
            for n in range(len(ficherosFITS)):
                filename = ficherosFITS[n].replace(".fits.gz",".xml")
                os.chmod(filename,int(permisos,8))
                shutil.move(filename, dirGuardados + diaExtraido + "/Overdense/" + filename)
            os.chdir(actual)
        else:
            os.chdir(directorioTransformadosVOTableUnderdense)
            for n in range(len(ficherosFITS)):
                filename = ficherosFITS[n].replace(".fits.gz",".xml")
                os.chmod(filename,int(permisos,8))
                shutil.move(filename, dirGuardados + diaExtraido + "/Underdense/" + filename)
            os.chdir(actual)
    except:
        flogs.write("LOG: ERROR al mover los VOTable de los " + flag + "\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)      

#########################################
###         INICIO DEL SCRIPT         ###
#########################################

r  = requests.get(raiz + diaExtraido + screenshots_overdense)
if r.status_code != 200:
    print("LOG: No hay datos para extraer en la fecha introducida")
    flogs.write("LOG: ERROR, No hay datos para extraer en la fecha introducida\n")
    flogs.close()
    sys.exit(1)
else: 
    if(os.path.isdir(dirGuardados + diaExtraido)):
        actual = os.getcwd()
        os.chdir(dirGuardados)
        shutil.rmtree(diaExtraido)
        os.chdir(actual)
    os.makedirs(directorio)
    try:
        dirs = os.listdir(datsYscreenshots + diaExtraido + screenshots_overdense)
        for file in dirs:
            array_screenshots.append(file)
        dirs = os.listdir(datsYscreenshots + diaExtraido + gnuplot_overdense)
        for file in dirs:
            array_dats.append(file)
    except:
        flogs.write("LOG: ERROR al listar los directorios con los gnuplots y las screenshots overdense\n")
        flogs.close()
        shutil.rmtree(directorio)
        sys.exit(1)   
        
array_screenshots.sort()
array_dats.sort()

flag = "overdense"
print("LOG: Va a comenzar la conversion de los archivos Overdense")
flogs.write("LOG: Conversion de los Overdense:\n")
manejodats(array_dats,flag)
flogs.write("LOG: Datos leidos de los .dat y ruido eliminado de los " + flag + " con exito\n")
conversionfits(array_screenshots,array_dats,flag)
flogs.write("LOG: Conversion de los archivos " + flag + " a FITS realizada con exito\n")
moverArchivosFITS(ficherosFITS,flag)
flogs.write("LOG: Ficheros FITS " + flag + " comprimidos y movidos con exito\n")
enlacesVOTable(flag)
conversionVOTable(array_dats,flag)
flogs.write("LOG: Conversion de fits a VOTable de los " + flag + " realizada con exito\n")
moverArchivosVOTable(ficherosFITS,flag)
flogs.write("LOG: Ficheros VOTable de los " + flag + " comprimidos y movidos con exito\n")

array_screenshots = []
array_dats = []
ficherosFITS = []
enlaces = []

try:
    dirs = os.listdir(datsYscreenshots + diaExtraido + screenshots_underdense)
    for file in dirs:
        array_screenshots.append(file)
    dirs = os.listdir(datsYscreenshots + diaExtraido + gnuplot_underdense)
    for file in dirs:
        array_dats.append(file)
    
    array_screenshots.sort()
    array_dats.sort()
except:
    flogs.write("LOG: ERROR al listar los directorios con los gnuplots y las screenshots underdense\n")
    flogs.close()
    shutil.rmtree(directorio)
    sys.exit(1)   

flag = "underdense"
print("LOG: Va a comenzar la conversion de los archivos Underdense")
flogs.write("LOG: Conversion de los Underdense:\n")
manejodats(array_dats,flag)
flogs.write("LOG: Datos leidos de los .dat y ruido eliminado de los " + flag + " con exito\n")
conversionfits(array_screenshots,array_dats,flag)
flogs.write("LOG: Conversion de los archivos " + flag + " a FITS realizada con exito\n")
moverArchivosFITS(ficherosFITS,flag)
flogs.write("LOG: Ficheros FITS " + flag + " comprimidos y movidos con exito\n")
enlacesVOTable(flag)
conversionVOTable(array_dats,flag)
flogs.write("LOG: Conversion de fits a VOTable de los " + flag + " realizada con exito\n")
moverArchivosVOTable(ficherosFITS,flag)
flogs.write("LOG: Ficheros VOTable de los " + flag + " comprimidos y movidos con exito\n")
shutil.rmtree(directorio)
flogs.close()
sys.exit(0) 