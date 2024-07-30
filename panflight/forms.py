# -*- coding: utf-8 -*-
# vi:si:et:sw=4:ts=4

from django import forms
from django.contrib.auth.models import Group, User

from panflight.models.documents import Document, DocumentSubCategory
from panflight.models.projects import Department, News, Project, ProjectActivity, ProjectFiles


def get_status_choices():
    status_choices = [('', 'Todos')]
    status_choices += list(Project.statuses.items())
    return status_choices

def get_event_choices():
    event_choices = [('', 'Todos')]
    event_choices += list(ProjectActivity.events.items())
    return event_choices

def get_user_choices():
    user_choices = [('', 'Todos')]
    user_choices += list(User.objects.all().values_list('id', 'username'))
    return user_choices

def get_status_file_choices():
    status_choices = [('', 'Todos')]
    status_choices += list(ProjectFiles.statuses.items())
    return status_choices

def get_category_choices():
    category_choices = [('', '')]
    category = list(DocumentSubCategory.objects.all())
    for item in category:
        category_choices.append((item.id, item.category.name + ' - ' + item.name))
    return category_choices


class HomeForm(forms.Form):
    search = forms.CharField(required=False)


class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['status', 'creation_date', 'responsible', 'panflight_pn']
        widgets = {
                'description': forms.Textarea(),
        }


class ProjectFilesUploadForm(forms.ModelForm):
    GROUP_CHOICES = [[group.id, group.name]
                      for group in Group.objects.all().order_by('name')]

    project_id = forms.CharField(required=False)
    status = forms.BooleanField(required=False)
    groups = forms.MultipleChoiceField(required=False,                        
                                       widget=forms.CheckboxSelectMultiple(),
                                       choices=GROUP_CHOICES)
    class Meta:
        CHOICES = list(ProjectFiles.statuses.items())
        model = ProjectFiles
        exclude = ['upload_date', 'uploaded_by', 'project', 'status']
        widgets = {
                'comments': forms.Textarea(),
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        exclude = ['creation_date', 'created_by', 'active']
        widgets = {
                'description': forms.Textarea(),
        }

class ProjectReportForm(forms.Form):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    status = forms.ChoiceField(choices=[], required=False)
    identifier = forms.CharField(required=False)
    name = forms.CharField(required=False)
    pn_panflight = forms.CharField(required=False)
    pn_original = forms.CharField(required=False)
    csv_export = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(ProjectReportForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = get_status_choices()


class ProjectActivityReportForm(forms.Form):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    event = forms.ChoiceField(choices=[], required=False)
    project_identifier = forms.CharField(required=False)
    reason = forms.CharField(required=False)
    csv_export = forms.BooleanField(required=False)
    user = forms.ChoiceField(choices=[], required=False)

    def __init__(self, *args, **kwargs):
        super(ProjectActivityReportForm, self).__init__(*args, **kwargs)
        self.fields['event'].choices = get_event_choices()
        self.fields['user'].choices = get_user_choices()


class ProjectFilesReportForm(forms.Form):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    status = forms.ChoiceField(choices=[], required=False)
    project_identifier = forms.CharField(required=False)
    version = forms.CharField(required=False)
    draw = forms.CharField(required=False)
    name = forms.CharField(required=False)
    csv_export = forms.BooleanField(required=False)
    uploaded_by = forms.ChoiceField(choices=[], required=False)

    def __init__(self, *args, **kwargs):
        super(ProjectFilesReportForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = get_status_file_choices()
        self.fields['uploaded_by'].choices = get_user_choices()


class DocumentUploadForm(forms.ModelForm):
    category = forms.ChoiceField(choices=[])
    document_id = forms.CharField(required=False)
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    perpetual = forms.BooleanField(required=False)
    send_approval = forms.BooleanField(initial=False, required=False)
    users = forms.CharField(required=False)
    approval_reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    class Meta:
        model = Document
        exclude = ['status', 'upload_date', 'uploaded_by']
        widgets = {
                'comments': forms.Textarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super(DocumentUploadForm, self).__init__(*args, **kwargs)
        self.fields['category'].choices = get_category_choices()
