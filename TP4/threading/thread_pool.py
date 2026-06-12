"""
TP4 - Programmation Concurrente avec Threading
Démonstration d'un pool de threads pour traiter des tâches en parallèle
"""

import threading
import time
import queue
import random

class ThreadPool:
    """Pool de threads pour exécuter des tâches en parallèle"""
    
    def __init__(self, num_workers=4):
        self.tasks = queue.Queue()
        self.workers = []
        self.running = True
        self.results = []
        self.results_lock = threading.Lock()
        
        print(f"📊 Création du pool avec {num_workers} workers")
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker, name=f"Worker-{i+1}")
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Fonction exécutée par chaque worker"""
        while self.running:
            try:
                # Récupérer une tâche avec timeout
                task_id, func, args, kwargs = self.tasks.get(timeout=1)
                
                print(f"🔄 [{threading.current_thread().name}] Début tâche {task_id}")
                start_time = time.time()
                
                # Exécuter la tâche
                result = func(*args, **kwargs)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Stocker le résultat
                with self.results_lock:
                    self.results.append({
                        'task_id': task_id,
                        'result': result,
                        'duration': duration,
                        'worker': threading.current_thread().name
                    })
                
                print(f"✅ [{threading.current_thread().name}] Fin tâche {task_id} ({duration:.2f}s)")
                self.tasks.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Erreur dans worker: {e}")
    
    def submit(self, func, *args, **kwargs):
        """Soumettre une tâche au pool"""
        task_id = len(self.results) + self.tasks.qsize() + 1
        self.tasks.put((task_id, func, args, kwargs))
        return task_id
    
    def wait_completion(self):
        """Attendre que toutes les tâches soient terminées"""
        self.tasks.join()
    
    def shutdown(self):
        """Arrêter tous les workers"""
        self.running = False
        for worker in self.workers:
            worker.join()
        print("🛑 Pool de threads arrêté")
    
    def get_results(self):
        """Récupérer tous les résultats"""
        return self.results

# ============================================================
# FONCTIONS DE TEST
# ============================================================

def tache_simple(duration, name):
    """Tâche simple avec une durée définie"""
    time.sleep(duration)
    return f"Tâche {name} terminée après {duration}s"

def calcul_intensif(n):
    """Calcul mathématique intensif"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

def tache_aleatoire():
    """Tâche avec durée aléatoire"""
    duration = random.uniform(0.5, 3)
    time.sleep(duration)
    return duration

# ============================================================
# EXEMPLES D'UTILISATION
# ============================================================

def exemple_1_taches_simples():
    """Exemple 1: Tâches simples avec différentes durées"""
    print("\n" + "="*50)
    print("EXEMPLE 1: Tâches avec différentes durées")
    print("="*50)
    
    pool = ThreadPool(num_workers=3)
    
    # Soumettre 5 tâches
    durations = [1, 2, 0.5, 1.5, 0.8]
    for i, d in enumerate(durations):
        pool.submit(tache_simple, d, f"T{i+1}")
    
    pool.wait_completion()
    pool.shutdown()
    
    print("\n📊 RÉSULTATS:")
    for r in pool.get_results():
        print(f"   Tâche {r['task_id']}: {r['result']} (par {r['worker']})")

def exemple_2_calcul_intensif():
    """Exemple 2: Calculs intensifs en parallèle"""
    print("\n" + "="*50)
    print("EXEMPLE 2: Calculs intensifs en parallèle")
    print("="*50)
    
    # Comparaison séquentiel vs parallèle
    valeurs = [100000, 200000, 300000, 400000]
    
    # Version séquentielle
    print("\n📊 Version SÉQUENTIELLE:")
    start = time.time()
    for v in valeurs:
        result = calcul_intensif(v)
        print(f"   calcul_intensif({v}) = {result}")
    seq_time = time.time() - start
    print(f"   ⏱ Temps séquentiel: {seq_time:.2f}s")
    
    # Version parallèle
    print("\n📊 Version PARALLÈLE (ThreadPool):")
    pool = ThreadPool(num_workers=4)
    start = time.time()
    
    for v in valeurs:
        pool.submit(calcul_intensif, v)
    
    pool.wait_completion()
    par_time = time.time() - start
    pool.shutdown()
    
    print(f"\n   ⏱ Temps parallèle: {par_time:.2f}s")
    print(f"   ⚡ Accélération: {seq_time/par_time:.2f}x")

def exemple_3_taches_aleatoires():
    """Exemple 3: Tâches avec durées aléatoires"""
    print("\n" + "="*50)
    print("EXEMPLE 3: Tâches aléatoires")
    print("="*50)
    
    pool = ThreadPool(num_workers=4)
    
    # Soumettre 8 tâches aléatoires
    for i in range(8):
        pool.submit(tache_aleatoire)
    
    pool.wait_completion()
    
    results = pool.get_results()
    total_time = sum(r['duration'] for r in results)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Nombre de tâches: {len(results)}")
    print(f"   Temps total CPU: {total_time:.2f}s")
    print(f"   Temps réel écoulé: {max(r['duration'] for r in results):.2f}s")
    
    pool.shutdown()

# ============================================================
# EXERCICE: SIMULATION DE REQUÊTES SERVEUR
# ============================================================

class ServeurWebSimule:
    """Simulation d'un serveur web qui traite des requêtes en parallèle"""
    
    def __init__(self, max_workers=10):
        self.pool = ThreadPool(max_workers)
        self.requetes_traitees = 0
        self.stats_lock = threading.Lock()
    
    def traiter_requete(self, requete_id, temps_traitement):
        """Simule le traitement d'une requête HTTP"""
        # Simuler le temps de traitement
        time.sleep(temps_traitement)
        
        with self.stats_lock:
            self.requetes_traitees += 1
        
        return f"Requête {requete_id} traitée en {temps_traitement}s"
    
    def soumettre_requete(self, requete_id, temps_traitement):
        """Soumettre une requête au pool"""
        return self.pool.submit(self.traiter_requete, requete_id, temps_traitement)
    
    def get_stats(self):
        return {
            'traitees': self.requetes_traitees,
            'file_attente': self.pool.tasks.qsize()
        }

def simulation_serveur():
    """Simulation d'un serveur web avec des requêtes entrantes"""
    print("\n" + "="*50)
    print("SIMULATION: Serveur Web avec ThreadPool")
    print("="*50)
    
    serveur = ServeurWebSimule(max_workers=5)
    
    # Simuler 15 requêtes avec différents temps de traitement
    requetes = [
        (1, 0.5), (2, 1.0), (3, 0.3), (4, 2.0), (5, 0.8),
        (6, 1.2), (7, 0.4), (8, 1.5), (9, 0.6), (10, 0.9),
        (11, 1.8), (12, 0.2), (13, 1.1), (14, 0.7), (15, 1.3)
    ]
    
    print(f"\n📥 Arrivée de {len(requetes)} requêtes...")
    start_time = time.time()
    
    # Soumettre toutes les requêtes
    for req_id, temps in requetes:
        serveur.soumettre_requete(req_id, temps)
        print(f"   Requête {req_id} soumise (temps estimé: {temps}s)")
    
    # Attendre la fin de toutes les requêtes
    serveur.pool.wait_completion()
    total_time = time.time() - start_time
    
    print(f"\n📊 RÉSULTATS SIMULATION:")
    print(f"   Requêtes traitées: {serveur.get_stats()['traitees']}")
    print(f"   Temps total: {total_time:.2f}s")
    print(f"   Débit moyen: {len(requetes)/total_time:.1f} req/s")
    
    serveur.pool.shutdown()

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🧵 TP4.1 - Programmation Concurrente avec Threading")
    print("="*60)
    
    # Exécuter les exemples
    exemple_1_taches_simples()
    exemple_2_calcul_intensif()
    exemple_3_taches_aleatoires()
    simulation_serveur()
    
    print("\n" + "="*60)
    print("✅ TP4.1 TERMINÉ")
    print("="*60)