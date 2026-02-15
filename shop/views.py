from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Panier, ElementPanier, Commande, ElementCommande, Commentaire, Confiance
from django.core.mail import send_mail
from django.contrib import messages
import threading
from django.db.models import Avg, Sum, Count, Prefetch
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncDate
from datetime import timedelta




#On crée la vue qui va s'affiche sur la page d'acceuil home navigation 
def home(request):
    products = Product.objects.all()
    confiance_list = Confiance.objects.all()


    return render(request, 'shop/index.html', {
        'products': products,
        'confiance_list': confiance_list,
    })



#envoyer panier non vide a toutes les pages 
def panier_context(request):
    panier = get_panier(request)
    panier_non_vide = ElementPanier.objects.filter(panier=panier).exists()
    return {'panier_non_vide': panier_non_vide}


#la fonction qui reirige vers panier.html
def panier(request):
    panier = get_panier(request)
    return render(request, 'shop/panier.html', {'panier': panier})



#fonction qui recupere le panier du visiteur
def get_panier(request):
    if not request.session.session_key:
        request.session.create()

    cle = request.session.session_key
    panier, created = Panier.objects.get_or_create(cle_session=cle)
    return panier


#la fct qui permet d'ajouter element au panier 
def ajouter_au_panier(request, product_id):
    produit = Product.objects.get(id=product_id)
    panier = get_panier(request)

    element, created = ElementPanier.objects.get_or_create(
        panier=panier,
        produit=produit
    )

    if not created:
        element.quantite += 1
        element.save()

    messages.success(request, "Success ! Produit ajouté au panier 🛒")
    return redirect('home')



#la fct qui permet d'augmenter la quantité de produit dans le panier 
def plus_quantite(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    element.quantite += 1
    element.save()
    return redirect('panier')


#la fct qui permet de diminuier la quantité de produit dans le panier 
def moins_quantite(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    if element.quantite > 1:
        element.quantite -= 1
        element.save()
    else:
        element.delete()
    return redirect('panier')


#la fct qui permet de supprimer un produit du panier 
def supprimer_element(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    element.delete()
    return redirect('panier')

#la fct qui permet d'acceder au page commander et de saisir le formulaire 
def page_commande(request):
    return render(request, 'shop/commande.html')


#
def envoyer_mail(message):
    send_mail(
        'Nouvelle commande SenGadget',
        message,
        'sengadget.sn@gmail.com',
        ['sengadget.sn@gmail.com'],
        fail_silently=True,
    )


#la vue qui enregistre la commande 
def valider_commande(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        panier = Panier.objects.get(cle_session=request.session.session_key)
        elements = ElementPanier.objects.filter(panier=panier)
        elements_liste = list(elements)

        total = 0
        for e in elements_liste:
            total += e.produit.price * e.quantite

        commande = Commande.objects.create(
            nom_complet=nom,
            telephone=telephone,
            adresse=adresse,
            montant_total=total
        )

        for e in elements_liste:
            ElementCommande.objects.create(
                commande=commande,
                produit=e.produit,
                quantite=e.quantite,
                prix=e.produit.price
            )

        elements.delete()

            # ================== EMAIL NOTIFICATION ==================

        message = f"""
        Nouvelle commande SenGadget 🇸🇳

        Nom: {nom}
        Téléphone: {telephone}
        Adresse: {adresse}

        Produits commandés :
        """

        for e in elements_liste:
            message += f"- {e.produit.name} x {e.quantite} = {e.produit.price * e.quantite} FCFA\n"

        message += f"\nTotal: {total} FCFA"

        threading.Thread(target=envoyer_mail, args=(message,)).start()

        messages.success(
            request,
            "Votre commande a bien été prise en compte ✅. Vous serez contacter par notre service client dans les plus brefs délais."
        )

        return redirect('/')


#vue pour ajouter un commentaire 
def ajouter_commentaire(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        texte = request.POST.get('commentaire')
        note = request.POST.get('note')

        Commentaire.objects.create(
            nom=nom,
            commentaire=texte,
            note=note
        )
    return redirect('home')


#fct pour la page detail produit 
def detail_produit(request, id):
    produit = Product.objects.get(id=id)

    if request.method == "POST":
        nom = request.POST.get('nom')
        commentaire = request.POST.get('commentaire')
        note = request.POST.get('note')

        Commentaire.objects.create(
            produit=produit,
            nom=nom,
            commentaire=commentaire,
            note=note,
            actif=False  # très important (modération)
        )

    commentaires = produit.commentaires.filter(actif=True)

    moyenne = commentaires.aggregate(Avg('note'))['note__avg']
    moyenne = round(moyenne, 1) if moyenne else 0

    return render(request, 'shop/detail_produit.html', {
        'produit': produit,
        'commentaires': commentaires,
        'moyenne': moyenne
    })

def a_propos(request):
    return render(request, 'shop/a_propos.html')


def contact(request):
    return render(request, 'shop/contact.html')

def confidentialites(request):
    return render(request, 'shop/confidentialite.html')

def mentions_legal(request):
    return render(request, 'shop/mentions_legal.html')





#vue pour changer le statut d'une commande depuis dashboard
@staff_member_required
def changer_statut(request, commande_id, nouveau_statut):
    commande = get_object_or_404(Commande, id=commande_id)
    commande.statut = nouveau_statut
    commande.save()

    # ✅ Si la commande est livrée → on retire le stock
    if nouveau_statut == 'livree':
        elements = ElementCommande.objects.filter(commande=commande)

        for element in elements:
            produit = element.produit
            produit.stock -= element.quantite
            produit.save()

    return redirect('dashboard')



#vue pour mon dashboard
@staff_member_required
def dashboard(request):
    aujourd_hui = timezone.now().date()

    commandes = (
        Commande.objects
        .all()
        .order_by('-date_commande')
        .prefetch_related(
            Prefetch(
                'elementcommande_set',
                queryset=ElementCommande.objects.select_related('produit')
            )
        )
    )


    statut = request.GET.get('statut')
    date = request.GET.get('date')
    telephone = request.GET.get('telephone')

    if statut:
        commandes = commandes.filter(statut=statut)

    if date:
        commandes = commandes.filter(date_commande__date=date)

    if telephone:
        commandes = commandes.filter(telephone__icontains=telephone)



    total_ventes = Commande.objects.filter(statut='livree').aggregate(
        total=Sum('montant_total')
    )['total'] or 0

    nombre_commandes = commandes.count()

    ventes_du_jour = Commande.objects.filter(
        statut='livree',
        date_commande__date=aujourd_hui
    ).count()

    # ====== DONNÉES POUR LE GRAPHIQUE (7 derniers jours) ======

    dates = []
    ventes_par_jour = []

    for i in range(6, -1, -1):
        jour = aujourd_hui - timezone.timedelta(days=i)

        total_jour = Commande.objects.filter(
            statut='livree',
            date_commande__date=jour
        ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0

        dates.append(jour.strftime("%d/%m"))
        ventes_par_jour.append(total_jour)

    
    #Classement des produits selon le plus vendues
    top_produits = (
        ElementCommande.objects
        .filter(commande__statut='livree')
        .values('produit__name')
        .annotate(total_vendu=Sum('quantite'))
        .order_by('-total_vendu')[:5]
    )

    # =======  =======
    
    aujourd_hui = timezone.now()
    debut_mois = aujourd_hui.replace(day=1)

    # Mois précédent
    fin_mois_precedent = debut_mois - timedelta(days=1)
    debut_mois_precedent = fin_mois_precedent.replace(day=1)

    # CA mois en cours
    ca_mois = Commande.objects.filter(
        statut='livree',
        date_commande__gte=debut_mois
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    # CA mois précédent
    ca_mois_precedent = Commande.objects.filter(
        statut='livree',
        date_commande__range=(debut_mois_precedent, fin_mois_precedent)
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    # Nombre commandes livrées ce mois
    commandes_mois = Commande.objects.filter(
        statut='livree',
        date_commande__gte=debut_mois
    ).count()

    # Produit le plus vendu du mois
    top_mois = (
        ElementCommande.objects
        .filter(
            commande__statut='livree',
            commande__date_commande__gte=debut_mois
        )
        .values('produit__name')
        .annotate(total_vendu=Sum('quantite'))
        .order_by('-total_vendu')
        .first()
    )

    # Pourcentage évolution
    evolution = 0
    if ca_mois_precedent > 0:
        evolution = ((ca_mois - ca_mois_precedent) / ca_mois_precedent) * 100




    context = {
        'commandes': commandes,
        'total_ventes': total_ventes,
        'nombre_commandes': nombre_commandes,
        'ventes_du_jour': ventes_du_jour,
        'dates': dates,
        'ventes_par_jour': ventes_par_jour,
        'top_produits': top_produits,
        'ca_mois': ca_mois,
        'commandes_mois': commandes_mois,
        'top_mois': top_mois,
        'evolution': round(evolution, 1),


    }


    return render(request, 'shop/dashboard.html', context)


#vue pour detail commande 
@staff_member_required
def detail_commande(request, id):
    commande = get_object_or_404(Commande, id=id)
    elements = ElementCommande.objects.filter(commande=commande)

    total = sum([e.sous_total() for e in elements])

    return render(request, 'shop/detail_commande.html', {
        'commande': commande,
        'elements': elements,
        'total': total
    })

