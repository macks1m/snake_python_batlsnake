import bottle
import os
import random

INF = 1000000000
DEBUG = True

def debug(message):
    if DEBUG: print(message)

class Point:
    
    def __init__(self, x, y):
        
        self.x = x
        self.y = y 

    def __eq__(self, other):
       
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return (str)(self.x) + ',' + (str)(self.y)

    def __repr__(self):
        return self.__str__()

    def closest(self, l):
       
        closest = l[0]
        for point in l:
            if (self.dist(point) < self.dist(closest)):
                closest = point
        return closest

    def dist(self, other):
        
        return abs(self.x - other.x) + abs(self.y - other.y)

    def get(self, direction):
        
        if (direction == 'left'): 
            return self.left()
        if (direction == 'right'):
            return self.right()
        if (direction == 'up'):
            return self.up()
        if (direction == 'down'):
            return self.down()

    def left(self):
        
        return Point(self.x-1, self.y)

    def right(self):
        
        return Point(self.x+1, self.y)

    def up(self):
        
        return Point(self.x, self.y-1)

    def down(self):
        
        return Point(self.x, self.y+1)

    def surrounding_four(self):
        
        return [self.left(), self.right(), self.up(), self.down()]

    def surrounding_eight(self):
        
        return [self.left(), self.right(), self.up(), self.down(), 
                self.left().up(), self.left().down(), self.right().up(), self.right().down()]

    def direction_of(self, point):
        
        if self.x < point.x: return 'right'
        if self.x > point.x: return 'left'
        if self.y < point.y: return 'down'
        if self.y > point.y: return 'up'
        return 'left' # whatever

def point_from_string(string):
    s = string.split(',')
    return Point(int(s[0]), int(s[1]))

class Snake:
    
    def __init__(self, board, data):
        
        self.board = board
        self.id = data['id']
        self.name = data['name']
        self.health = data['health']
        self.head = Point(data['body'][0]['x'], 
                          data['body'][0]['y'])
        self.tail = Point(data['body'][-1]['x'], 
                          data['body'][-1]['y'])
        self.body = []

        for b in data['body'][1:]:
            self.body.append(Point(b['x'], b['y']))

        self.length = len(self.body)
        self.next_move = ''

    
    def smart_movement(self):
        
        if not self.eat_closest_food():
            debug('smart_movement: No path to food')
            self.smart_walk()
            if not self.next_move:
                self.walk()
        elif not self.is_smart_move(self.head.get(self.next_move)):
            debug('smart_movement: No smart move to food')
            self.smart_walk()
            if not self.next_move:
                self.walk()

    def eat_closest_food(self):
        
        distances = self.board.distances(self.head, self.board.food)
        if distances:
            closest_food = point_from_string(min(distances, key=distances.get))
            if(self.board.snakes_are_around_point(closest_food)):
                return False
            return self.move_towards(closest_food)
        return False

    def random_walk(self):
       
        valid = self.valid_moves()
        if valid:
            self.next_move = random.choice(valid)
            return True
        return False

    def random_smart_walk(self):
        
        smart = self.smart_moves()
        if smart: 
            self.next_move = random.choice(smart)
            return True
        return False

    def walk(self):
        
        valid = self.valid_moves()
        if valid:
            self.next_move = random.choice(valid)
            return True
        return False

    def smart_walk(self):
        
        smart = self.smart_moves()
        if smart: 
            self.next_move = random.choice(smart)
            return True
        return False

    def chase_tail(self):
        
        tail = self.body[-1]
        return self.move_towards(tail)

    def move_towards(self, point):
        
        path = self.board.a_star_path(self.head, point)
        if path:
            direction = self.head.direction_of(path[0])
            self.next_move = direction
            return True
        debug('move_towards: no path found to point ' + str(point))
        return False

    def valid_moves(self):
        
        moves = ['up', 'down', 'left', 'right']
        for move in moves[:]:
            next_pos = self.head.get(move)
            if ((next_pos in self.board.obstacles or 
                    self.board.is_outside(next_pos)) and
                    (next_pos not in self.board.tails or
                    self.board.tail_health.get(str(next_pos)) == 100)):
                moves.remove(move)
        return moves

    def smart_moves(self):
        
        moves = self.valid_moves()
        for move in moves[:]:
            next_pos = self.head.get(move)
            if not self.is_smart_move(next_pos):
                moves.remove(move)
        return moves

    def is_smart_move(self, point):
        
        if self.board.is_threatened_by_enemy(point):
            return False
        if self.board.player.health == 100 and self.food_adj_tail(point):
            return False
        if self.is_not_trapped_with_no_out(point):
            return False
        return True

    def is_not_constricting_self(self, point):
        
        possible_moves = self.valid_moves()

        if len(possible_moves) == 0:
            return

        areas = {}
        for move in possible_moves:
            areas[move] = self.board.count_available_space(self.head.get(move))

        best_area = max(areas.values)
        next_area = self.board.count_available_space(point)

        if(best_area == next_area):
            return False
        return True

    def is_not_trapped_with_no_out(self, point):
        
        possible_moves = self.valid_moves()

        for move in possible_moves:
            p = self.head.get(move)
            if self.board.is_threatened_by_enemy(p):
                possible_moves.remove(move)
            if self.health == 100 and self.food_adj_tail(p):
                possible_moves.remove(move)

        if len(possible_moves) == 0:
            return

        areas = {}
        for move in possible_moves:
            areas[move] = self.board.count_available_space_and_snake_data(self.head.get(move))
        best_area = sorted(areas.items(), key=lambda e: (e[1][1] == 0 and e[1][2] > 0 and e[1][0] > 4, e[1][2] - e[1][1], e[1][0]), reverse=True)[0]
        print(areas)
        next_area = self.board.count_available_space_and_snake_data(point)
        print(next_area, best_area)
        print(best_area[0])

        for move in possible_moves:
            if self.board.player.head.get(move) == point and best_area[1] == next_area:
                return False
        return True

    def food_adj_tail(self, point):
        return (point in self.board.food) and (point in self.board.player.tail.surrounding_four())

class Board:
    

    def __init__(self, data):
        
        self.width = data['board']['width']
        self.height = data['board']['height']
        self.player = Snake(self, data['you']) 
        self.enemies = []
        self.turn = data['turn']
        self.food = []
        self.obstacles = []
        self.heads = []
        self.tails = []
        self.tail_health = {}
        self.snake_length = {}

        for snake_data in data['board']['snakes']:
            snake = Snake(self, snake_data)
            for point in snake_data['body']:
                self.obstacles.append(Point(point['x'], point['y']))
            if snake.id != self.player.id:
                self.enemies.append(snake)
                self.heads.append(snake.head)
                self.snake_length[str(snake.head)] = snake.length
            self.tails.append(snake.tail)
            self.tail_health[str(snake.tail)] = snake.health

        for p in data['board']['food']:
            self.food.append(Point(p['x'], p['y']))

    def is_outside(self, p):
        
        return p.x < 0 or p.y < 0 or p.x >= self.width or p.y >= self.height

    def neighbors_of(self, p):
        
        res = []
        for p in p.surrounding_four():
            if p not in self.obstacles and not self.is_outside(p):
                res.append(p)
        return res

    def snakes_are_around_point(self, p):
        for point in p.surrounding_eight():
            if point in self.heads and self.snake_length[str(point)] >= self.player.length:
                return True
        return False

    def count_available_space(self, p):
        
        visited = []
        return self.rec_flood_fill(p, visited)
    
    def rec_flood_fill(self, p, visited):
        
        if p in visited or p in self.obstacles or self.is_outside(p):
            return 0
        visited.append(p)
        return 1 + (self.rec_flood_fill(p.left(), visited) + 
                    self.rec_flood_fill(p.right(), visited) + 
                    self.rec_flood_fill(p.up(), visited) + 
                    self.rec_flood_fill(p.down(), visited))    

    def count_available_space_and_snake_data(self, p):
        
        visited = []
        heads = []
        tails = []
        space = self.rec_flood_fill_with_snake_data(p, visited, heads, tails)
        return [space, len(heads), len(tails)]

    def rec_flood_fill_with_snake_data(self, p, visited, heads, tails):
        
        if p in visited or p in self.obstacles or self.is_outside(p):
            if p in self.heads and p not in heads and p != self.player.head:
                heads.append(p)
            if p in self.tails and p not in tails:
                tails.append(p)
            return 0
        visited.append(p)
        return 1 + (self.rec_flood_fill_with_snake_data(p.left(), visited, heads, tails) + 
                    self.rec_flood_fill_with_snake_data(p.right(), visited, heads, tails) + 
                    self.rec_flood_fill_with_snake_data(p.up(), visited, heads, tails) + 
                    self.rec_flood_fill_with_snake_data(p.down(), visited, heads, tails))

    def available_space(self, p):
        
        visited = []
        return self.rec_flood_fill2(p, visited)

    def rec_flood_fill2(self, p, visited):
        
        if p in visited or p in self.obstacles or self.is_outside(p):
            return visited
        visited.append(p)
        self.rec_flood_fill(p.left(), visited)
        self.rec_flood_fill(p.right(), visited)
        self.rec_flood_fill(p.up(), visited)
        self.rec_flood_fill(p.down(), visited)
        return visited

    def distances(self, start, points):
        
        distances = {}
        for point in points:
            distance = len(self.a_star_path(start, point))
            if distance > 0:
                distances[str(point)] = distance
        return distances

    def is_threatened_by_enemy(self, point):
        
        for enemy in self.enemies:
            if enemy.length >= self.player.length:
                if point in enemy.head.surrounding_four():
                    return True
        return False

    def a_star_path(self, start, goal):
        
        

        closed_set = []
        open_set = [start]
        came_from = {}
        g_score = {}
        f_score = {}

        str_start = str(start)
        g_score[str_start] = 0
        f_score[str_start] = start.dist(goal)

        while open_set:
            str_current = str(open_set[0])
            for p in open_set[1:]:
                str_p = str(p)
                if str_p not in f_score:
                    f_score[str_p] = INF
                if str_current not in f_score:
                    f_score[str_current] = INF
                if f_score[str_p] < f_score[str_current]:
                    str_current = str_p

            current = point_from_string(str_current)

            if current == goal:
                path = self.reconstruct_path(came_from, current)
                path.reverse()
                return path[1:]

            open_set.remove(current)
            closed_set.append(current)

            for neighbor in self.neighbors_of(current):
                str_neighbor = str(neighbor)
                if neighbor in closed_set:
                    continue

                if neighbor not in open_set:
                    open_set.append(neighbor)

                if str_current not in g_score:
                    g_score[str_current] = INF
                if str_neighbor not in g_score:
                    g_score[str_neighbor] = INF

                tentative_g_score = (g_score[str_current] + 
                                     current.dist(neighbor))
                if tentative_g_score >= g_score[str_neighbor]:
                    continue

                came_from[str_neighbor] = current
                g_score[str_neighbor] = tentative_g_score
                f_score[str_neighbor] = (g_score[str_neighbor] + 
                                          neighbor.dist(goal))
        return []

    def reconstruct_path(self, came_from, current):
        
        total_path = [current]
        while str(current) in came_from.keys():
            current = came_from[str(current)]
            total_path.append(current)
        return total_path

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
    return {
        "color": "#9932CC",
        "headType":"",
        "tailType":""
    }

@bottle.post('/move')
def move():
    data = bottle.request.json
    
    # Set-up our board and snake and define its goals
    board = Board(data)
    snake = board.player
    snake.smart_movement()

    return {
        'move': snake.next_move,
        'taunt': 'drawing...'
    }

@bottle.post('/end')
def end():
    return {}

@bottle.post('/ping')
def ping():
    return {}

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, port=os.getenv('PORT', '8080'))