import json
import os
import io
import webbrowser
import zipfile

from django.http import HttpResponse
from django.views.generic import View

from panflight.models.documents import Document, DocumentCategory
from panflight.models.projects import Department, Project, ProjectActivity, ProjectFiles
from panflight.settings import MEDIA_ROOT


class CreateFolderRESTView(View):
    def get(self, request):
        success = False
        error = None
        try:
            project_id = request.GET["project_id"]
            folder_name = request.GET["folder_name"]
            project = Project.objects.get(id=project_id)
            project_folder = Project.get_project_folder(project)
            os.mkdir(os.path.join(MEDIA_ROOT, project_folder, folder_name))
            success = True
        except Exception as e:
            error = str(e)
        response_data = {"success": success, "error": error}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class ChangeProjectStatusRESTView(View):
    def get(self, request):
        success = False
        error = None
        project_id = request.GET["project_id"]
        status = int(request.GET["status"])
        reason = request.GET["reason"]
        try:
            _type = request.GET["type"]
        except:
            _type = None
        if reason:
            reason = reason.upper()
        if not _type:
            project = Project.objects.get(id=project_id)
            if status == 1:
                project.status = Project.STATUS_EXECUTION
                ProjectActivity.objects.create(
                    event=ProjectActivity.EVENT_START,
                    project=project,
                    user=self.request.user,
                )
            elif status == 3:
                project.status = Project.STATUS_COMPLETED
                ProjectActivity.objects.create(
                    event=ProjectActivity.EVENT_COMPLETE,
                    project=project,
                    user=self.request.user,
                )

            elif status == 2:
                project.status = Project.STATUS_PAUSED
                ProjectActivity.objects.create(
                    event=ProjectActivity.EVENT_PAUSE,
                    project=project,
                    user=self.request.user,
                    reason=reason,
                )
            elif status == 4:
                project.status = Project.STATUS_CANCELED
                ProjectActivity.objects.create(
                    event=ProjectActivity.EVENT_CANCEL,
                    project=project,
                    user=self.request.user,
                    reason=reason,
                )
            super(Project, project).save()
        else:
            document = Document.objects.get(id=project_id)
            if status == 2:
                document.status = Document.STATUS_APPROVED
                last_activity = ProjectActivity(
                    event=ProjectActivity.EVENT_APPROVAL,
                    document=document,
                    user=self.request.user,
                    reason=reason,
                )
                last_activity.save()
                document.last_activity = last_activity
                recipients = (
                    document.uploaded_by.email,
                    document.approver.email,
                )
                subject = "Gestor de Documentos - Documento {} Aprovado"
                subject = subject.format(document.name)
                message = "O documento {} - {} foi aprovado por  {}."
                message = message.format(
                    document.code, document.name, document.approver.username
                )
                if recipients:
                    try:
                        send_mail(
                            subject,
                            message,
                            "gestordocumentos@panflight.com",
                            recipients,
                        )
                    except:
                        pass
            elif status == 3:
                document.status = Document.STATUS_REVISION
                last_activity = ProjectActivity(
                    event=ProjectActivity.EVENT_REVISION,
                    document=document,
                    user=self.request.user,
                    reason=reason,
                )
                last_activity.save()
                document.last_activity = last_activity
                recipients = (
                    document.uploaded_by.email,
                    document.approver.email,
                )
                subject = "Gestor de Documentos - Documento {} Enviado Para Revisão"
                subject = subject.format(document.name)
                message = (
                    "O documento {} - {} foi enviado para revisão pelo usuário  {}.\n"
                )
                message += "Motivo: {}\nVerifique o link abaixo para mais detalhes:\n"
                message += "http://SERVIDOR01/documento/detalhes/14"
                message = message.format(
                    document.code, document.name, document.approver.username, reason
                )
                if recipients:
                    try:
                        send_mail(
                            subject,
                            message,
                            "gestordocumentos@panflight.com",
                            recipients,
                        )
                    except:
                        pass
            elif status == 5:
                document.status = Document.STATUS_CANCELED
                last_activity = ProjectActivity(
                    event=ProjectActivity.EVENT_CANCEL,
                    document=document,
                    user=self.request.user,
                    reason=reason,
                )
                last_activity.save()
                document.last_activity = last_activity
            super(Document, document).save()

        success = True
        response_data = {"success": success, "error": error}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class DocumentCategoryRESTView(View):
    def get(self, request):
        categories = list(
            DocumentCategory.objects.all().order_by("name").values_list("name")
        )
        response_data = {"categories": categories}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class ChangeFileStatusRESTView(View):
    def get(self, request):
        success = False
        file_id = request.GET["file_id"]
        status = request.GET["status"]
        project_file = ProjectFiles.objects.get(id=file_id)
        project_file.status = status
        project_file.save()
        if status == 0:
            reason = "Arquivo Disponibilizado P/ Produção"
        else:
            reason = "Arquivo Removido da Produção"
        ProjectActivity.objects.create(
            event=ProjectActivity.EVENT_UPDATE,
            project=project_file.project,
            project_file=project_file,
            user=self.request.user,
            reason=reason,
        )
        success = True
        response_data = {"success": success}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class OpenFolderRESTView(View):
    def get(self, request):
        success = False
        error = None
        try:
            project_id = request.GET["project_id"]
            project = Project.objects.get(id=project_id)
            department = Department.objects.get(user=request.user)
            path = "//Servidor02/GestorDoc$/Projetos/%s - %s/%s/Editáveis"
            path = path % (project.identifier, project.name, department.name)
            webbrowser.open(os.path.realpath(path))
            success = True
        except Exception as e:
            error = str(e)
        response_data = {"success": success, "error": error}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class DownloadFilesRESTView(View):
    def get(self, request):
        success = True
        error = None
        id_files = list(self.request.GET.items())
        id_files = id_files[0][0]
        files = id_files.split("_")
        files.pop(0)
        zip_name = "arquivos_projeto"
        zip_filename = "%s.zip" % zip_name

        # Open StringIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        for _file in files:
            project_file = ProjectFiles.objects.get(id=_file)
            fpath = project_file.project_file.path
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(fname)

            # Add file, at correct path
            zf.write(fpath, zip_path)

        # Must close zip for all contents to be written
        zf.close()

        # Grab ZIP file from in-memory, make response with correct MIME-type

        resp = HttpResponse(s.getvalue(), content_type="application/zip")
        # ..and correct content-disposition
        resp["Content-Disposition"] = "attachment; filename=%s" % zip_filename

        return resp


class CheckFileVersionRESTView(View):
    def get(self, request):
        same = False
        project_file_id = request.GET["project_file_id"]
        file_version = request.GET["version"]
        project_file = ProjectFiles.objects.get(id=project_file_id)
        if project_file.version == file_version:
            same = True
        response_data = {"same": same}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")


class CheckFileNameRESTView(View):
    def get(self, request):
        same = False
        project_file_id = request.GET["project_file_id"]
        file_name = request.GET["name"]
        project_file = ProjectFiles.objects.get(id=project_file_id)
        if project_file.name.lower() == file_name.lower():
            same = True
        response_data = {"same": same}
        json_data = json.dumps(response_data)
        return HttpResponse(content=json_data, content_type="application/json")
