# -*- coding: utf-8 -*-
# vi:si:et:sw=4:ts=4
import datetime
import json

from braces.views import LoginRequiredMixin, PermissionRequiredMixin 

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect
# from django.shortcuts import render_to_response
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, FormMixin
from django.views.generic.list import ListView

from panflight.forms import (
    CreateProjectForm,
    DocumentUploadForm,
    HomeForm,
    NewsForm,
    ProjectFilesUploadForm,
)
from panflight.models.documents import Document, DocumentCategory, DocumentSubCategory
from panflight.models.projects import (
    Department,
    News,
    Project,
    ProjectActivity,
    ProjectFiles,
)
from panflight.views.base import FormListView


class HomeView(LoginRequiredMixin, FormListView):
    model = Project
    template_name = "index.html"
    login_url = "/login/"
    form_class = HomeForm

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)
        self.object_list = self.get_queryset()
        self.news_list = News.objects.filter(
            end_date__gte=datetime.datetime.today(), active=True
        )
        context = self.get_context_data(
            form=self.form, object_list=self.object_list, news_list=self.news_list
        )
        return self.render_to_response(context)

    def get_queryset(self):
        open_statuses = (
            Project.STATUS_NEW,
            Project.STATUS_EXECUTION,
        )
        qs = super(HomeView, self).get_queryset()
        qs = qs.filter(status__in=open_statuses).order_by("-creation_date")[:10]
        if hasattr(self.form, "data") and self.request.method == "POST":
            filters = {}
            search = self.form.data.get("search")
            if search:
                filters["identifier__icontains"] = search
            qs = Project.objects.filter(**filters).order_by("-creation_date")
        return qs


class LoginView(FormView):
    template_name = "login.html"
    form_class = AuthenticationForm
    success_url = "/"

    def __init__(self, *args, **kwargs):
        super(LoginView, self).__init__(*args, **kwargs)
        self.next = None

    def form_valid(self, form, *args, **kwargs):
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form, *args, **kwargs)

    def post(self, request):
        if "next" in list(request.GET.keys()):
            self.next = request.GET["next"]
        return super(LoginView, self).post(request)

    def get_success_url(self):
        if self.next:
            return self.next
        return super(LoginView, self).get_success_url()


class LogoutView(TemplateView):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class CreateProjectView(PermissionRequiredMixin, CreateView):
    model = Project
    form_class = CreateProjectForm
    login_url = '/login/'
    template_name = 'new_project.html'
    permission_required = ('panflight.add_project')

    def get_context_data(self, **kwargs):
        context = super(CreateProjectView, self).get_context_data(**kwargs)
        return context

    def form_invalid(self, form):
        error = True
        print("form invalid")
        return error

    def form_valid(self, form):
        try:
            with transaction.atomic():
                identifier = form.cleaned_data['identifier'].upper()
                original_pn = form.cleaned_data['original_pn'].upper()
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                description = form.cleaned_data['description'].upper()
                name = form.cleaned_data['name'].upper()
                panflight_pn = identifier
                responsible = self.request.user
                status = Project.STATUS_NEW
                template = form.cleaned_data["template"]
                if self.request.FILES:
                    image = self.request.FILES["media"]
                else:
                    image = None
                project = Project(
                    identifier="{:06d}".format(int(identifier)),
                    media=image,
                    original_pn=original_pn,
                    panflight_pn=panflight_pn,
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                    name=name,
                    status=status,
                    responsible=responsible,
                    template=template,
                )
                project.save()
                Project.create_folders(
                    project.identifier, project.name, project.template
                )
                ProjectActivity.objects.create(
                    user=responsible,
                    project=project,
                    event=ProjectActivity.EVENT_CREATE,
                )
                messages.success(
                    self.request, "Projeto %s Criado Com Sucesso!" % project.identifier
                )
        except Exception as e:
            print(str(e))
            messages.error(self.request, "Erro ao criar projeto: %s" % str(e))
        return self.render_to_response(self.get_context_data())


class ProjectDetailsView(PermissionRequiredMixin, DetailView):
    model = Project
    template_name = "project_details.html"
    login_url = "/login/"
    permission_required = "panflight.view_project"

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailsView, self).get_context_data(**kwargs)
        groups = self.request.user.groups.all()
        if self.request.user.is_superuser:
            context["project_files"] = ProjectFiles.objects.filter(
                project=self.object
            ).distinct("draw", "upload_date").order_by("draw", "upload_date")
        elif self.request.user.has_perm("panflight.view_projectfiles"):
            context["project_files"] = ProjectFiles.objects.filter(
                project=self.object, groups__in=groups
            ).distinct("draw", "upload_date").order_by("draw", "upload_date")
        else:
            context["project_files"] = (
                ProjectFiles.objects.filter(
                    project=self.object,
                    status=ProjectFiles.STATUS_PRODUCTION,
                    groups__in=groups,
                )
                .distinct("draw", "upload_date")
                .order_by("draw", "upload_date")
            )
        photos = []
        files = ProjectFiles.objects.filter(
            project=self.object, status=ProjectFiles.STATUS_PRODUCTION
        )
        for _file in files:
            file_path = _file.project_file.path
            if file_path.endswith((".jpg", ".png", ".bmp", ".gif", ".jpeg")):
                photos.append((_file.project_file.url))
        context["photos"] = photos
        department = Department.objects.get(user=self.request.user)
        context['department'] = department.department.name
        return context


class ProjectFilesUploadView(PermissionRequiredMixin, FormView):
    form_class = ProjectFilesUploadForm
    template_name = 'project_file_upload.html'
    login_url = '/login/'
    permission_required = ('panflight.add_projectfiles')

    def get(self, request, pk, id=False):
        self.object = Project.objects.get(id=pk)
        if id:
            self.draw = ProjectFiles.objects.get(id=id)
        return self.render_to_response(self.get_context_data())

    def post(self, request, pk, *args, **kwargs):
        self.object = Project.objects.get(id=pk)
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(ProjectFilesUploadView, self).get_context_data(**kwargs)
        try:
            context["object"] = self.object
            context["draw"] = self.draw
            context["name"] = self.name
        except:
            pass
        return context

    def form_valid(self, form):
        project_id = form.cleaned_data["project_id"]
        project = Project.objects.get(id=project_id)
        name = form.cleaned_data["name"].upper()
        draw = form.cleaned_data["draw"].upper()
        version = form.cleaned_data["version"].upper()
        comments = form.cleaned_data["comments"].upper()
        project_file = self.request.FILES["project_file"]
        status = form.cleaned_data["status"]
        group = form.cleaned_data["groups"]
        groups = Group.objects.filter(id__in=group)
        if status:
            status = ProjectFiles.STATUS_PRODUCTION
            files = ProjectFiles.objects.filter(
                draw=draw, status=ProjectFiles.STATUS_PRODUCTION
            )
            if files:
                for item in files:
                    item.status = ProjectFiles.STATUS_OBSOLETE
                    super(ProjectFiles, item).save()
        else:
            status = ProjectFiles.STATUS_PROGRESS
        context_data = self.get_context_data()
        project_files = ProjectFiles(
            name=name,
            draw=draw,
            version="{:02d}".format(int(version)),
            comments=comments,
            project_file=project_file,
            status=int(status),
            project=project,
            uploaded_by=self.request.user,
        )
        project_files.save()
        for item in groups:
            project_files.groups.add(item)
        ProjectActivity.objects.create(
            user=self.request.user,
            project=project_files.project,
            project_file=project_files,
            event=ProjectActivity.EVENT_UPLOAD,
        )
        messages.success(self.request, "Arquivo Carregado com Sucesso!")
        return self.render_to_response(self.get_context_data())


class CreateNewsView(PermissionRequiredMixin, CreateView):
    model = News
    form_class = NewsForm
    login_url = '/login/'
    template_name = 'create_news.html'
    permission_required = ('panflight.add_news')

    def get_context_data(self, **kwargs):
        context = super(CreateNewsView, self).get_context_data(**kwargs)
        return context

    def form_invalid(self, form):
        error = True
        return error

    def form_valid(self, form):
        try:
            with transaction.atomic():
                title = form.cleaned_data["title"].title()
                description = form.cleaned_data["description"]
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
                if self.request.FILES:
                    image = self.request.FILES["media"]
                else:
                    image = None
                news = News(
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    media=image,
                    created_by=self.request.user,
                )
                news.save()
                messages.success(
                    self.request, 'Notícia "%s" Criado Com Sucesso!' % news.title
                )
        except Exception as e:
            print(str(e))
            messages.error(self.request, "Erro ao criar notícia: %s" % str(e))
        return self.render_to_response(self.get_context_data())


class ProjectFilesDetailsView(PermissionRequiredMixin, DetailView):
    model = ProjectFiles
    template_name = "file_history.html"
    login_url = "/login/"
    permission_required = "panflight.view_projectfiles"

    def get_context_data(self, **kwargs):
        context = super(ProjectFilesDetailsView, self).get_context_data(**kwargs)
        context["object_list"] = ProjectFiles.objects.filter(
            project=self.object.project, draw=self.object.draw
        ).order_by("-upload_date")
        return context


class ProjectListView(PermissionRequiredMixin, ListView):
    model = Project
    template_name = 'project_list.html'
    permission_required = ('panflight.view_project')
    login_url = '/login/'

    def get(self, request, _type, *args, **kwargs):
        if _type == "novo":
            self.object_list = Project.objects.filter(status=Project.STATUS_NEW)
            self.list_status = "Novos"
        if _type == "execucao":
            self.object_list = Project.objects.filter(status=Project.STATUS_EXECUTION)
            self.list_status = "Em Execução"
        if _type == "concluidos":
            self.object_list = Project.objects.filter(status=Project.STATUS_COMPLETED)
            self.list_status = "Concluídos"
        if _type == "paralisados":
            self.object_list = Project.objects.filter(status=Project.STATUS_PAUSED)
            self.list_status = "Paralisados"
        if _type == "cancelados":
            self.object_list = Project.objects.filter(status=Project.STATUS_CANCELED)
            self.list_status = "Cancelados"
        if _type == "todos":
            self.object_list = Project.objects.all()
            self.list_status = "- Exibindo Todos os Projetos"
        context = self.get_context_data(
            object_list=self.object_list, list_status=self.list_status
        )
        return self.render_to_response(context)


class NewsListView(PermissionRequiredMixin, ListView):
    model = News
    template_name = "news_list.html"
    login_url = "/login/"
    permission_required = "panflight.view_project"

    def get_context_data(self, **kwargs):
        context = super(NewsListView, self).get_context_data(**kwargs)
        context["news"] = News.objects.filter(active=True).order_by("-creation_date")
        return context


class DocumentListView(PermissionRequiredMixin, ListView):
    model = Document
    template_name = "document_list.html"
    login_url = "/login/"
    permission_required = "panflight.view_document"

    def get(self, request, category, *args, **kwargs):
        try:
            self.object_list = Document.objects.filter(
                document_subcategory__id=category
            )
            self.category = DocumentSubCategory.objects.get(id=category)
            if not self.request.user.is_superuser:
                self.object_list = self.object_list.filter(status=2)
        except:
            self.object_list = Document.objects.all().order_by("upload_date")
            self.category = None
            if not self.request.user.is_superuser:
                self.object_list = self.object_list.filter(status=2)
        context = self.get_context_data(
            object_list=self.object_list, category=self.category
        )
        return self.render_to_response(context)


class DocumentUploadView(PermissionRequiredMixin, FormView):
    form_class = DocumentUploadForm
    template_name = 'document_upload.html'
    login_url = '/login/'
    permission_required = ('panflight.add_document')

    def get(self, request, pk=False):
        if pk:
            self.document = Document.objects.get(id=pk)
            activities = (
                ProjectActivity.objects.filter(document=self.document)
                .exclude(reason=None)
                .exclude(reason="")
                .order_by("date")
            )
            self.comment = None
            for item in activities:
                date = item.date.strftime("%d/%m/%Y %H:%M:%S")
                if not self.comment:
                    self.comment = (
                        item.reason + " (" + item.user.username + " - " + date + ")"
                    )
                else:
                    self.comment += (
                        "\n"
                        + item.reason
                        + " ("
                        + item.user.username
                        + " - "
                        + date
                        + ")"
                    )
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(DocumentUploadView, self).get_form_kwargs()
        try:
            if self.document:
                if not self.document.expiration_date:
                    perpetual = True
                else:
                    perpetual = False
                kwargs["initial"] = {
                    "code": self.document.code,
                    "name": self.document.name,
                    "version": self.document.version,
                    "expiration_date": self.document.expiration_date,
                    "comments": self.document.comments,
                    "category": self.document.document_subcategory.id,
                    "reason": self.comment,
                    "document_id": self.document.id,
                    "perpetual": perpetual,
                }
        except:
            pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(DocumentUploadView, self).get_context_data(**kwargs)
        approvers = list(User.objects.all().values_list("username", flat=True))
        json_list = json.dumps(approvers)
        context["approvers"] = json_list
        try:
            context["document"] = self.document
        except:
            pass
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                name = form.cleaned_data["name"].upper()
                version = form.cleaned_data["version"].upper()
                comments = form.cleaned_data["comments"].upper()
                try:
                    document_file = self.request.FILES["document_file"]
                except:
                    document_file = None
                expiration_date = form.cleaned_data["expiration_date"]
                code = form.cleaned_data["code"].upper()
                category = form.cleaned_data["category"]
                category = DocumentSubCategory.objects.get(id=int(category))
                context_data = self.get_context_data()
                document_id = form.cleaned_data["document_id"]
                send_approval = form.cleaned_data["send_approval"]
                approval_reason = form.cleaned_data["approval_reason"].upper()
                approver = form.cleaned_data["users"]
                try:
                    approver = User.objects.get(username=approver)
                except:
                    approver = None
                if send_approval:
                    status = Document.STATUS_VERIFIED
                else:
                    status = Document.STATUS_DRAFT
                if not document_id:
                    document = Document(
                        name=name,
                        code=code,
                        document_subcategory=category,
                        version="{:02d}".format(int(version)),
                        comments=comments,
                        document_file=document_file,
                        status=status,
                        uploaded_by=self.request.user,
                        expiration_date=expiration_date,
                        approver=approver,
                    )
                    document.save()
                    activity = ProjectActivity(
                        user=self.request.user,
                        document=document,
                        event=ProjectActivity.EVENT_CREATE,
                        reason=approval_reason,
                    )
                    activity.save()
                    document.last_activity = activity
                    document.save()
                else:
                    self.document = Document.objects.get(id=document_id)
                    self.document.name = name
                    self.document.code = code
                    self.document_subcategory = category
                    self.document.comments = comments
                    if send_approval:
                        self.document.status = Document.STATUS_VERIFIED
                        self.document.approver = approver
                        subject = (
                            "Gestor de Documentos - Documento %s Agd. Aprovação"
                            % self.document.code
                        )
                        message = (
                            "O Documento %s (%s) feito pelo usuário %s está "
                            "aguardando sua aprovação.\nPara visualizar, acesse o link abaixo:\n"
                            "http://SERVIDOR01/documento/detalhes/%s"
                        )
                        message = message % (
                            self.document.name,
                            self.document.document_subcategory,
                            self.document.uploaded_by,
                            self.document.id,
                        )
                        recepients = (self.document.approver.email,)
                        try:
                            send_mail(
                                subject,
                                message,
                                "gestordocumentos@panflight.com",
                                recepients,
                            )
                        except Exception as e:
                            print(str(e))
                            pass
                    else:
                        self.document.status = Document.STATUS_DRAFT
                    self.document.expiration_date = expiration_date
                    self.uploaded_by = self.request.user
                    if self.request.FILES:
                        self.document.document_file = document_file
                    self.document.save()
                    activity = ProjectActivity(
                        user=self.request.user,
                        document=self.document,
                        event=ProjectActivity.EVENT_UPDATE,
                        reason=approval_reason,
                    )
                    activity.save()
                    self.document.last_activity = activity
                    self.document.save()

                messages.success(self.request, "Documento Carregado com Sucesso!")
        except Exception as e:
            messages.error(self.request, "Erro ao Criar Documento: %s" % str(e))
        return self.render_to_response(self.get_context_data())


class DocumentDetailsView(PermissionRequiredMixin, DetailView):
    model = Document
    template_name = "document_details.html"
    permission_required = "panflight.view_document"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailsView, self).get_context_data(**kwargs)
        activity = ProjectActivity.objects.filter(document=self.object).order_by(
            "-date"
        )
        context["activity"] = activity
        return context
