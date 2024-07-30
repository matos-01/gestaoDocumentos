# -*- coding: utf-8 -*-
# vi:si:et:sw=4:ts=4

import datetime
import os


from braces.views import LoginRequiredMixin

from panflight.forms import (
    ProjectActivityReportForm,
    ProjectFilesReportForm,
    ProjectReportForm,
)
from panflight.models.projects import Project, ProjectActivity, ProjectFiles
from panflight.views.base import FormListView


class ProjectReportView(LoginRequiredMixin, FormListView):
    template_name = "project_report.html"
    form_class = ProjectReportForm
    csv_header = (
        "CÓD. PROJETO",
        "NOME",
        "DESCRIÇÃO",
        "P/N ORIGINAL",
        "P/N PANFLIGHT",
        "STATUS",
        "DT. CRIAÇÃO",
        "DT. PREV. INÍCIO",
        "DT. PREV. TÉRMINO",
        "CRIADO POR",
        "TEMPLATE",
    )

    def __init__(self, *args, **kwargs):
        super(ProjectReportView, self).__init__(*args, **kwargs)
        self.start_date = self.end_date = datetime.date.today()

    def get_context_data(self, **kwargs):
        context = super(ProjectReportView, self).get_context_data(**kwargs)
        context["object_list"] = self.get_queryset()
        return context

    def get_queryset(self):
        filters = {}
        if self.request.method == "POST":
            try:
                start_date = self.form.cleaned_data["start_date"]
            except:
                start_date = datetime.datetime.now()
            self.start_date = start_date or self.start_date

            end_date = self.form.cleaned_data["end_date"]
            self.end_date = end_date or self.end_date

            try:
                service_order = self.form.cleaned_data["service_order"]
                self.service_order = HangarServiceOrder.objects.get(id=service_order)
            except:
                self.service_order = None
            if self.form.cleaned_data["identifier"]:
                filters["identifier"] = self.form.cleaned_data["identifier"]
            if self.form.cleaned_data["name"]:
                filters["name__icontains"] = self.form.cleaned_data["name"]
            if self.form.cleaned_data["pn_original"]:
                filters["original__icontains"] = self.form.cleaned_data["pn_original"]
            if self.form.cleaned_data["pn_panflight"]:
                filters["panflight_pn__icontains"] = self.form.cleaned_data[
                    "pn_panflight"
                ]
            if self.form.cleaned_data["status"]:
                filters["status"] = self.form.cleaned_data["status"]

        start_date = self.start_date
        end_date = datetime.datetime.combine(self.end_date, datetime.time(23, 59, 59))
        projects = Project.objects.filter(**filters)
        if hasattr(self, "form") and self.form.cleaned_data["csv_export"]:
            formatted_projects = []
            for project in projects:
                creation_date = project.creation_date.strftime("%d/%m/%Y")
                start_date = project.start_date.strftime("%d/%m/%Y")
                end_date = project.start_date.strftime("%d/%m/%Y")
                formatted_projects.append(
                    (
                        project.identifier,
                        project.name,
                        project.description,
                        project.original_pn,
                        project.panflight_pn,
                        Project.statuses[project.status],
                        creation_date,
                        start_date,
                        end_date,
                        project.responsible,
                        project.template.template_name,
                    )
                )
            return formatted_projects

        return projects

    def get_title(self):
        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        if self.service_order:
            title = "Relatório de Projetos"
        if self.start_date != self.end_date:
            title += "de %s a %s" % (start_date, end_date)
        else:
            title += "de %s" % start_date

        return title

    def get_csv_filename(self):
        if self.start_date != self.end_date:
            filename = "Relatorio_Projetos_%s_a_%s.csv"
            filename = filename % (self.start_date, self.end_date)
        else:
            filename = "Relatorio_Projetos_%s.csv" % self.start_date
        return filename + ".csv"


class ProjectActivityReportView(LoginRequiredMixin, FormListView):
    template_name = "activity_report.html"
    form_class = ProjectActivityReportForm
    csv_header = (
        "COD. PROJETO",
        "NOME PROJETO",
        "USUARIO",
        "EVENTO",
        "DATA",
        "MOTIVO",
        "ARQUIVO DO UPLOAD",
    )

    def __init__(self, *args, **kwargs):
        super(ProjectActivityReportView, self).__init__(*args, **kwargs)
        self.start_date = self.end_date = datetime.date.today()

    def get_context_data(self, **kwargs):
        context = super(ProjectActivityReportView, self).get_context_data(**kwargs)
        context["object_list"] = self.get_queryset()
        return context

    def get_queryset(self):
        filters = {}
        if self.request.method == "POST":
            start_date = self.form.cleaned_data["start_date"]
            end_date = self.form.cleaned_data["end_date"]
            if start_date:
                filters["date__gte"] = start_date
            if end_date:
                filters["date__lte"] = end_date
            if self.form.cleaned_data["project_identifier"]:
                filters["project__identifier__icontains"] = self.form.cleaned_data[
                    "project_identifier"
                ]
            if self.form.cleaned_data["user"]:
                filters["user"] = self.form.cleaned_data["user"]
            if self.form.cleaned_data["event"]:
                filters["event"] = self.form.cleaned_data["event"]
            activities = ProjectActivity.objects.filter(**filters)

        if hasattr(self, "form") and self.form.cleaned_data["csv_export"]:
            formatted_projects = []
            print(activities)
            for activity in activities:
                upload_file = "N/A"
                date = activity.date.strftime("%d/%m/%Y %H:%M:%S")
                if activity.project_file:
                    upload_file = os.path.basename(
                        activity.project_file.project_file.name
                    )
                formatted_projects.append(
                    (
                        activity.project.identifier,
                        activity.project.name,
                        activity.user.username,
                        activity.events[activity.event],
                        date,
                        activity.reason,
                        upload_file,
                    )
                )
            return formatted_projects
        elif self.request.method == "POST":
            return activities

    def get_title(self):
        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        if self.service_order:
            title = "Relatório de Atividades"
        if self.start_date != self.end_date:
            title += "de %s a %s" % (start_date, end_date)
        else:
            title += "de %s" % start_date

        return title

    def get_csv_filename(self):
        if self.start_date != self.end_date:
            filename = "Relatorio_Atividades_%s_a_%s.csv"
            filename = filename % (self.start_date, self.end_date)
        else:
            filename = "Relatorio_Atividades_%s.csv" % self.start_date
        return filename + ".csv"


class ProjectFilesReportView(LoginRequiredMixin, FormListView):
    template_name = "file_report.html"
    form_class = ProjectFilesReportForm
    csv_header = (
        "COD. PROJETO",
        "NOME PROJETO",
        "ARQUIVO",
        "DATA",
        "USUARIO",
        "DESENHO",
        "VERSAO",
        "NOME",
        "COMENTARIOS",
        "STATUS",
    )

    def __init__(self, *args, **kwargs):
        super(ProjectFilesReportView, self).__init__(*args, **kwargs)
        self.start_date = self.end_date = datetime.date.today()

    def get_context_data(self, **kwargs):
        context = super(ProjectFilesReportView, self).get_context_data(**kwargs)
        context["object_list"] = self.get_queryset()
        return context

    def get_queryset(self):
        filters = {}
        if self.request.method == "POST":
            start_date = self.form.cleaned_data["start_date"]
            end_date = self.form.cleaned_data["end_date"]
            if start_date:
                filters["upload_date__gte"] = start_date
            if end_date:
                filters["upload_date__lte"] = end_date
            if self.form.cleaned_data["project_identifier"]:
                filters["project__identifier__icontains"] = self.form.cleaned_data[
                    "project_identifier"
                ]
            if self.form.cleaned_data["uploaded_by"]:
                filters["uploaded_by"] = self.form.cleaned_data["uploaded_by"]
            if self.form.cleaned_data["status"]:
                filters["status"] = self.form.cleaned_data["status"]
            if self.form.cleaned_data["version"]:
                filters["version"] = self.form.cleaned_data["version"]
            if self.form.cleaned_data["draw"]:
                filters["draw__icontains"] = self.form.cleaned_data["draw"]
            if self.form.cleaned_data["name"]:
                filters["name__icontains"] = self.form.cleaned_data["name"]
            files = ProjectFiles.objects.filter(**filters)

        if hasattr(self, "form") and self.form.cleaned_data["csv_export"]:
            formatted_projects = []
            for _file in files:
                upload_file = "N/A"
                date = _file.upload_date.strftime("%d/%m/%Y %H:%M:%S")
                upload_file = os.path.basename(_file.project_file.name)
                formatted_projects.append(
                    (
                        _file.project.identifier,
                        _file.project.name,
                        upload_file,
                        date,
                        _file.uploaded_by,
                        _file.draw,
                        _file.version,
                        _file.name,
                        _file.comments,
                        _file.statuses[_file.status],
                    )
                )
            return formatted_projects
        elif self.request.method == "POST":
            return files

    def get_title(self):
        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        if self.service_order:
            title = "Relatório de Arquivos"
        if self.start_date != self.end_date:
            title += "de %s a %s" % (start_date, end_date)
        else:
            title += "de %s" % start_date

        return title

    def get_csv_filename(self):
        if self.start_date != self.end_date:
            filename = "Relatorio_Arquivos_%s_a_%s.csv"
            filename = filename % (self.start_date, self.end_date)
        else:
            filename = "Relatorio_Arquivos_%s.csv" % self.start_date
        return filename + ".csv"
