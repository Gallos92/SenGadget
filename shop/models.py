from django.db import models

#le model produit 
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    stock = models.PositiveIntegerField(default=0) 
    
    def __str__(self):
        return self.name



#le model panier appartient a un visiteur meme sil na pas de compte 
class Panier(models.Model):
    cle_session = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)

    def total_panier(self):
        elements = self.elementpanier_set.all()
        return sum([e.sous_total() for e in elements])

    def __str__(self):
        return f"Panier {self.cle_session}"



#le model les elements d'un panier klkjonque un panier peut contenir plusieurs produits. stocke produit et quantite
class ElementPanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('panier', 'produit')

    def sous_total(self):
        return self.produit.price * self.quantite

    def __str__(self):
        return f"{self.produit.name} x {self.quantite}"



#le model commande quand le client confirme, stocke les infos client 
class Commande(models.Model):

    STATUT_CHOICES = [
        ('attente', 'En attente de confirmation'),
        ('confirmee', 'Confirmée par téléphone'),
        ('livree', 'Livrée au client'),
        ('annulee', 'Annulée'),
        ('refusee', 'Refusée à la livraison'),
    ]

    nom_complet = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    montant_total = models.IntegerField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='attente'
    )

    date_commande = models.DateTimeField(auto_now_add=True)
    
    def total_reel(self):
        return sum(e.sous_total() for e in self.elementcommande_set.all())

    def __str__(self):
        return f"Commande de {self.nom_complet}- {self.statut}"
    



#le model element commande stocke produit et quantite d'une commande 
class ElementCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix = models.PositiveIntegerField()

    def sous_total(self):
        return self.prix * self.quantite

    def __str__(self):
        return f"{self.produit.name} x {self.quantite}"


#le model commentaires pour les avis et produits 
class Commentaire(models.Model):
    produit = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='commentaires')
    nom = models.CharField(max_length=100)
    commentaire = models.TextField()
    note = models.IntegerField(default=5)
    date = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

#le model confiance pour ajouter les points necessaire pour la section nous faire confiance
class Confiance(models.Model):
    icone = models.CharField(max_length=50)  # ex: 'fa-shipping-fast'
    titre = models.CharField(max_length=100)
    description = models.TextField()

