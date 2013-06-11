# -*- coding: utf-8 -*-
import re
from pyquery import PyQuery
from preciosa.precios.models import Cadena, Ciudad, Sucursal


class smart_dict(dict):
    def __missing__(self, key):
        return key


def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text


def import_coto():
    URL = 'http://www.coto.com.ar/mapassucursales/Sucursales/ListadoSucursales.aspx'
    COTO = Cadena.objects.get(nombre='Coto')
    HOR_TMPL = "Lunes a Jueves: %s\nViernes: %s\nSábado: %s\nDomingo: %s"

    normalize_ciudad = smart_dict({'CAP. FED.': 'Capital Federal',
                                   'VTE LOPEZ': 'Vicente Lopez',
                                   'CAPITAL': 'Capital Federal',
                                   'CAP.FED': 'Capital Federal',
                                   'CAP.FEDERAL': 'Capital Federal',
                                   'CDAD. DE BS.AS': 'Capital Federal',
                                   'V ILLA LUGANO': 'Villa Lugano',
                                   'CIUDAD DE SANTA FE': 'Santa Fe',
                                   'CUIDAD DE SANTA FE': 'Santa Fe',
                                   'FISHERTON': 'Rosario',
                                   'GRAL MADARIAGA': 'General Madariaga',
                                   'PARUQUE CHACABUCO': 'Parque Chacabuco',
                                   '': 'Mataderos'
                                   })

    provincias_conocidas = {'Rosario': 'Santa Fe',
                             'Santa Fe': 'Santa Fe',
                             'Lanus': 'Buenos Aires',
                             'Banfield': 'Buenos Aires',
                             'Bernal': 'Buenos Aires',
                             'Olivos': 'Buenos Aires',
                             'San Isidro': 'Buenos Aires',
                             'La Plata': 'Buenos Aires',
                             'Lomas De Zamora': 'Buenos Aires',
                             'Sarandi': 'Buenos Aires',
                             'Malvinas Argentinas': 'Buenos Aires',
                             'General Madariaga': 'Buenos Aires',
                             'Punta Chica': 'Buenos Aires',
                             'Ezeiza': 'Buenos Aires',
                             'Pilar': 'Buenos Aires',
                             'Gonzalez Catan': 'Buenos Aires',
                             'Barracas': 'Buenos Aires',

                        }


    pq = PyQuery(URL)
    for row in pq('table.tipoSuc tr'):
        suc = pq(row)
        if not 'verDetalle' in suc.html():
            continue
        nombre = suc.children('td').eq(2).text().title()
        horarios = HOR_TMPL % tuple([t.text for t in suc.children('td')[3:7]])

        direccion = suc.children('td').eq(7).text().split('-')
        ciudad = normalize_ciudad[direccion[-1].strip()].title()

        try:
            ciudad = Ciudad.objects.get(nombre=ciudad)
        except Ciudad.DoesNotExist:
            prov = provincias_conocidas.get(ciudad, 'Ciudad Autónoma de Buenos Aires')
            ciudad = Ciudad.objects.create(nombre=ciudad,
                                           provincia=prov)
        direccion = '-'.join(direccion[:-1]).strip().title()
        telefono = suc.children('td').eq(8).text().strip()
        print Sucursal.objects.create(nombre=nombre, ciudad=ciudad, direccion=direccion,
                               horarios=horarios, telefono=telefono, cadena=COTO)


def importador_laanonima():
    dir_pattern = re.compile(r'(?P<suc>Suc.*\: )?(?P<dir>.*),?.*\((?P<cp>\d+)\), (?P<ciu>.*), (?P<prov>.*)$')
    URL_BASE = 'http://www.laanonima.com.ar/sucursales/sucursal.php?id='
    LA_ANONIMA = Cadena.objects.get(nombre=u"La Anónima")

    for i in range(1, 159):
        url = URL_BASE + str(i)
        pq = PyQuery(url)
        nombre = pq('td.titulos').eq(0).text().strip()
        if not nombre:
            continue
        descripcion = pq('td.descipciones').eq(1).text()
        if 'Superquik' in descripcion or 'Quick' in descripcion:
            continue
        try:
            horarios = re.search(r'atenci\xf3n: (.*) \xc1rea', descripcion).groups()[0]
        except (AttributeError, IndexError):
            horarios = ''
        direccion = pq('td.descipciones').eq(2).text()
        try:
            _, direccion, cp, ciudad, provincia = dir_pattern.match(direccion).groups()
        except (TypeError, AttributeError):
            ciudad, _ = Ciudad.objects.get_or_create(nombre='Rio Gallegos',
                                                  provincia='Santa Cruz')
            cp = None
            print 'Fallo: ', url
        else:
            direccion = direccion[:-2]
            provincia = replace_all(provincia, dict(zip(u'áéíóú', 'aeiou')))
            ciudad, _ = Ciudad.objects.get_or_create(nombre=ciudad, provincia=provincia)

        telefono = pq('td.descipciones').eq(3).text()
        print Sucursal.objects.create(nombre=nombre, ciudad=ciudad, direccion=direccion,
                               horarios=horarios, telefono=telefono, cadena=LA_ANONIMA,
                               cp=cp)



if __name__ == '__main__':
    importador_laanonima()
