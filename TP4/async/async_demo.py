"""
TP4.3 - Programmation Asynchrone avec Async/Await
Pour les opérations I/O bound (réseau, fichiers, API)
"""

import asyncio
import aiohttp
import time
import random

# ============================================================
# EXEMPLE 1: Bases de async/await
# ============================================================

async def tache_asynchrone(nom, duree):
    """Tâche asynchrone qui simule une opération I/O"""
    print(f"🔄 Début de {nom} (durée: {duree}s)")
    await asyncio.sleep(duree)  # Simule une attente I/O
    print(f"✅ Fin de {nom}")
    return f"Résultat de {nom}"

async def exemple_basique():
    """Exemple basique d'exécution asynchrone"""
    print("\n" + "="*50)
    print("EXEMPLE 1: Async/Await basique")
    print("="*50)
    
    # Exécution séquentielle
    print("\n📊 Version SÉQUENTIELLE:")
    start = time.time()
    
    resultat1 = await tache_asynchrone("Tâche A", 2)
    resultat2 = await tache_asynchrone("Tâche B", 1)
    
    print(f"Temps total: {time.time()-start:.2f}s")
    
    # Exécution parallèle (concurrente)
    print("\n📊 Version CONCURRENTE (asyncio.gather):")
    start = time.time()
    
    resultats = await asyncio.gather(
        tache_asynchrone("Tâche C", 2),
        tache_asynchrone("Tâche D", 1)
    )
    
    print(f"Temps total: {time.time()-start:.2f}s")

# ============================================================
# EXEMPLE 2: Simulation d'appels API
# ============================================================

async def appel_api(nom, duree):
    """Simule un appel API avec latence variable"""
    print(f"🌐 API {nom}: appel en cours...")
    await asyncio.sleep(duree)
    return f"API {nom} a répondu en {duree}s"

async def exemple_appels_api():
    """Simulation d'appels API parallèles"""
    print("\n" + "="*50)
    print("EXEMPLE 2: Appels API parallèles")
    print("="*50)
    
    # Liste des APIs avec leurs latences
    apis = [
        ("Weather API", 1.5),
        ("User API", 0.8),
        ("Payment API", 2.0),
        ("Notification API", 0.5)
    ]
    
    print("\n📊 Appels API en parallèle:")
    start = time.time()
    
    # Créer toutes les tâches
    taches = [appel_api(nom, duree) for nom, duree in apis]
    
    # Exécuter en parallèle
    resultats = await asyncio.gather(*taches)
    
    temps_total = time.time() - start
    
    print(f"\n📊 RÉSULTATS:")
    for r in resultats:
        print(f"   {r}")
    print(f"⏱ Temps total: {temps_total:.2f}s")
    print(f"   (Si c'était séquentiel: {sum(d for _,d in apis):.2f}s)")

# ============================================================
# EXEMPLE 3: Web Scraping asynchrone (simulé)
# ============================================================

async def scraper_url(url, duree):
    """Simule le scraping d'une URL"""
    print(f"🔍 Scraping de {url}...")
    await asyncio.sleep(duree)
    return f"Scrapé {url}: trouvé {random.randint(10, 100)} liens"

async def exemple_scraping():
    """Simulation de scraping parallèle"""
    print("\n" + "="*50)
    print("EXEMPLE 3: Web Scraping Parallèle")
    print("="*50)
    
    urls = [
        ("https://example.com/page1", 1.2),
        ("https://example.com/page2", 0.8),
        ("https://example.com/page3", 1.5),
        ("https://example.com/page4", 0.6),
        ("https://example.com/page5", 1.0),
    ]
    
    print(f"\n🔗 Scraping de {len(urls)} URLs:")
    start = time.time()
    
    taches = [scraper_url(url, duree) for url, duree in urls]
    resultats = await asyncio.gather(*taches)
    
    temps_total = time.time() - start
    
    print(f"\n📊 RÉSULTATS:")
    for r in resultats:
        print(f"   {r}")
    print(f"⏱ Temps total: {temps_total:.2f}s")

# ============================================================
# EXEMPLE 4: Timeouts et gestion d'erreurs
# ============================================================

async def service_lent(nom, duree):
    """Service qui peut être lent"""
    print(f"🔄 Service {nom}: démarrage (prévu: {duree}s)")
    await asyncio.sleep(duree)
    return f"Service {nom}: terminé"

async def exemple_timeouts():
    """Gestion des timeouts avec asyncio"""
    print("\n" + "="*50)
    print("EXEMPLE 4: Timeouts et Gestion d'Erreurs")
    print("="*50)
    
    services = [
        ("A", 1, 2),   # (nom, durée, timeout)
        ("B", 3, 2),   # Ce service va timeout
        ("C", 1.5, 2),
        ("D", 4, 2),   # Ce service va timeout
    ]
    
    print("\n📊 Appels avec timeout de 2s:")
    
    async def appeler_avec_timeout(nom, duree, timeout):
        try:
            resultat = await asyncio.wait_for(
                service_lent(nom, duree),
                timeout=timeout
            )
            return {"nom": nom, "status": "succès", "resultat": resultat}
        except asyncio.TimeoutError:
            return {"nom": nom, "status": "timeout", "resultat": f"{nom} a dépassé {timeout}s"}
    
    taches = [appeler_avec_timeout(nom, duree, timeout) for nom, duree, timeout in services]
    resultats = await asyncio.gather(*taches)
    
    print("\n📊 RÉSULTATS:")
    for r in resultats:
        if r["status"] == "succès":
            print(f"   ✅ {r['resultat']}")
        else:
            print(f"   ⏰ {r['resultat']}")

# ============================================================
# EXEMPLE 5: Queue asynchrone (Producteur-Consommateur)
# ============================================================

async def producteur_async(queue, n_messages):
    """Producteur asynchrone"""
    for i in range(n_messages):
        message = f"Message {i+1}"
        await queue.put(message)
        print(f"📦 Produit: {message}")
        await asyncio.sleep(random.uniform(0.1, 0.5))
    
    await queue.put(None)  # Signal de fin

async def consommateur_async(queue, nom):
    """Consommateur asynchrone"""
    while True:
        message = await queue.get()
        if message is None:
            await queue.put(None)  # Propager le signal
            break
        
        print(f"🔄 Consommateur {nom}: traitement de {message}")
        await asyncio.sleep(random.uniform(0.2, 0.8))
        print(f"✅ Consommateur {nom}: {message} traité")

async def exemple_queue():
    """Exemple de queue asynchrone"""
    print("\n" + "="*50)
    print("EXEMPLE 5: Queue Asynchrone")
    print("="*50)
    
    queue = asyncio.Queue()
    
    # Créer les coroutines
    prod = producteur_async(queue, 10)
    cons1 = consommateur_async(queue, "A")
    cons2 = consommateur_async(queue, "B")
    
    # Exécuter en parallèle
    await asyncio.gather(prod, cons1, cons2)
    
    print("\n✅ Tous les messages ont été traités")

# ============================================================
# EXEMPLE 6: Simulateur de serveur web asynchrone
# ============================================================

class ServeurWebAsync:
    """Simulation d'un serveur web asynchrone"""
    
    def __init__(self):
        self.requetes_traitees = 0
    
    async def traiter_requete(self, requete_id, temps_traitement):
        """Traite une requête entrante"""
        print(f"📥 Requête {requete_id}: début du traitement")
        await asyncio.sleep(temps_traitement)
        self.requetes_traitees += 1
        print(f"📤 Requête {requete_id}: terminée ({temps_traitement}s)")
        return f"Réponse à la requête {requete_id}"
    
    async def gerer_connexion(self, requete_id, temps_traitement):
        """Gère une connexion client"""
        return await self.traiter_requete(requete_id, temps_traitement)

async def exemple_serveur():
    """Simulation d'un serveur web asynchrone"""
    print("\n" + "="*50)
    print("EXEMPLE 6: Serveur Web Asynchrone")
    print("="*50)
    
    serveur = ServeurWebAsync()
    
    # Simuler 10 requêtes concurrentes
    requetes = [
        (i+1, random.uniform(0.5, 2.0))
        for i in range(10)
    ]
    
    print(f"\n🌐 Arrivée de {len(requetes)} requêtes concurrentes...")
    start = time.time()
    
    # Traiter toutes les requêtes en parallèle
    taches = [serveur.gerer_connexion(req_id, temps) for req_id, temps in requetes]
    resultats = await asyncio.gather(*taches)
    
    temps_total = time.time() - start
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Requêtes traitées: {serveur.requetes_traitees}")
    print(f"   Temps total: {temps_total:.2f}s")
    print(f"   Débit moyen: {len(requetes)/temps_total:.1f} req/s")
    print(f"   (En séquentiel: {sum(t for _,t in requetes):.2f}s)")

# ============================================================
# MAIN
# ============================================================

async def main():
    """Fonction principale asynchrone"""
    print("="*60)
    print("🔄 TP4.3 - Programmation Asynchrone avec Async/Await")
    print("="*60)
    
    await exemple_basique()
    await exemple_appels_api()
    await exemple_scraping()
    await exemple_timeouts()
    await exemple_queue()
    await exemple_serveur()
    
    print("\n" + "="*60)
    print("✅ TP4.3 TERMINÉ")
    print("="*60)

if __name__ == "__main__":
    # Installer aiohttp si nécessaire
    # pip install aiohttp
    
    asyncio.run(main())