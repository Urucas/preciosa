# -*- coding: utf-8 -*-
import os.path

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from model_utils import Choices
from model_utils.models import TimeStampedModel
from treebeard.mp_tree import MP_Node


class Categoria(MP_Node):
    nombre = models.CharField(max_length=100)
    node_order_by = ['nombre']

    def reload(self):
        if self.id:
            return Categoria.objects.get(pk=self.id)
        return self

    def __unicode__(self):
        return self.nombre


class Producto(models.Model):
    UM_GRAMO = 'gr'
    UM_KILO = 'kg'
    UM_ML = 'ml'
    UM_L = 'l'
    UM_UN = 'unidad'
    UNIDADES_PESO = [UM_GRAMO, UM_KILO]
    UNIDADES_VOLUMEN = [UM_ML, UM_L]
    UNIDADES_CHOICES = Choices(UM_GRAMO, UM_KILO, UM_ML, UM_L, UM_UN)

    descripcion = models.CharField(max_length=100)
    upc = models.CharField(verbose_name=u"Código de barras",
                           max_length=13, unique=True, null=True, blank=True)
    categoria = models.ForeignKey('Categoria')
    marca = models.ForeignKey('Marca', null=True, blank=True)
    contenido = models.DecimalField(max_digits=5, decimal_places=1,
                                    null=True, blank=True)
    unidad_medida = models.CharField(max_length=10,
                                     choices=UNIDADES_CHOICES, null=True, blank=True)
    notas = models.TextField(null=True, blank=True)
    foto = models.ImageField(null=True, blank=True,
                             upload_to=os.path.join(settings.MEDIA_ROOT, 'productos'))
    acuerdos = models.ManyToManyField('Cadena', through='PrecioEnAcuerdo')

    def __unicode__(self):
        return self.descripcion


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(null=True, blank=True,
                             upload_to=os.path.join(settings.MEDIA_ROOT, 'marcas'))
    empresa = models.ForeignKey('Empresa', null=True, blank=True)

    def __unicode__(self):
        return self.nombre


class Empresa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(null=True, blank=True,
                             upload_to=os.path.join(settings.MEDIA_ROOT, 'empresas'))

    def __unicode__(self):
        return self.nombre


class Cadena(Empresa):
    cadena_madre = models.ForeignKey('self', null=True, blank=True)


class LocalComercial(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=100, unique=True)
    cadena = models.ForeignKey('Cadena', null=True, blank=True)

    def clean(self):
        if not self.cadena and not self.nombre:
            raise models.ValidationError('Indique la cadena o el nombre del comercio')

    def __unicode__(self):
        return "%s (%s)" % (self.cadena or self.nombre, self.direccion)


class Precio(TimeStampedModel):
    producto = models.ForeignKey('Producto')
    local = models.ForeignKey('LocalComercial')
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    usuario = models.ForeignKey(User, null=True, blank=True)


class PrecioEnAcuerdo(models.Model):
    producto = models.ForeignKey('Producto')
    cadena = models.ForeignKey('Cadena',
                               limit_choices_to={'cadena_madre__isnull': True})

    precio_norte = models.DecimalField(max_digits=5, decimal_places=2)
    precio_sur = models.DecimalField(max_digits=5, decimal_places=2)
