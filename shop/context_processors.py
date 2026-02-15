from .models import Panier, ElementPanier

def panier_count(request):
    if not request.session.session_key:
        request.session.create()

    cle = request.session.session_key

    try:
        panier = Panier.objects.get(cle_session=cle)
        count = ElementPanier.objects.filter(panier=panier).count()
    except Panier.DoesNotExist:
        count = 0

    return {'panier_count': count}
