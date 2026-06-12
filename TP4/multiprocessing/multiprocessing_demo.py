"""
TP4.2 - Programmation Concurrente avec Multiprocessing
Utilisation de multiples processus CPU pour le vrai parallélisme
(contourne le GIL de Python)
"""

import multiprocessing
import time
import os
import math

# ============================================================
# FONCTIONS DE TEST (opérations CPU intensives)
# ============================================================

def calculer_factorielle(n):
    """Calcul intensif de factorielle"""
    resultat = math.factorial(n)
    return f"Factorielle({n}) = {resultat}"

def est_nombre_premier(n):
    """Test de primalité (opération CPU intensive)"""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def trouver_nombres_premiers(limite):
    """Trouve tous les nombres premiers jusqu'à une limite"""
    resultats = []
    for i in range(2, limite + 1):
        if est_nombre_premier(i):
            resultats.append(i)
    return resultats

def tache_cpu_intensive(identifiant, intensite):
    """Tâche CPU intensive"""
    pid = os.getpid()
    print(f"🔄 Processus {pid} - Tâche {identifiant}: début")
    
    start = time.time()
    
    # Calcul intensif
    resultat = 0
    for i in range(intensite):
        resultat += math.sqrt(i) * math.sin(i)
    
    end = time.time()
    
    print(f"✅ Processus {pid} - Tâche {identifiant}: fin ({end-start:.2f}s)")
    return resultat

# ============================================================
# EXEMPLE 1: Comparaison Séquentiel vs Multiprocessing
# ============================================================

def exemple_comparaison():
    """Compare l'exécution séquentielle vs parallèle avec multiprocessing"""
    print("\n" + "="*60)
    print("EXEMPLE 1: Comparaison Séquentiel vs Multiprocessing")
    print("="*60)
    
    # Liste de tâches CPU intensives
    intensites = [5000000, 5000000, 5000000, 5000000]
    
    # Version SÉQUENTIELLE
    print("\n📊 Version SÉQUENTIELLE:")
    start_seq = time.time()
    
    resultats_seq = []
    for i, intensite in enumerate(intensites):
        resultat = tache_cpu_intensive(i+1, intensite)
        resultats_seq.append(resultat)
    
    temps_seq = time.time() - start_seq
    print(f"\n⏱ Temps séquentiel: {temps_seq:.2f}s")
    
    # Version PARALLÈLE (Multiprocessing)
    print("\n📊 Version PARALLÈLE (Multiprocessing):")
    start_par = time.time()
    
    # Créer un pool de processus
    with multiprocessing.Pool(processes=4) as pool:
        # Soumettre toutes les tâches
        args = [(i+1, intensite) for i, intensite in enumerate(intensites)]
        resultats_par = pool.starmap(tache_cpu_intensive, args)
    
    temps_par = time.time() - start_par
    
    print(f"\n⏱ Temps parallèle: {temps_par:.2f}s")
    print(f"⚡ Accélération: {temps_seq/temps_par:.2f}x")

# ============================================================
# EXEMPLE 2: Map parallèle
# ============================================================

def exemple_map_parallele():
    """Utilisation de map pour paralléliser facilement"""
    print("\n" + "="*60)
    print("EXEMPLE 2: Map Parallèle avec Pool")
    print("="*60)
    
    # Tester la primalité de plusieurs nombres
    nombres_a_tester = [
        1000003, 1000033, 1000037, 1000039,
        1000081, 1000099, 1000117, 1000121
    ]
    
    print(f"\n🔢 Test de primalité de {len(nombres_a_tester)} nombres...")
    
    # Version séquentielle
    print("\n📊 Version SÉQUENTIELLE:")
    start_seq = time.time()
    resultats_seq = [est_nombre_premier(n) for n in nombres_a_tester]
    temps_seq = time.time() - start_seq
    print(f"   Temps: {temps_seq:.2f}s")
    
    # Version parallèle avec multiprocessing
    print("\n📊 Version PARALLÈLE (Map):")
    start_par = time.time()
    
    with multiprocessing.Pool(processes=4) as pool:
        resultats_par = pool.map(est_nombre_premier, nombres_a_tester)
    
    temps_par = time.time() - start_par
    print(f"   Temps: {temps_par:.2f}s")
    print(f"⚡ Accélération: {temps_seq/temps_par:.2f}x")
    
    # Afficher les résultats
    print("\n📊 RÉSULTATS:")
    for n, est_premier in zip(nombres_a_tester, resultats_par):
        print(f"   {n}: {'PREMIER' if est_premier else 'NON PREMIER'}")

# ============================================================
# EXEMPLE 3: Processus avec Queue (communication inter-processus)
# ============================================================

def producteur(queue, nombre_elements):
    """Producteur: génère des nombres et les met dans la queue"""
    pid = os.getpid()
    print(f"📦 Producteur ({pid}): démarrage")
    
    for i in range(nombre_elements):
        queue.put(i)
        time.sleep(0.1)
        print(f"📦 Producteur ({pid}): produit {i}")
    
    queue.put(None)  # Signal de fin
    print(f"✅ Producteur ({pid}): terminé")

def consommateur(queue, nom):
    """Consommateur: récupère les nombres de la queue et les traite"""
    pid = os.getpid()
    print(f"🔄 Consommateur {nom} ({pid}): démarrage")
    
    while True:
        item = queue.get()
        if item is None:
            queue.put(None)  # Remettre le signal pour les autres consommateurs
            break
        
        # Traiter l'élément
        resultat = item * item
        print(f"🔄 Consommateur {nom}: {item}² = {resultat}")
    
    print(f"✅ Consommateur {nom}: terminé")

def exemple_producteur_consommateur():
    """Exemple classique producteur-consommateur avec multiprocessing"""
    print("\n" + "="*60)
    print("EXEMPLE 3: Producteur-Consommateur avec Queue")
    print("="*60)
    
    # Créer une queue partagée
    queue = multiprocessing.Queue()
    
    # Créer les processus
    p_producteur = multiprocessing.Process(
        target=producteur, 
        args=(queue, 10)
    )
    
    p_consommateur1 = multiprocessing.Process(
        target=consommateur, 
        args=(queue, "A")
    )
    
    p_consommateur2 = multiprocessing.Process(
        target=consommateur, 
        args=(queue, "B")
    )
    
    # Démarrer les processus
    p_producteur.start()
    p_consommateur1.start()
    p_consommateur2.start()
    
    # Attendre la fin
    p_producteur.join()
    p_consommateur1.join()
    p_consommateur2.join()
    
    print("\n✅ Producteur-Consommateur terminé")

# ============================================================
# EXEMPLE 4: Valeurs et tableaux partagés
# ============================================================

def incrementer_compteur(compteur_partage, lock, iterations):
    """Incrémente un compteur partagé"""
    for _ in range(iterations):
        with lock:  # Verrou pour éviter les conditions de course
            compteur_partage.value += 1

def exemple_memoire_partagee():
    """Utilisation de mémoire partagée entre processus"""
    print("\n" + "="*60)
    print("EXEMPLE 4: Mémoire Partagée entre Processus")
    print("="*60)
    
    # Créer un compteur partagé
    compteur = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    
    # Créer plusieurs processus qui incrémentent le compteur
    processus = []
    for i in range(4):
        p = multiprocessing.Process(
            target=incrementer_compteur,
            args=(compteur, lock, 1000)
        )
        processus.append(p)
        p.start()
    
    # Attendre tous les processus
    for p in processus:
        p.join()
    
    print(f"\n📊 Valeur finale du compteur: {compteur.value}")
    print(f"   (Devrait être 4000 si pas de condition de course)")

# ============================================================
# EXEMPLE 5: Pool avec callback
# ============================================================

def traitement_parallele_avec_callback():
    """Utilisation de callbacks avec Pool"""
    print("\n" + "="*60)
    print("EXEMPLE 5: Pool avec Callbacks")
    print("="*60)
    
    # Liste de nombres pour factorielle
    nombres = [100, 200, 300, 400, 500, 600]
    
    # Fonction pour collecter les résultats
    resultats = []
    
    def collecter_resultat(resultat):
        resultats.append(resultat)
        print(f"📥 Résultat reçu: {resultat[:50]}...")
    
    print(f"\n🔢 Calcul des factorielles pour {nombres}")
    print("📊 Execution parallèle...")
    
    start = time.time()
    
    with multiprocessing.Pool(processes=4) as pool:
        # Soumettre les tâches avec callback
        for n in nombres:
            pool.apply_async(
                calculer_factorielle,
                args=(n,),
                callback=collecter_resultat
            )
        
        # Fermer et attendre
        pool.close()
        pool.join()
    
    temps = time.time() - start
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Nombre de résultats: {len(resultats)}")
    print(f"   Temps total: {temps:.2f}s")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🐍 TP4.2 - Multiprocessing en Python")
    print("="*60)
    print(f"🖥️ CPU Cœurs disponibles: {multiprocessing.cpu_count()}")
    
    # Exécuter les exemples
    exemple_comparaison()
    exemple_map_parallele()
    exemple_producteur_consommateur()
    exemple_memoire_partagee()
    traitement_parallele_avec_callback()
    
    print("\n" + "="*60)
    print("✅ TP4.2 TERMINÉ")
    print("="*60)