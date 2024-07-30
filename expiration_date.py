import datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from panflight.models.documents import Document

users = User.objects.all()
for user in users:
    document_list = []
    documents = Document.objects.filter(uploaded_by=user).exclude(expiration_date=None)
    for document in documents:
        expiration_date = document.expiration_date
        today = datetime.date.today()
        delta = abs(expiration_date - today).days
        if delta < 0:
            document.status = Document.STATUS_EXPIRED
            document.save()
        elif delta <= 50 and delta >= 0:
            document_list.append((document, delta))
    if document_list:
        message =  ('Olá %s!\nVim informar que os documento(s) abaixo irá(ão) expirar em breve:\n\n')
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
