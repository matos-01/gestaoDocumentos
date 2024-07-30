import datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from panflight.models.documents import Document

users = User.objects.all()
for user in users:
    document_list = []
    documents = Document.objects.filter(uploaded_by=user, status=Document.STATUS_VERIFIED)
    for document in documents:
        waiting_date = document.last_activity.date
        today = datetime.datetime.now()
        delta = abs(waiting_date - today).days
        if delta >= 1:
            document_list.append((document, delta))
    if document_list:
        message =  ('Olá %s!\nVim informar que o(s) documento(s) abaixo está(ão) aguardando sua aprovação:\n\n')
        message = message % (user.first_name)
        for document, delta in document_list:
            message += '%s | %s (%s dia(s) - http://SERVIDOR01/documento/detalhes/%s\n'
            message = message % (document.code, document.name, delta, document.id)
        message += '\nTenha um ótimo dia!\nSistema de Gestão de Documentos - Panflight'
        subject = 'Gestor de Documents - Documentos Próximos de Expiração'
        recipients = (user.email, )
        try:
            send_mail(subject, message, 'gestordocumentos@panflight.com', recipients)
        except Exception as e:
            print(str(e))
