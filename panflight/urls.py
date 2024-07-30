"""panflight URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from panflight.views.rest import (ChangeProjectStatusRESTView,
                                  ChangeFileStatusRESTView,
                                  CheckFileNameRESTView,
                                  CheckFileVersionRESTView,
                                  CreateFolderRESTView,
                                  DocumentCategoryRESTView,
                                  DownloadFilesRESTView,
                                  OpenFolderRESTView)
from panflight.views.views import( CreateNewsView,
                                   CreateProjectView,
                                   DocumentDetailsView,
                                   DocumentListView,
                                   DocumentUploadView,
                                   HomeView,
                                   LoginView,
                                   LogoutView,
                                   NewsListView,
                                   ProjectDetailsView,
                                   ProjectFilesDetailsView,
                                   ProjectFilesUploadView,
                                   ProjectListView)
from panflight.views.reports import ProjectActivityReportView, ProjectFilesReportView, ProjectReportView

admin.autodiscover()

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('projeto/novo/', CreateProjectView.as_view(), name='create_project'),
    path('projeto/detalhes/<slug:pk>', ProjectDetailsView.as_view(), name='project_details'),
    path('admin/', admin.site.urls),
    path('projeto/upload_arquivo/<slug:pk>', ProjectFilesUploadView.as_view(), name='project_file_upload'),
    path('projeto/upload_arquivo/<slug:pk>/<slug:id>', ProjectFilesUploadView.as_view(),
         name='project_file_upload_category'),
    path('projeto/arquivo/<slug:pk>', ProjectFilesDetailsView.as_view(), name='project_file_details'),
    path('noticia/nova/', CreateNewsView.as_view(), name='create_news'),
    path('noticia/lista/', NewsListView.as_view(), name='news_list'),
    path('projeto/lista/<slug:_type>', ProjectListView.as_view(), name='project_list'),
    path('projeto/rest/criar_pasta', CreateFolderRESTView.as_view(), name='create_folder_rest'),
    path('projeto/rest/trocar_status', ChangeProjectStatusRESTView.as_view(), name='change_status_rest'),
    path('projeto/arquivo/rest/trocar_status', ChangeFileStatusRESTView.as_view(), name='change_file_status_rest'),
    path('relatorios/projetos', ProjectReportView.as_view(), name='project_report'),
    path('relatorios/atividades', ProjectActivityReportView.as_view(), name='activity_report'),
    path('relatorios/arquivos', ProjectFilesReportView.as_view(), name='files_report'),
    path('documento/lista/<slug:category>', DocumentListView.as_view(), name='document_list'),
    path('documento/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('document/upload/<slug:pk>', DocumentUploadView.as_view(), name='document_upload_revision'),
    path('documento/detalhes/<slug:pk>', DocumentDetailsView.as_view(), name='document_details'),
    path('documento/rest/categorias', DocumentCategoryRESTView.as_view(), name='document_category_rest'),
    path('projeto/rest/abrir_editaveis', OpenFolderRESTView.as_view(), name='open_folder_rest'),
    path('projeto/rest/download_arquivos', DownloadFilesRESTView.as_view(), name='download_all'),
    path('projeto/rest/checa_versao_arquivos', CheckFileVersionRESTView.as_view(),
        name='check_file_version_rest'),
    path('projeto/rest/checa_nome_arquivos', CheckFileNameRESTView.as_view(),
        name='check_file_name_rest'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
