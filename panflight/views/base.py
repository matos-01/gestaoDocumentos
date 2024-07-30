
import csv
import datetime

from decimal import Decimal

from django.http import HttpResponse
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView


def export_to_csv(report, header, filename):
    """ Receives a list of iterables and generates an HttpResponse
    containing a CSV file with the list's content
    """
    if not report:
        pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    writer = csv.writer(response, delimiter=';')
    response.write('\ufeff'.encode('utf-8'))
    if header:
        writer.writerow(header)

    for line in report:
        row = []
        for element in line:
            if type(element) is str:
                element = element.replace('\n', ' ').replace('\r', ' ').replace('\u2013', '-') \
                                 .replace('\u2019', '').replace('\u2014', '') \
                                 .replace('\u2010', '').replace('\u201c', '') \
                                 .replace('\u201d', '')
            elif type(element) is datetime.datetime:
                element = element.strftime('%d/%m/%Y %H:%M:%S')
            elif type(element) is datetime.date:
                element = element.strftime('%d/%m/%Y')
            elif type(element) is float:
                element = str(element)
                element = element.replace('.', ',')
            row.append(element)

        writer.writerow(row)

    return response


class FormListView(FormMixin, ListView):
    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.object_list = []
        context = self.get_context_data(form=form, object_list=self.object_list)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        if not self.form.is_valid():
            self.object_list = []
            context = self.get_context_data(errors=self.form.errors,
                                            form=self.form,
                                            object_list=self.object_list)
            return self.render_to_response(context)
        if ('csv_export' in list(self.form.cleaned_data.keys())
                and self.form.cleaned_data['csv_export']):
            return self.csv_export()

        self.object_list = self.get_queryset()
        context = self.get_context_data(form=self.form,
                                        object_list=self.object_list)
        return self.render_to_response(context)

    def csv_export(self):
        data = self.get_queryset()
        if not data:
            error = 'Não é possível exportar para CSV um relatório vazio'
            form = self.get_form(self.get_form_class())
            self.object_list = data
            context = self.get_context_data(form=form, object_list=data, errors=error)
            return self.render_to_response(context)

        return export_to_csv(data, self.get_csv_header(), self.get_csv_filename())

    def get_csv_header(self):
        return self.csv_header

    def get_csv_filename(self):
        return self.csv_filename

    def get_title(self):
        if hasattr(self, 'title'):
            return self.title
        else:
            return ''
