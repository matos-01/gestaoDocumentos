# -*- coding: utf-8 -*-
# vi:si:et:sw=4:ts=4

import os

from django.db import models
from django.contrib.auth.models import Group, User

from panflight.settings import MEDIA_ROOT


def get_upload_path(instance, filename):
    user = instance.uploaded_by
    department = Department.objects.get(user=user)
    folder_project = Project.get_project_folder(instance.project)
    draw = instance.draw
    images = [".jpg", ".png", ".jpeg", ".bmp", "gif", ".jfif", ".tiff"]
    documents = [".doc", ".docx", ".pdf", ".odt", ".txt"]
    spreadsheet = [".xls", ".xlsx", ".ods", ".csv"]
    cad = [".dwg", ".dxf"]
    upload_path = os.path.join("Projetos", folder_project, department.department.name, draw)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    if any(item in filename for item in images):
        upload_path = os.path.join(upload_path, "Imagens")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
    elif any(item in filename for item in documents):
        upload_path = os.path.join(upload_path, "Documentos")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
    elif any(item in filename for item in spreadsheet):
        upload_path = os.path.join(upload_path, "Planilhas")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
    elif any(item in filename for item in cad):
        upload_path = os.path.join(upload_path, "CADs")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
    else:
        upload_path = os.path.join(upload_path, "Outros")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
    return os.path.join(upload_path, filename)


class News(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"

    def __str__(self):
        return self.title

    description = models.TextField("Descrição")

    title = models.CharField("Título", max_length=128)

    media = models.FileField(upload_to="news_media/", verbose_name="Imagem", blank=True, null=True)

    creation_date = models.DateTimeField("Data de Criação", auto_now_add=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    start_date = models.DateField("Data de Início")

    end_date = models.DateField("Data de Fim")

    active = models.BooleanField("Ativa?", default=True)


class Project(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self):
        return self.identifier + " - " + self.name

    identifier = models.CharField("Código", max_length=6, null=True)

    media = models.FileField(upload_to="project_media/", verbose_name="Imagem", blank=True, null=True)

    name = models.CharField("Nome do Projeto", max_length=64, null=True)

    description = models.CharField("Descrição", max_length=256, null=True)

    status = models.SmallIntegerField("Status", null=True)

    creation_date = models.DateTimeField("Data de Criação", auto_now_add=True, null=True)

    start_date = models.DateField("Data de Início", null=True, blank=True)

    end_date = models.DateField("Data de Conclusão", null=True, blank=True)

    responsible = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    original_pn = models.CharField("P/N Original", max_length=64, null=True)

    panflight_pn = models.CharField("P/N PanFlight", max_length=64, null=True)

    template = models.ForeignKey("panflight.ProjectTemplate", on_delete=models.CASCADE, null=True)

    STATUS_NEW = 0
    STATUS_EXECUTION = 1
    STATUS_PAUSED = 2
    STATUS_COMPLETED = 3
    STATUS_CANCELED = 4

    statuses = {
        STATUS_NEW: "Novo",
        STATUS_EXECUTION: "Em Execução",
        STATUS_PAUSED: "Pausado",
        STATUS_COMPLETED: "Concluído",
        STATUS_CANCELED: "Cancelado",
    }

    @classmethod
    def create_folders(cls, identifier, name, template):
        success = False
        error = False
        project_folder_name = identifier + " - " + name
        try:
            project_dir = os.path.join(MEDIA_ROOT, "Projetos", project_folder_name)
            os.mkdir(project_dir)
            editable = "Editáveis"
            for folder in template.folders.all().filter(active=True):
                os.makedirs(os.path.join(project_dir, folder.name, editable))
                actual_folder = os.path.join(project_dir, folder.name, editable)
                dept = folder.name.replace(" ", "_")
                folder_name = "Editaveis" + "_" + dept + "_" + identifier
                actual_folder = actual_folder.replace("/", "\\")
                # subprocess.run('net share %s="%s" /grant:Todos,FULL' % (folder_name,
                #                                                         actual_folder),
                #                                                         shell=True, check=True)
                # departments = Department.objects.filter(name=folder.name)
                # print(departments)
                # for item in departments:
                #     command = 'cacls "%s" /G %s:F' % (actual_folder, item.user.username)
                #     try:
                #         subprocess.run(command, shell=True, check=True)
                #     except Exception as e:
                #         continue
            success = True
        except Exception as e:
            print(str(e))
            error = True
        return (success, error)

    @classmethod
    def get_project_folder(cls, project):
        project_folder_name = project.identifier + " - " + project.name
        project_folder = project_folder_name
        return project_folder


class Department(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Usuario x Departamento"
        verbose_name_plural = "Usuarios x Departamentos"
        unique_together = [["department", "user"]]

    def __str__(self):
        return self.department.name

    department = models.ForeignKey("panflight.DepartmentName", on_delete=models.CASCADE)

    user = models.OneToOneField(User, on_delete=models.CASCADE)


class ProjectFiles(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Arquivo de Projeto"
        verbose_name_plural = "Arquivos de Projeto"

    def __str__(self):
        return self.draw + " - " + self.name

    project_file = models.FileField("Arquivo", upload_to=get_upload_path, max_length=768)

    project = models.ForeignKey("panflight.Project", on_delete=models.CASCADE)

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    comments = models.CharField("Comentários", max_length=256)

    status = models.SmallIntegerField("Status")

    version = models.CharField("Versão", max_length=2)

    draw = models.CharField("Desenho", max_length=64)

    name = models.CharField("Name", max_length=64)

    upload_date = models.DateTimeField("Data do Upload", auto_now_add=True)

    groups = models.ManyToManyField(Group)

    STATUS_PRODUCTION = 0
    STATUS_PROGRESS = 1
    STATUS_OBSOLETE = 2

    statuses = {
        STATUS_PRODUCTION: "Disp. Produção",
        STATUS_PROGRESS: "Em Processo",
        STATUS_OBSOLETE: "Obsoleto",
    }


class ProjectActivity(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Atividade do Projeto"
        verbose_name_plural = "Atividades dos Projetos"

    def __str__(self):
        if self.project:
            return self.project.name
        else:
            return self.document.name

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    date = models.DateTimeField("Data", auto_now_add=True)

    project_file = models.ForeignKey(
        "panflight.ProjectFiles",
        verbose_name="Arquivos",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    event = models.SmallIntegerField("Evento")

    project = models.ForeignKey(
        "panflight.Project",
        verbose_name="Projeto",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    reason = models.TextField("Motivo", null=True, blank=True)

    document = models.ForeignKey(
        "panflight.Document",
        verbose_name="Documento",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    EVENT_CREATE = 0
    EVENT_START = 1
    EVENT_PAUSE = 2
    EVENT_COMPLETE = 3
    EVENT_CANCEL = 4
    EVENT_UPLOAD = 5
    EVENT_APPROVAL = 6
    EVENT_REVISION = 7
    EVENT_UPDATE = 8

    events = {
        EVENT_CREATE: "Criar",
        EVENT_START: "Iniciar",
        EVENT_PAUSE: "Paralisar",
        EVENT_COMPLETE: "Concluir",
        EVENT_CANCEL: "Cancelar",
        EVENT_UPLOAD: "Upload",
        EVENT_APPROVAL: "Aprovar",
        EVENT_REVISION: "Revisar",
        EVENT_UPDATE: "Atualizar",
    }


class ProjectTemplateFolder(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Pasta do Template"
        verbose_name_plural = "Pastas do Template"

    def __str__(self):
        return self.name

    name = models.CharField("Nome da Pasta", max_length=32)

    public = models.BooleanField("Público?", default=False)

    active = models.BooleanField("Ativa", default=True)


class ProjectTemplate(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Template do Projeto"
        verbose_name_plural = "Template de Projetos"

    def __str__(self):
        return self.template_name

    template_name = models.CharField("Nome do Template", max_length=32)

    folders = models.ManyToManyField(ProjectTemplateFolder, verbose_name="Pastas")

    active = models.BooleanField("Ativo", default=True)


class DepartmentName(models.Model):
    class Meta:
        app_label = "panflight"
        verbose_name = "Departmento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.name

    name = models.CharField("Nome", max_length=128)
