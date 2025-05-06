
import random
from collections import defaultdict


class AntColonyOptimizer:
    def __init__(self, graph, n_ants=20, n_iterations=50, decay=0.1, alpha=1, beta=2):
        self.graph = graph
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.decay = decay
        self.alpha = alpha  # Pheromone exponent
        self.beta = beta    # Heuristic exponent
        self.pheromone = defaultdict(float)
        
        # Initialize pheromones on edges
        for u, v in graph.edges():
            self.pheromone[(u, v)] = 1.0

    def _construct_path(self, start, end):
        path = [start]
        current = start
        visited = set([start])
        
        while current != end:
            neighbors = list(self.graph.neighbors(current))
            valid_neighbors = [n for n in neighbors if n not in visited]
            
            if not valid_neighbors:
                return None  # No valid path
            
            # Calculate probabilities
            probabilities = []
            total = 0
            for neighbor in valid_neighbors:
                pheromone = self.pheromone[(current, neighbor)] ** self.alpha
                weight = self.graph[current][neighbor]['weight']
                heuristic = (1/weight) ** self.beta
                total += pheromone * heuristic
                probabilities.append((neighbor, pheromone * heuristic))
            
            # Select next node
            if total == 0:
                return None
            
            r = random.uniform(0, total)
            cumulative = 0
            for neighbor, prob in probabilities:
                cumulative += prob
                if r <= cumulative:
                    current = neighbor
                    path.append(current)
                    visited.add(current)
                    break
        
        return path if current == end else None

    def optimize(self, start, end):
        best_path = None
        best_length = float('inf')
        
        for _ in range(self.n_iterations):
            paths = []
            path_lengths = []
            
            # Generate ant paths
            for _ in range(self.n_ants):
                path = self._construct_path(start, end)
                if path:
                    length = sum(self.graph[path[i]][path[i+1]]['weight'] 
                               for i in range(len(path)-1))
                    paths.append((path, length))
                    if length < best_length:
                        best_path = path
                        best_length = length
            
            # Update pheromones
            self._update_pheromones(paths)
            
        return best_path

    def _update_pheromones(self, paths):
        # Evaporate pheromones
        for edge in self.pheromone:
            self.pheromone[edge] *= (1 - self.decay)
        
        # Deposit new pheromones
        for path, length in paths:
            if length > 0:
                delta = 1 / length
                for i in range(len(path)-1):
                    edge = (path[i], path[i+1])
                    self.pheromone[edge] += delta
