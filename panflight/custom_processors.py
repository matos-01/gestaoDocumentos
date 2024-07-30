from panflight.models.documents import DocumentCategory, DocumentSubCategory

def categories_processor(request):
 categories = DocumentCategory.objects.all().order_by('name')
 subcategory = DocumentSubCategory.objects.all().order_by('name')
 return {'categories': categories,
         'subcategories': subcategory}
