# -*- coding: utf-8 -*-
import re
from django.db.models import Q
from pyquery import PyQuery
from cities_light.models import City
from preciosa.precios.models import Cadena, Sucursal


class smart_dict(dict):
    def __missing__(self, key):
        return key


def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text


def buscar_ciudad(ciudad, default='Buenos Aires'):
    try:
        ciudad = City.objects.get(Q(name__iexact=ciudad) | Q(name_ascii__iexact=ciudad))
    except City.DoesNotExist:
        try:
            ciudad = City.objects.get(alternate_names__icontains=ciudad)
        except City.DoesNotExist:
            ciudad = City.objects.get(name='Buenos Aires')
    return ciudad


def import_coto():
    URL = 'http://www.coto.com.ar/mapassucursales/Sucursales/ListadoSucursales.aspx'
    COTO = Cadena.objects.get(nombre='Coto')
    HOR_TMPL = "Lunes a Jueves: %s\nViernes: %s\nSábado: %s\nDomingo: %s"

    normalize_ciudad = smart_dict({'CAP. FED.': 'Capital Federal',
                                   'VTE LOPEZ': 'Vicente Lopez',
                                   'CAPITAL': 'Capital Federal',
                                   'CAP.FED': 'Capital Federal',
                                   'CAP.FEDERAL': 'Capital Federal',
                                   'MALVINAS ARGENTINAS': 'Los Polvorines',
                                   'CDAD. DE BS.AS': 'Capital Federal',
                                   'V ILLA LUGANO': 'Villa Lugano',
                                   'CIUDAD DE SANTA FE': 'Santa Fe',
                                   'CUIDAD DE SANTA FE': 'Santa Fe',
                                   'FISHERTON': 'Rosario',
                                   'GRAL MADARIAGA': 'General Juan Madariaga',
                                   'PARUQUE CHACABUCO': 'Parque Chacabuco',
                                   '': 'Mataderos'
                                   })

    pq = PyQuery(URL)
    for row in pq('table.tipoSuc tr'):
        suc = pq(row)
        if not 'verDetalle' in suc.html():
            continue
        nombre = suc.children('td').eq(2).text().title()
        horarios = HOR_TMPL % tuple([t.text for t in suc.children('td')[3:7]])

        direccion = suc.children('td').eq(7).text().split('-')
        ciudad = buscar_ciudad(normalize_ciudad[direccion[-1].strip()])
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
            cp = None
            ciudad = 'Río Gallegos'     # default
            print 'Fallo: ', url

        direccion = direccion[:-2]
        ciudad = buscar_ciudad()

        telefono = pq('td.descipciones').eq(3).text()
        print Sucursal.objects.create(nombre=nombre, ciudad=ciudad, direccion=direccion,
                               horarios=horarios, telefono=telefono, cadena=LA_ANONIMA,
                               cp=cp)

if __name__ == '__main__':
    importador_laanonima()
