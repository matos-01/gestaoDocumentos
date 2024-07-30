# -*- coding: utf-8 -*-
# vi:si:et:sw=4:ts=4

import os

from django.db import models
from django.contrib.auth.models import Group, User

from panflight.models.projects import Department


def get_upload_path(instance, filename):
    user = instance.uploaded_by
    department = Department.objects.get(user=user)
    category = instance.document_subcategory.category.name
    subcategory = instance.document_subcategory.name
    folder_project = instance.code + " - " + instance.name
    upload_path = os.path.join("Documentos", category, subcategory, folder_project, department.department.name)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return os.path.join(upload_path, filename)


class Document(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def __str__(self):
        return self.code + " - " + self.name

    document_file = models.FileField("Arquivo", upload_to=get_upload_path, max_length=768, null=True, blank=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    comments = models.CharField("Comentários", max_length=256)

    status = models.SmallIntegerField("Status")

    version = models.CharField("Versão", max_length=2)

    name = models.CharField("Name", max_length=64)

    upload_date = models.DateTimeField("Data do Upload", auto_now_add=True)

    expiration_date = models.DateField("Data de Expiração", null=True, blank=True)

    code = models.CharField("Código", max_length=64)

    document_subcategory = models.ForeignKey(
        "panflight.DocumentSubCategory", null=True, blank=True, on_delete=models.CASCADE
    )

    last_activity = models.ForeignKey(
        "panflight.ProjectActivity",
        related_name="last_activity",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    approver = models.ForeignKey(User, related_name="Aprovador", null=True, blank=True, on_delete=models.CASCADE)

    STATUS_DRAFT = 0
    STATUS_VERIFIED = 1
    STATUS_APPROVED = 2
    STATUS_REVISION = 3
    STATUS_EXPIRED = 4
    STATUS_CANCELED = 5

    statuses = {
        STATUS_DRAFT: "Rascunho",
        STATUS_VERIFIED: "Verificado",
        STATUS_APPROVED: "Aprovado",
        STATUS_REVISION: "Pendente Revisão",
        STATUS_EXPIRED: "Expirado",
        STATUS_CANCELED: "Cancelado",
    }


class DocumentCategory(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Categoria do Documento"
        verbose_name_plural = "Categorias dos Documentos"

    def __str__(self):
        return self.name

    name = models.CharField("Nome", max_length=64, null=True, blank=True)

    groups = models.ManyToManyField(Group)

    active = models.BooleanField("Ativo?", default=True)


class UserCategory(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Usuário x Categoria"
        verbose_name_plural = "Usuários x Categorias"

    category = models.ForeignKey("panflight.DocumentCategory", on_delete=models.CASCADE)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    editor = models.BooleanField("Editor", default=False)


class DocumentSubCategory(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Sub Categoria do Documento"
        verbose_name_plural = "Sub Categorias do Documento"

    def __str__(self):
        return self.category.name + " - " + self.name

    name = models.CharField("Nome", max_length=64)

    active = models.BooleanField("Ativo?", default=True)

    category = models.ForeignKey("panflight.DocumentCategory", on_delete=models.CASCADE)
