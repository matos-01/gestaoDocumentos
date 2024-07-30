from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group, User


from panflight.models.documents import Document, DocumentCategory, DocumentSubCategory, UserCategory
from panflight.models.projects import (Department,
                                       DepartmentName,
                                       News,
                                       Project,
                                       ProjectActivity,
                                       ProjectFiles,
                                       ProjectTemplate,
                                       ProjectTemplateFolder)


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'start_date', )
    search_fields = ('title', 'description', )


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'original_pn', 'panflight_pn', 'creation_date', 'status_field')
    search_fields = ('identifier', 'name', 'original_pn', 'panflight_pn',)

    def status_field(self, obj):
        return Project.statuses[obj.status]
    status_field.short_description = 'Status'

class ProjectActivityAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'event_field', 'date')
    search_fields = ('user', 'project')

    def event_field(self, obj):
        return ProjectActivity.events[obj.event]
    event_field.short_description = 'Evento'


class ProjectFilesAdmin(admin.ModelAdmin):
    list_display = ('name', 'draw', 'version', 'uploaded_by', 'upload_date', 'status_field')
    search_fields = ('name', 'draw', )

    def status_field(self, obj):
        return ProjectFiles.statuses[obj.status]
    status_field.short_description = 'Status'


class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'active',)
    search_fields = ('template_name',)
    filter_horizontal = ('folders',)


class ProjectTemplateFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',)
    search_fields = ('name',)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'status', 'uploaded_by', 'expiration_date')
    search_fields = ('name',)

    def status_field(self, obj):
        return Document.statuses[obj.status]
    status_field.short_description = 'Status'


class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    search_fields = ('name', )


class DocumentSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_field', 'active')
    search_fields = ('name', )
    
    def category_field(self, obj):
        category = DocumentCategory.objects.get(id=obj.category.id)
        return category.name
    category_field.short_description = 'Categoria'


class DepartmentNameAdmin(admin.ModelAdmin):
    list_display = ('name',)


class MyUserChangeForm(UserChangeForm):
    department = forms.ChoiceField(choices=[])
    password_user = forms.CharField()
    def __init__(self, *args, **kwargs):
        super(MyUserChangeForm, self).__init__(*args, **kwargs)
        self.fields['department'].label = 'Departamento'
        self.fields['department'].choices = [('0', '')] + list((i.id, i.name) for i in DepartmentName.objects.all())
        self.fields['password_user'].label = 'Senha'
        try:
            initial = Department.objects.get(user__id=self.instance.pk)
            self.fields['department'].initial = initial.department.id
        except:
            self.fields['department'].initial = 0
        try:
            user = User.objects.get(id=self.instance.pk)
            if user.password:
                self.fields['password_user'].initial = user.password
                self.fields['password_user'].widget.attrs['readonly'] = True
            else:
                self.fields['password_user'].initial = ''
            if user.is_superuser:
                self.fields['password_user'].widget.attrs['readonly'] = False
        except:
                self.fields['password_user'].initial = ''


class UserAdmin(admin.ModelAdmin):
    form = MyUserChangeForm

    def get_form(self, request, *args, **kwargs):
        form = super(UserAdmin, self).get_form(request, *args, **kwargs)
        form.current_user = request.user
        return form

    def save_model(self, request, obj, form, change):
        obj.save()
        user = User.objects.get(id=obj.id)
        if not user.password:
            password = form.cleaned_data.get('password_user')
            user.set_password(password)
            user.save()
            password = form.cleaned_data.get('password_user')
        else: 
            password = form.cleaned_data.get('password_user')
            if str(password) != str(user.password):
                print('alterou')
                user.set_password(password)
                user.save()
        if form.cleaned_data.get('department'):
            department_id = form.cleaned_data.get('department')
            try:
                user_department = Department.objects.get(user__id=obj.pk)
                user_department.delete()
            except:
                pass
            department = DepartmentName.objects.get(id=department_id)
            Department.objects.create(department=department, user=obj)


class UserSetInline(admin.TabularInline):
    model = User.groups.through
    raw_id_fields = ('user',)  # optional, if you have too many users


class MyGroupAdmin(GroupAdmin):
    inlines = [UserSetInline]

admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)
admin.site.unregister(User)
admin.site.register(DepartmentName, DepartmentNameAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentCategory, DocumentCategoryAdmin)
admin.site.register(DocumentSubCategory, DocumentSubCategoryAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectActivity, ProjectActivityAdmin)
admin.site.register(ProjectFiles, ProjectFilesAdmin)
admin.site.register(ProjectTemplate, ProjectTemplateAdmin)
admin.site.register(ProjectTemplateFolder, ProjectTemplateFolderAdmin)
admin.site.register(User, UserAdmin)
