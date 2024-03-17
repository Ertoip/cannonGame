from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Rotate, Line, Ellipse
from kivy.uix.button import Button
from kivy.core.window import Window, Keyboard
from kivy.config import Config
import math
import random
import time
import threading

class Ground(Widget):
    reflective = BooleanProperty(False)
    bulletproof = BooleanProperty(False)
    elastic = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            Color(0.6, 0.3, 0)     

class Obstacle(Widget):
    gravity = BooleanProperty(False)
    wormhole = BooleanProperty(False)
    radius = NumericProperty(1)
    effectRadius = NumericProperty(10)
    attraction = NumericProperty(0.2)
    repulsive = BooleanProperty(False)
    wormhole_exit = ListProperty([])
    
    def __init__(self, cell_size, gravity = False, wormhole=False, wormhole_exit=[0,0], **kwargs):
        super().__init__(**kwargs)
        self.cell_size = cell_size
        self.gravity = gravity
        self.wormhole = wormhole
        self.wormhole_exit = wormhole_exit
        
        with self.canvas:
            # Draw the obstacle (circle)
            Color(0, 0, 0)
            self.obstacle = Ellipse(pos=self.pos, size=(self.radius*2*self.cell_size, self.radius*2*self.cell_size))

            if self.gravity:
                obstacle_center = (self.pos[0] + self.obstacle.size[0] / 2,
                self.pos[1] + self.obstacle.size[1] / 2)

                # Draw the effect radius ring
                Color(0, 0, 0,)  # Red color with 50% opacity
                self.effect_radius_ring = Line(circle=(obstacle_center[0], obstacle_center[1], self.effectRadius * self.cell_size), width=1.1)            
            
            if wormhole:
                Color(1, 1, 1)
                
                self.wormhole = Ellipse(pos=self.wormhole_exit, size=(self.radius*2*self.cell_size, self.radius*2*self.cell_size))
                        
        self.bind(pos=self.update_obstacle_position)

    def update_obstacle_position(self, *args):
        # Update the position of the obstacle and effect radius ring when the widget's position changes
        self.obstacle.pos = self.pos
        self.effect_radius_ring.circle = (self.center_x, self.center_y, self.effectRadius)
        
    def apply_gravity(self, bullet, dt):
        # Calculate distance between bullet and obstacle
        dist_x = self.center_x - bullet.center_x
        dist_y = self.center_y - bullet.center_y
        distance = max(1, math.sqrt(dist_x ** 2 + dist_y ** 2))  # Avoid division by zero
        
        # Calculate unit vector pointing towards the obstacle's center
        unit_vector_x = dist_x / distance
        unit_vector_y = dist_y / distance
        
        # Apply attraction force
        if distance < self.effectRadius * self.cell_size:
            force_direction = -1 if self.repulsive else 1
            force = (self.attraction * self.cell_size)
            # Update bullet position towards the center of the obstacle
            bullet.x += force * unit_vector_x * bullet.mass * force_direction 
            bullet.y += force * unit_vector_y * bullet.mass * force_direction
            
    def wormholeCheck(self, bullet):
        dist_x = self.center_x - bullet.center_x
        dist_y = self.center_y - bullet.center_y
        distance = math.sqrt(dist_x ** 2 + dist_y ** 2)  # Avoid division by zero
        
        if distance < self.radius*2 * self.cell_size/2:
            bullet.x = self.wormhole_exit[0]+self.wormhole.size[0]/2
            bullet.y = self.wormhole_exit[1]+self.wormhole.size[0]/2
#-------------------------------------------------------------------------enemy target-------------------------------------------------------------------------#
class Enemy(Widget):
    cannon_angle = NumericProperty(math.pi)
    speed = NumericProperty(20)
    mass = NumericProperty(0.5)
    health = NumericProperty(5)
    last_shot_time = NumericProperty(0)

    bullet_preds = ListProperty([])
    num_preds = 3
    dot_size = 1
    
    #ai_settings
    direct_hitter = BooleanProperty(True)
    imprecision = NumericProperty(0.01)
    weapon_range = NumericProperty(50)
    moving = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Draw the tank body (rectangle)
            Color(0.1, 0.1, 0.1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
            # Draw the cannon
            self.cannon_length = self.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.size[0] * 0.03  # Adjust the width of the cannon as needed
            self.cannon = Line(points=(self.center_x, self.center_y, 
                                        self.center_x + self.cannon_length, self.center_y + self.cannon_width), width=self.cannon_width)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Update the cannon length and width
        self.cannon_length = self.size[1] * 1.5  # Adjust the length of the cannon as needed
        self.cannon_width = self.size[0] * 1.5  # Adjust the width of the cannon as needed
        
        # Update the cannon points
        self.cannon.points = (self.center_x, self.center_y, 
                            self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                            self.center_y + self.cannon_length * math.sin(self.cannon_angle))
    def shoot(self, game):
        weapon = game.enemy_weapon

        firerate = weapon.get("firerate")
        
        if time.time() - self.last_shot_time >= 1 / firerate:
            bullet = Bullet(radius=weapon.get("radius", None)*game.cell_size)
            
            bullet.angle = self.cannon_angle
            bullet.pos = [self.center_x + (self.cannon_length +5) * math.cos(self.cannon_angle)-bullet.radius, self.center_y + (self.cannon_length +5) * math.sin(self.cannon_angle)-bullet.radius]
            bullet.color = (0.5, 0.5, 0.5, 1)
            
            bullet.init_x = bullet.x
            bullet.init_y = bullet.y
            
            bullet.effect_diameter = weapon.get("effect_diameter", None)
            bullet.mass = weapon.get("mass", None)*game.cell_size
            bullet.speed = weapon.get("speed", None)*game.cell_size
            bullet.drill = weapon.get("drill", None)
            bullet.repeat_explosions = weapon.get("repeat_explosions", None)
            bullet.laser = weapon.get("laser", None)
            
            game.bullet_group.add(bullet)
            game.add_widget(bullet)
            
            self.last_shot_time = time.time()

    def enemy_ai(self, game, start_x, start_y, target_x, target_y, speed, g, dt):
        x = target_x - start_x
        y = target_y - start_y

        distance_to_target = math.sqrt(x ** 2 + y ** 2)  # Calculate distance to target
        
        if distance_to_target <= self.weapon_range * game.cell_size:
            discriminant = speed ** 4 - g * (g * x ** 2 + 2 * y * speed ** 2)

            if discriminant < 0:
                self.cannon_angle = math.pi
            else:
                numerator = speed ** 2 - math.sqrt(discriminant) if self.direct_hitter else speed ** 2 + math.sqrt(discriminant)
                denominator = g * x

                if denominator == 0:
                    self.cannon_angle = math.pi / 2 if numerator > 0 else -math.pi / 2
                    random_adjustment = random.uniform(-self.imprecision, self.imprecision)
                    self.cannon_angle += random_adjustment
                else:
                    self.cannon_angle = math.atan2(numerator, denominator)
                    random_adjustment = random.uniform(-self.imprecision, self.imprecision)
                    self.cannon_angle += random_adjustment

                self.shoot(game)
        
        elif self.moving:
            if x < 0:
                return 1,0
            else:
                return 0,1

        # Update cannon position
        self.cannon.points = (self.center_x, self.center_y,
                              self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                              self.center_y + self.cannon_length * math.sin(self.cannon_angle))
        
        return 0,0
            
    def move_right(self, cell_size, dt):
        self.x += self.speed*cell_size*dt
    
    def move_left(self, cell_size, dt):
        self.x -= self.speed*cell_size*dt
    
    def fall(self, cell_size):
        self.y -= self.mass*cell_size
        
    def hit(self, damage = 1):
        self.health -= damage
        if self.health < 1:
            App.get_running_app().stop() 
            
#-------------------------------------------------------------------------tank-------------------------------------------------------------------------#

class Tank(Widget):
    cannon_angle = NumericProperty(0)
    speed = NumericProperty(20)
    mass = NumericProperty(0.5)
    last_shot_time = NumericProperty(0)
    
    bullet_preds = ListProperty([])
    num_preds = 3
    dot_size = 1
    dot_step_size = 5
    
    def __init__(self, health = 50,**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Draw the tank body (rectangle)
            Color(0.9, 0.9, 0.9)
            self.tank_image_source = "Tank 1.png"
            self.rect = Rectangle(source=self.tank_image_source, pos=self.pos, size=self.size)
            self.health = health
            
            # Draw the cannon
            self.cannon_length = self.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.size[0] * 0.02  # Adjust the width of the cannon as needed
            self.cannon = Line(points=(self.center_x, self.center_y, 
                                    self.center_x + self.cannon_length, self.center_y + self.cannon_width), width=self.cannon_width)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Update the cannon length and width
        self.cannon_length = self.size[1] * 1  # Adjust the length of the cannon as needed
        self.cannon_width = self.size[0] * 1.5  # Adjust the width of the cannon as needed
        
        # Update the cannon points
        self.cannon.points = (self.center_x, self.center_y, 
                            self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                            self.center_y + self.cannon_length * math.sin(self.cannon_angle))
        
    def set_cannon_angle(self, mouse_pos):
        """Set the angle of the cannon based on the mouse position."""
        dx = mouse_pos[0] - self.center_x
        dy = mouse_pos[1] - self.center_y
        self.cannon_angle = math.atan2(dy, dx)  
        
        
        self.cannon.points = (self.center_x, self.center_y, 
                            self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                            self.center_y + self.cannon_length * math.sin(self.cannon_angle))
        
    def shoot(self, game):
        weapon = game.weapons[game.current_weapon]

        firerate = weapon.get("firerate")
        
        if time.time() - self.last_shot_time >= 1 / firerate:
            bullet = Bullet(radius=weapon.get("radius", None)*game.cell_size)
            
            bullet.angle = self.cannon_angle
            bullet.pos = [self.center_x + (self.cannon_length +5) * math.cos(self.cannon_angle)-bullet.radius, self.center_y + (self.cannon_length +5) * math.sin(self.cannon_angle)-bullet.radius]
            bullet.color = (0.5, 0.5, 0.5, 1)
            
            bullet.init_x = bullet.x
            bullet.init_y = bullet.y
            
            bullet.effect_diameter = weapon.get("effect_diameter", None)
            bullet.mass = weapon.get("mass", None)*game.cell_size
            bullet.speed = weapon.get("speed", None)*game.cell_size
            bullet.drill = weapon.get("drill", None)
            bullet.repeat_explosions = weapon.get("repeat_explosions", None)
            bullet.laser = weapon.get("laser", None)
            
            game.bullet_group.add(bullet)
            game.add_widget(bullet)
            
            self.last_shot_time = time.time()
    
    def move_right(self, cell_size, dt):
        self.x += self.speed*cell_size*dt
    
    def move_left(self, cell_size, dt):
        self.x -= self.speed*cell_size*dt
    
    def fall(self, cell_size):
        self.y -= self.mass*cell_size
        
    def draw_preds(self, game):
        if len(self.bullet_preds) > 1:
            for pred in self.bullet_preds:
                self.canvas.remove(pred)
            self.bullet_preds.clear()
        for i in range(self.num_preds):
            i = i+1
            weapon = game.weapons[game.current_weapon]
            mass = weapon.get("mass", None)*game.cell_size
            speed = weapon.get("speed", None)*game.cell_size
            radius=weapon.get("radius", None)*game.cell_size
            cannon_pos = [self.center_x + self.cannon_length * math.cos(self.cannon_angle)-self.dot_size/2, self.center_y + self.cannon_length * math.sin(self.cannon_angle)-self.dot_size/2]
            
            with self.canvas:
                                
                Color(1,1,1, 1/i)
                
                dot_x = cannon_pos[0] + speed * math.cos(self.cannon_angle) * i * self.dot_step_size
                dot_y = cannon_pos[1] + i*self.dot_step_size*(speed * math.sin(self.cannon_angle)) - 0.5 * mass * i * self.dot_step_size * i * self.dot_step_size

                
                dot = Ellipse(pos=(dot_x-radius, dot_y-radius), size=(self.dot_size*game.cell_size, self.dot_size*game.cell_size))
                self.bullet_preds.append(dot)
    
    def hit(self, damage = 1):
        self.health -= damage
        if self.health < 1:
            App.get_running_app().stop() 
            
#------------------------------------------------------------------------- bullets -------------------------------------------------------------------------#

class Bullet(Widget):
    mass = NumericProperty(1)
    effect_diameter = NumericProperty(300)
    speed = NumericProperty(2)
    flighttime = NumericProperty(0)
    angle = NumericProperty(0)
    radius = NumericProperty(5)
    drill = NumericProperty(0)
    
    init_x = NumericProperty(0)
    init_y = NumericProperty(0)
    
    repeat_explosions = BooleanProperty(False)
    laser = BooleanProperty(False)
    rays = ListProperty([])
    prev_coordinates = ListProperty([0,0])
    
    def __init__(self, radius=1, **kwargs):
        super().__init__(**kwargs)
        
        self.radius = radius
        self.size=(self.radius*2, self.radius*2)
        with self.canvas:
            # Draw the bullet (circle)
            Color(0.4, 0.4, 0.4)
            self.bullet = Ellipse(pos=self.pos)

        self.bind(pos=self.update_bullet_position)

    def update_bullet_position(self, *args):
        # Update the position of the bullet when the widget's position changes
        self.bullet.pos = self.pos
        self.bullet.size = self.size
        
    def trajectory(self):
        # Convert speed to units per second
        self.prev_coordinates = [self.x,self.y]
        self.x = self.init_x + self.speed * math.cos(self.angle) * self.flighttime
        self.y = self.init_y + self.speed * math.sin(self.angle) * self.flighttime - 0.5 * self.mass * self.flighttime * self.flighttime
        self.flighttime += 1
            
    def explode(self, game):
        explosion = Explosion(effect_diameter=self.effect_diameter * game.cell_size, pos=self.pos)
        game.add_widget(explosion)
        game.explosion_group.add(explosion)
        
    def recalculate_angle(self, normal_vector):
        # Calculate the angle of incidence
        angle_incidence = math.atan2(self.speed * math.sin(self.angle), self.speed * math.cos(self.angle))

        # Calculate the angle between the normal vector and the horizontal axis
        angle_normal = math.atan2(normal_vector[1], normal_vector[0])

        # Calculate the angle of reflection (angle of incidence - angle of normal)
        angle_reflection = 2 * angle_normal - angle_incidence

        # Normalize the angle to the range [0, 2*pi) or [0, 360 degrees)
        self.angle = angle_reflection % (2 * math.pi)

        # Convert the angle back to the range [-pi, pi) or [-180, 180 degrees)
        if self.angle > math.pi:
            self.angle -= 2 * math.pi

#------------------------------------------------------------------------- explosions -------------------------------------------------------------------------#

class Explosion(Widget):
    effect_diameter = NumericProperty(10)#this is used to determine the meximum size of the explosion
    radius = NumericProperty(0)#this is the actual radius of the explosion
    radius_steps = NumericProperty(0)
    explosion_speed = NumericProperty(7)
    
    def __init__(self, effect_diameter, **kwargs):
        super().__init__(**kwargs)
        self.effect_diameter = effect_diameter 
        self.radius_steps = self.effect_diameter/self.explosion_speed
        with self.canvas:
            Color(1, 0, 0)
            self.fire = Ellipse(pos=(self.x - self.radius, self.y - self.radius), size=(self.radius/2, self.radius/2))

    def increase_explosion_radius(self):
        self.radius += self.radius_steps
        self.fire.pos = (self.x - self.radius, self.y - self.radius)
        self.fire.size = (self.radius*2, self.radius*2)
        self.size = (self.radius*2, self.radius*2)
        
#-------------------------------------------------------------------------class game-------------------------------------------------------------------------#
class CannonGame(Widget):
    tank = ObjectProperty(None)
    enemy = ObjectProperty(None)
    fps = NumericProperty(120)
    keys_up = ListProperty([])
    fullscreen = BooleanProperty(True)
    
    chunk_size = NumericProperty(2)
    chunk_number = NumericProperty(100)
    chunks = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self.grid_size_x = self.chunk_number*self.chunk_size-1  # Define the size of the grid
        self.grid_size_y = 50 # Define the size of the grid
        self.cell_size = self.width / self.grid_size_x
        self.prev_cell_size = self.cell_size

        for i in range(self.chunk_number):
            
            self.chunks.append({"ground":[], "explosions":[], "bullets":[], "obstacles":[], "x_limit":(((i+1)*self.chunk_size-self.chunk_size)*self.cell_size, ((i+1)*self.chunk_size)*self.cell_size)})
        
        # Define the parameters for scaling
        amplitude = 5  # Half of the peak-to-peak height (from -1 to 1)
        frequency = 2
        offset_y = 20
        offset_x = 10
        # Calculate the heights using a sine function
        self.heights = []
        for x in range(self.grid_size_x):
            # Scale the sine function to fit within [0, 10]
            y = math.sin(((x+offset_x) * (2 * math.pi / self.grid_size_x))*frequency) * amplitude + offset_y

            self.heights.append(round(y))  # Round the result to the nearest integer
        
        self.ground_tiles = set()
        self.bullet_group = set()
        self.explosion_group = set()
        self.obstacle_group = set()
        self.enemy_group = set()
        
        self.draw_background() # Draw the background
        self.terrain_gen()  # Draw the grid
        self.create_tank()  # Create the tank
        self.spawn_enemy()
        
        if self.fullscreen: 
            Window.fullscreen = 'auto'
        else:
            Config.set('graphics', 'width', '400')
            Config.set('graphics', 'height', '300')
            
            # Prevent resizing
            Config.set('graphics', 'resizable', '0')

        self.keyboard = Window.request_keyboard(self.keyboard_closed, self)
        self.keyboard.bind(on_key_down=self.on_key_down)
        self.keyboard.bind(on_key_up=self.on_key_up)
        self.keys_pressed = set()
        
        Window.bind(mouse_pos=self.on_mouse_move)
        self.mouse = Vector(Window.mouse_pos)  # Vector to store mouse position        
        self.bind(on_touch_down = self.onMousePressed)

#------------------------------------------------------------------------- Weapons -------------------------------------------------------------------------#

        self.weapons = [{
            "name": "Bullet",
            "mass": 0.05,
            "effect_diameter": 15,
            "speed": 2,
            "firerate": 2,
            "radius": 0.5,
            "drill": 0,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Bombshell",
            "mass": 0.05,
            "effect_diameter": 10,
            "speed": 2,
            "firerate": 3,
            "radius": 0.3,
            "drill": 40,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Laser",
            "mass": 0.0,
            "effect_diameter": 1,
            "speed": 1,
            "firerate": 3,
            "radius": 0.5,
            "drill": 100,
            "repeat_explosions": False,
            "laser": True,
        }]
        

        self.current_weapon = 0
        
        self.enemy_weapon = {
            "name": "sniper",
            "mass": 0.01,
            "effect_diameter": 2,
            "speed": 2,
            "firerate": 20,
            "radius": 0.3,
            "drill": 0,
            "repeat_explosions": False,
            "laser": False,
        }

#-------------------------------------------------------------------------map generation-------------------------------------------------------------------------#
    def draw_background(self):
        # Draw the background
        with self.canvas:
            Color(0.529, 0.808, 0.922, 1)  # RGBA values (blue)
            Rectangle(pos=(0, 0),size=(Window.width, Window.height))
            
    def terrain_gen(self):
        # Generate terrain
        
        x_offset = (self.width - self.grid_size_x * self.cell_size) / 2
        y_offset = 0

        x = 0
        chunk = 0
        
        # Create a group for ground objects
        while x < len(self.heights):
            if (x +1)%self.chunk_size == 0:
                
                chunk += 1
                c = 0                

            for y in range(self.heights[x]):
                ground = Ground()
                if y == self.heights[x]-1:
                    ground_color = Color(0.1, 1, 0.1) # set color
                elif y == self.heights[x]-2:
                    ground_color = Color(0.1, 0.9, 0.1) # set color
                elif y == self.heights[x]-3:
                    ground_color = Color(0, 0.8, 0) # set color
                    
                elif y < 1:
                    ground_color = Color(0.3, 0.3, 0.3)  
                    ground.bulletproof = True
                else:
                    ground_color = Color(0.6, 0.3, 0)
                    
                ground.canvas.add(ground_color)
                ground_pos_y = (y * self.cell_size) + y_offset
                ground_rectangle = Rectangle(pos=((x * self.cell_size)+x_offset, ground_pos_y), size=(self.cell_size, self.cell_size))
                ground.canvas.add(ground_rectangle)
                ground.size_hint = (None, None)
                ground.size = (self.cell_size, self.cell_size)
                ground.pos=((x * self.cell_size)+x_offset, ground_pos_y)
                
                self.chunks[chunk]["ground"].append(ground)
                self.ground_tiles.add(ground)  # Add ground to the group
                self.add_widget(ground)

            x += 1

        
        #obstacle = Obstacle(cell_size=self.cell_size, gravity=True, wormhole=True, wormhole_exit=(((self.grid_size_x/2)-10)*self.cell_size, ((self.grid_size_y / 2)+10)*self.cell_size), pos=(((self.grid_size_x/2)+10)*self.cell_size, ((self.grid_size_y / 2)+10)*self.cell_size))  # Position the obstacle in the middle of the screen
        #self.obstacle_group.add(obstacle) # Add obstacle to the group
        #self.add_widget(obstacle)
        
        
    def create_tank(self, new_pos = None):

        self.tank = Tank()
        self.tank.size_hint = (None, None)
        
        if new_pos == None:
            self.tank.pos = (self.cell_size, self.heights[0]*(self.cell_size)+2)
        else:
            self.tank.pos = (new_pos[0], new_pos[1])  # Center tank horizontally

            
        self.tank.size = (self.cell_size*2, self.cell_size*2)
        
        self.add_widget(self.tank)  # Add tank widget to the game
    
    def spawn_enemy(self, new_pos = None):
        
        self.enemy = Enemy()
        self.enemy.size_hint = (None, None)
        self.enemy.size = (self.cell_size*2, self.cell_size*2)

        if new_pos == None:
            self.enemy.pos = (self.width-self.cell_size*10-self.enemy.size[0], self.heights[-5]*self.cell_size+2)
        else:
            self.enemy.pos = (new_pos[0], new_pos[1])  # Center tank horizontally        
                
        self.add_widget(self.enemy)  # Add tank widget to the game

#-------------------------------------------------------------------------system functions-------------------------------------------------------------------------#
    def on_size(self, *args):
        
        prev_cell_size = self.prev_cell_size
        self.cell_size = self.width / self.grid_size_x
        self.prev_cell_size = self.cell_size
                        
        # Redraw grid and background when the size of the widget changes
        self.remove_widget(self.tank)
        self.canvas.clear()
        self.ground_tiles.clear()
        self.bullet_group.clear()
        self.explosion_group.clear()
        self.obstacle_group.clear()
        
        
        self.chunks.clear()
        for i in range(self.chunk_number):    
            self.chunks.append({"ground":[], "explosions":[], "bullets":[], "obstacles":[], "x_limit":(((i+1)*self.chunk_size-self.chunk_size)*self.cell_size, ((i+1)*self.chunk_size)*self.cell_size)})

        self.draw_background()  # Redraw the background
        self.terrain_gen()  # Redraw the grid
        
        tank_x = self.tank.x
        tank_y = self.tank.y
        
        new_x = (tank_x/prev_cell_size)*self.cell_size
        new_y = (tank_y/prev_cell_size)*self.cell_size
        
        self.create_tank(new_pos=(new_x,new_y))  # Create the tank
        
        enemy_x = self.enemy.x
        enemy_y = self.enemy.y
        
        new_x = (enemy_x/prev_cell_size)*self.cell_size
        new_y = (enemy_y/prev_cell_size)*self.cell_size

        self.spawn_enemy()

    def update(self, dt):
        
        # Calculate movement distance based on normalized speed
        movement_distance = self.tank.speed*self.cell_size*dt # Adjust speed based on screen size
        tank_falling_distance = self.tank.mass*self.cell_size*dt
        
        tank_ground_to_render = []
        enemy_ground_to_render = []
        bullet_ground_to_render = []
        explosions_ground_to_render = []
        
        tank_processed_chunks = set()
        enemy_processed_chunks = set()
        bullet_processed_chunks = set()
        explosions_processed_chunks = set()

        bullets_to_remove = []
        explosions_to_remove = []
        ground_to_remove = []

        for i in range(self.chunk_number):
            if self.chunks[i]["x_limit"][0] <= self.tank.x <= self.chunks[i]["x_limit"][1] or self.chunks[i]["x_limit"][0] <= self.tank.x + self.tank.width <= self.chunks[i]["x_limit"][1]:
                # Check if the current chunk has already been processed
                if i not in tank_processed_chunks:
                    tank_ground_to_render.extend(self.chunks[i]["ground"])
                    tank_processed_chunks.add(i)

                if i - 1 > -1 and (i - 1) not in tank_processed_chunks:
                    tank_ground_to_render.extend(self.chunks[i - 1]["ground"])
                    tank_processed_chunks.add(i - 1)

                if i + 1 < self.chunk_number and (i + 1) not in tank_processed_chunks:
                    tank_ground_to_render.extend(self.chunks[i + 1]["ground"])
                    tank_processed_chunks.add(i + 1)
            
            if self.chunks[i]["x_limit"][0] <= self.enemy.x <= self.chunks[i]["x_limit"][1] or self.chunks[i]["x_limit"][0] <= self.enemy.x + self.enemy.width <= self.chunks[i]["x_limit"][1]:
                # Check if the current chunk has already been processed
                if i not in enemy_processed_chunks:
                    enemy_ground_to_render.extend(self.chunks[i]["ground"])
                    enemy_processed_chunks.add(i)

                if i - 1 > -1 and (i - 1) not in enemy_processed_chunks:
                    enemy_ground_to_render.extend(self.chunks[i - 1]["ground"])
                    enemy_processed_chunks.add(i - 1)

                if i + 1 < self.chunk_number and (i + 1) not in enemy_processed_chunks:
                    enemy_ground_to_render.extend(self.chunks[i + 1]["ground"])
                    enemy_processed_chunks.add(i + 1)

            for bullet in self.bullet_group:
                if self.chunks[i]["x_limit"][0] <= bullet.x <= self.chunks[i]["x_limit"][1] or self.chunks[i]["x_limit"][0] <= bullet.x + bullet.width <= self.chunks[i]["x_limit"][1]:
                    # Check if the current chunk has already been processed
                    if i not in bullet_processed_chunks:
                        bullet_ground_to_render.extend(self.chunks[i]["ground"])
                        bullet_processed_chunks.add(i)

                    if i - 1 > -1 and (i - 1) not in bullet_processed_chunks:
                        bullet_ground_to_render.extend(self.chunks[i - 1]["ground"])
                        bullet_processed_chunks.add(i - 1)

                    if i + 1 < self.chunk_number and (i + 1) not in bullet_processed_chunks:
                        bullet_ground_to_render.extend(self.chunks[i + 1]["ground"])
                        bullet_processed_chunks.add(i + 1)
                        
            for explosion in self.explosion_group:

                if (self.chunks[i]["x_limit"][0] <= explosion.x-explosion.radius <= self.chunks[i]["x_limit"][1] 
                    or self.chunks[i]["x_limit"][0] <= explosion.x + explosion.radius <= self.chunks[i]["x_limit"][1]
                    or explosion.x - explosion.radius <= self.chunks[i]["x_limit"][0] <= explosion.x + explosion.radius and explosion.x - explosion.radius <= self.chunks[i]["x_limit"][1] <= explosion.x + explosion.radius):
                    # Check if the current chunk has already been processed
                    if i not in explosions_processed_chunks:
                        explosions_ground_to_render.extend(self.chunks[i]["ground"])
                        explosions_processed_chunks.add(i)

                    if i - 1 > -1 and (i - 1) not in explosions_processed_chunks:
                        explosions_ground_to_render.extend(self.chunks[i - 1]["ground"])
                        explosions_processed_chunks.add(i - 1)

                    if i + 1 < self.chunk_number and (i + 1) not in explosions_processed_chunks:
                        explosions_ground_to_render.extend(self.chunks[i + 1]["ground"])
                        explosions_processed_chunks.add(i + 1)
                        
                                
        for explosion in self.explosion_group:
            if explosion.radius*2 < explosion.effect_diameter:
                    explosion.increase_explosion_radius()
            else:
                explosions_to_remove.append(explosion)
                
                touching, rect2 = self.check_collision_circle(circle=explosion, rect=self.tank) 
                if touching:
                    self.tank.hit()
                
                touching, rect2 = self.check_collision_circle(circle=explosion, rect=self.enemy) 
                if touching:
                    self.enemy.hit()
                    
                for ground in explosions_ground_to_render:
                    
                        if not ground.bulletproof:
                            touching, rect2 = self.check_collision_circle(circle=explosion, rect=ground) 
                            if touching:
                                ground_to_remove.append(ground)

                    
        self.tank.draw_preds(self)
                        
        falling = True #wheater the tank can fall or move
        right = False
        left = False     

        range_x = (self.tank.x - self.cell_size * 2, self.tank.x + self.cell_size * 2)#we use theese to improve performance by checking collision of only neraby objects
        range_y = (self.tank.y - self.cell_size * 2, self.tank.y + self.cell_size * 2)
            
        collision_not_detected = True
        
        #tank collisions
        for ground in tank_ground_to_render:

            if range_x[0] <= ground.x <= range_x[1] and range_y[0] <= ground.y <= range_y[1]: 

                if falling:    
                    touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, gravity=3)
                    if touching:
                        falling = False
                        if self.tank.y > rect2[3]:
                            self.tank.y = rect2[3]
                
                if collision_not_detected:

                    if "right" in self.keys_pressed or "d" in self.keys_pressed:
                        touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = movement_distance)

                        if self.tank.x + self.tank.width + movement_distance < self.width and not touching:
                            right = True
                            
                        elif (touching 
                            and not self.is_widget_at_coordinate(group=tank_ground_to_render, x=rect2[0]+3,y=self.tank.y+self.cell_size+3 ) 
                            and not self.is_widget_at_coordinate(group=tank_ground_to_render, x=rect2[0]+3,y=self.tank.y+self.cell_size*2+3 )):#this allows to climb to the right
                            self.tank.y = rect2[1]+self.cell_size+1
                            
                        elif touching:    
                            right = False
                            self.tank.x = rect2[0]-self.tank.width
                            collision_not_detected = False

                    if "left" in self.keys_pressed or "a" in self.keys_pressed:                     
                        touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = -movement_distance)
                        
                        if self.tank.x - movement_distance > 0 and not touching:
                            left = True
                        
                        elif (touching 
                            and not self.is_widget_at_coordinate(group=tank_ground_to_render, x=rect2[0]+3,y=self.tank.y+self.cell_size+3 ) 
                            and not self.is_widget_at_coordinate(group=tank_ground_to_render, x=rect2[0]+3,y=self.tank.y+self.cell_size*2+3 )):#this
                            self.tank.y = rect2[1]+self.cell_size+1
                        
                        elif touching:    
                            left = False
                            self.tank.x = rect2[2]-1 
                            collision_not_detected = False
                
            elif collision_not_detected:
                if ("right" in self.keys_pressed or "d" in self.keys_pressed) and self.tank.x + self.tank.width + movement_distance < self.width:
                    right = True
                
                elif ("left" in self.keys_pressed or "a" in self.keys_pressed) and self.tank.x - movement_distance > 0:
                    left = True
                    
        enemy_falling = True
        enemy_collision_not_detected = True
        
        enemy_left, enemy_right =self.enemy.enemy_ai(game=self, 
                        start_x=self.enemy.cannon.points[2], 
                        start_y=self.enemy.cannon.points[3], 
                        target_x=self.tank.center_x, 
                        target_y=self.tank.center_y, 
                        speed=self.enemy_weapon["speed"]*self.cell_size, 
                        g=self.enemy_weapon["mass"]*self.cell_size,
                        dt=dt)#move the player cannon

        enemy_range_x = (self.enemy.x - self.cell_size * 2, self.enemy.x + self.cell_size * 2)#we use theese to improve performance by checking collision of only neraby objects
        enemy_range_y = (self.enemy.y - self.cell_size * 2, self.enemy.y + self.cell_size * 2)
        
        enemy_movement_distance = self.enemy.speed*self.cell_size*dt # Adjust speed based on screen size
        enemy_falling_distance = self.enemy.mass*self.cell_size*dt

        enemy_touching = False

        for ground in enemy_ground_to_render:    
            if enemy_range_x[0] <= ground.x <= enemy_range_x[1] and enemy_range_y[0] <= ground.y <= enemy_range_y[1]: 
                if enemy_falling:    
                    enemy_touching, rect2 = self.check_collision(rect1=self.enemy, rect2=ground, gravity=3)
                    if enemy_touching:
                        enemy_falling = False
                        if self.enemy.y > rect2[3]:
                            self.enemy.y = rect2[3]
                
                if enemy_collision_not_detected:               
                    if enemy_right:
                        enemy_touching, rect2 = self.check_collision(rect1=self.enemy, rect2=ground, speed = movement_distance)
        
                        if (enemy_touching 
                            and not self.is_widget_at_coordinate(group=enemy_ground_to_render, x=rect2[0]+3,y=self.enemy.y+self.cell_size+3 ) 
                            and not self.is_widget_at_coordinate(group=enemy_ground_to_render, x=rect2[0]+3,y=self.enemy.y+self.cell_size*2+3 )):#this allows to climb to the enemy_right
                            self.enemy.y = rect2[1]+self.cell_size+1

                        elif enemy_touching:    
                            enemy_right = False
                            self.enemy.x = rect2[0]-self.enemy.width
                            enemy_collision_not_detected = False

                    if enemy_left:                     
                        enemy_touching, rect2 = self.check_collision(rect1=self.enemy, rect2=ground, speed = -movement_distance)
                                                
                        if (enemy_touching 
                            and not self.is_widget_at_coordinate(group=enemy_ground_to_render, x=rect2[0]+3,y=self.enemy.y+self.cell_size+3 ) 
                            and not self.is_widget_at_coordinate(group=enemy_ground_to_render, x=rect2[0]+3,y=self.enemy.y+self.cell_size*2+3 )):#this
                            self.enemy.y = rect2[1]+self.cell_size+1
                        
                    
                        elif enemy_touching:    
                            enemy_left = False
                            self.enemy.x = rect2[2]-1 
                            enemy_collision_not_detected = False
                            
            else:
                if self.enemy.x +enemy_movement_distance +self.enemy.width> Window.width:
                            self.enemy.x = Window.width - self.enemy.width
                            enemy_right = False
                            enemy_collision_not_detected = False    
                            
                if self.enemy.x -enemy_movement_distance < 0:
                            self.enemy.x = 0
                            enemy_left = False
                            enemy_collision_not_detected = False        

                            
        if falling:
            self.tank.fall(self.cell_size)
            if self.tank.y < 0:
                self.tank.y = self.cell_size+1
                
        # Move tank horizontally
        if right:
            self.tank.move_right(cell_size=self.cell_size, dt=dt)

        if left:
            self.tank.move_left(cell_size=self.cell_size, dt=dt)

        self.tank.set_cannon_angle(self.mouse)#move the player cannon
            
        if enemy_falling:
            self.enemy.fall(self.cell_size)
            if self.enemy.y < 0:
                self.enemy.y = self.cell_size+1
        
        if enemy_right:
            self.enemy.move_right(cell_size=self.cell_size, dt=dt)

        if enemy_left:
            self.enemy.move_left(cell_size=self.cell_size, dt=dt)
            

        #-------------neutral functions --------------------------------
        #bullet physics
        for bullet in self.bullet_group:
            bullet.trajectory()  # move all the bullets
            
            touching, rect2 = self.check_collision_circle(circle=bullet, rect=self.tank) 
            if touching:
                if bullet.laser:
                    self.tank.hit()
                bullets_to_remove.append(bullet)
            
            touching, rect2 = self.check_collision_circle(circle=bullet, rect=self.enemy) 
            if touching:
                if bullet.laser:
                    self.enemy.hit()
                bullets_to_remove.append(bullet)

            if bullet.laser:

                # Calculate new coordinates after moving the bullet
                new_coordinates = [bullet.x+bullet.radius , bullet.y+bullet.radius]
                prev_coordinates = [bullet.prev_coordinates[0]+bullet.radius, bullet.prev_coordinates[1]+bullet.radius]
                bullet.drill -= 1
                if bullet.drill < 1:
                    bullets_to_remove.append(bullet)
                
                # Draw the laser ray
                with self.canvas:
                    Color(1,0,0)
                    laser_ray = Line(points=prev_coordinates + new_coordinates, width=bullet.radius)
                    bullet.rays.append(laser_ray)
                    if len(bullet.rays) > 5:#length of the ray
                        self.canvas.remove(bullet.rays[0])
                        bullet.rays.pop(0)

                
            if (bullet.y < 0 or bullet.x < 0 or bullet.x > Window.width or (bullet.y > Window.height and bullet.laser)) and bullet not in bullets_to_remove:
                bullets_to_remove.append(bullet)
            
            bullet_range_x = (bullet.x - self.cell_size, bullet.x + self.cell_size)#we use theese to improve performance by checking collision of only neraby objects
            bullet_range_y = (bullet.y - self.cell_size, bullet.y + self.cell_size)

            for ground in bullet_ground_to_render:
                if (bullet_range_x[0] <= ground.x <= bullet_range_x[1]) and (bullet_range_y[0] <= ground.y <= bullet_range_y[1]):
                    touching, g = self.check_collision_bullet(bullet=bullet, rect=ground)
                    if touching and bullet.laser and ground.reflective:
                        
                        
                        top_side = ((g[0], g[3]), (g[2], g[3]))
                        bottom_side = ((g[0], g[1]), (g[2], g[1]))
                        left_side = ((g[0], g[1]), (g[0], g[3]))
                        right_side = ((g[2], g[1]), (g[2], g[3]))
                        
                        nearest = self.nearest_side([bullet.x + bullet.radius, bullet.y+bullet.radius], ground.pos, ground.size[0])
                        
                        if nearest == "top":
                            # Collision with the top side
                            normal_vector = [1, 0]  # Normal vector pointing upwards
                        
                        elif nearest == "bottom":
                            # Collision with the bottom side
                            normal_vector = [1, 0]  # Normal vector pointing downwards
                            
                        elif nearest == "right":
                            # Collision with the right side
                            normal_vector = [0, 1]  # Normal vector pointing to the right
                            
                        elif nearest == "left":
                            # Collision with the left side
                            normal_vector = [0, 1]  # Normal vector pointing to the left   
                        
                        bullet.pos = bullet.prev_coordinates
                        bullet.recalculate_angle(normal_vector)
                        break
                        
                    elif touching and not bullet.laser and ground.elastic:
                        
                        top_side = ((g[0], g[3]), (g[2], g[3]))
                        bottom_side = ((g[0], g[1]), (g[2], g[1]))
                        left_side = ((g[0], g[1]), (g[0], g[3]))
                        right_side = ((g[2], g[1]), (g[2], g[3]))
                        
                        nearest = self.nearest_side([bullet.x + bullet.radius, bullet.y+bullet.radius], ground.pos, ground.size[0])
                        
                        if nearest == "top":
                            # Collision with the top side
                            normal_vector = [1, 0]  # Normal vector pointing upwards
                            
                        elif nearest == "bottom":
                            # Collision with the bottom side
                            normal_vector = [1, 0]  # Normal vector pointing downwards

                        elif nearest == "right":
                            # Collision with the right side
                            normal_vector = [0, 1]  # Normal vector pointing to the right

                        elif nearest == "left":
                            # Collision with the left side
                            normal_vector = [0, 1]  # Normal vector pointing to the left   

                        bullet.pos=bullet.prev_coordinates
                        bullet.flighttime=0
                        bullet.speed=bullet.speed*0.9
            
                        bullet.recalculate_angle(normal_vector)
                        
                        break            
                    elif touching and bullet.drill <= 0:
                        bullets_to_remove.append(bullet)
                        break  # No need to check further collisions for this bullet if it has already collided  
                        
                    elif touching and bullet.drill > 0 and not ground.bulletproof:
                        bullet.drill -= 1

                        if bullet.repeat_explosions:
                            bullet.explode(self)

                        if bullet.laser:
                            ground_to_remove.append(ground)
                        break  # No need to check further collisions for this bullet if it has already collided  
            
        
            for obstacle in self.obstacle_group:
                if obstacle.gravity and not bullet.laser:
                    obstacle.apply_gravity(bullet=bullet)
                if obstacle.wormhole:
                    obstacle.wormholeCheck(bullet)

            
        if "tab" in self.keys_up:
            if self.current_weapon >= len(self.weapons) -1:
                self.current_weapon = 0
            else:
                self.current_weapon += 1
                            

        for bullet in bullets_to_remove:
            if bullet in self.bullet_group:
                
                if bullet.laser:
                    for r in bullet.rays:
                        self.canvas.remove(r)
                else:                
                    bullet.explode(self) # remove bullet
                self.bullet_group.remove(bullet)
                self.remove_widget(bullet)
        
        for explosion in explosions_to_remove:
            self.explosion_group.remove(explosion)
            self.remove_widget(explosion)
            
        for ground in ground_to_remove:
            if ground in self.ground_tiles:
                self.ground_tiles.remove(ground)
                self.remove_widget(ground)
                
            for chunk in self.chunks:
                if ground in chunk["ground"]:
                    chunk["ground"].remove(ground)
                
        self.keys_up = []
        
#-------------------------------------------------------------------------time functions-------------------------------------------------------------------------#    
    def check_seconds_passed(start_time, seconds):
        current_time = time.time()
        elapsed_time = current_time - start_time
        return elapsed_time >= seconds
                
#-------------------------------------------------------------------------collision functions-------------------------------------------------------------------------#    
                
        
    def check_collision(self, rect1, rect2, gravity=0, speed=0):
        # Get the bounding boxes of the widgets
        rect1_x, rect1_y = rect1.x+speed, rect1.y - gravity
        rect1_right, rect1_top = rect1.right+speed, rect1.top - gravity
        
        rect2_x, rect2_y = rect2.x, rect2.y
        rect2_right, rect2_top = rect2.right, rect2.top
        
        # Check for overlap in x-axis
        if (rect1_right > rect2_x and rect1_x < rect2_right):
            # Check for overlap in y-axis
            if (rect1_top > rect2_y and rect1_y < rect2_top):
                return True, [rect2_x, rect2_y, rect2_right, rect2_top]
        return False, []
    

    def check_collision_circle(self, circle, rect, gravity=0, speed=0):
        # Calculate center coordinates of the rectangle
        rect_center_x, rect_center_y = rect.x + rect.width / 2, rect.y + rect.height / 2
        
        # Calculate the distance between the centers of the circle and rectangle
        distance = math.hypot(circle.x - rect_center_x, circle.y - rect_center_y)

        # Check if the distance between the centers is less than or equal to the maximum allowed distance
        # and if all corners of the rectangle are within the circle
        if (distance <= (circle.radius*2+rect.width)/2):
            return True, [rect.x, rect.y, rect.x + rect.width, rect.y + rect.height]
        
        return False, []
    
    #basically the same as check_collision_circle
    def check_collision_bullet(self, bullet, rect):
        # Calculate center coordinates of the rectangle
        rect_center_x = (rect.x + rect.width / 2)
        rect_center_y = (rect.y + rect.height / 2)
        
        bullet_center_x = bullet.x+bullet.radius
        bullet_center_y = bullet.y+bullet.radius
        # Calculate the distance between the centers of the circle and rectangle
        distance = math.hypot(bullet_center_x - rect_center_x, bullet_center_y - rect_center_y)

        # Check if the distance between the centers is less than or equal to the maximum allowed distance
        # and if all corners of the rectangle are within the circle
        if (distance <= (bullet.radius+rect.width)/2):
            return True, [rect.x, rect.y, rect.x + rect.width, rect.y + rect.height]
        
        return False, []

    
    def is_widget_at_coordinate(self, group, x, y):
        """
        Check if there is a widget at the specified coordinate (x, y).
        
        Args:
            widget: The parent widget to search within.
            x: The x-coordinate.        if x1 == x2:  # Vertical line
            return abs(x0 - x1)
        elif y1 == y2:  # Horizontal line
            return abs(y0 - y1)
        else:
            return None  # Not a vertical or horizontal line
            y: The y-coordinate.
            
        Returns:
            True if a widget is found at the coordinate, False otherwise.
        """
        for child in group:
            if isinstance(child, Widget):
                if child.collide_point(x, y):
                    return True
        return False
    
    def nearest_side(self, point, bottom_left, width):
        x, y = point
        bx, by = bottom_left
        distance_top = abs(y - (by + width))
        distance_bottom = abs(y - by)
        distance_left = abs(x - bx)
        distance_right = abs(x - (bx + width))
        
        min_distance = min(distance_top, distance_bottom, distance_left, distance_right)
        
        if min_distance == distance_top:
            return "top"
        elif min_distance == distance_bottom:
            return "bottom"
        elif min_distance == distance_left:
            return "left"
        else:
            return "right"
    
#-------------------------------------------------------------------------keyboard control functions-------------------------------------------------------------------------#    
    def keyboard_closed(self):
        self.keyboard.unbind(on_key_down=self.on_key_down)
        self.keyboard.unbind(on_key_up=self.on_key_up)
        self.keyboard = None

    def on_key_down(self, keyboard, keycode, text, modifiers):
        self.keys_pressed.add(keycode[1])

    def on_key_up(self, keyboard, keycode):
        self.keys_pressed.remove(keycode[1])
        self.keys_up.append(keycode[1])

    def on_mouse_move(self, window, pos):
        self.mouse = Vector(pos)  # Update mouse position vector
        
    def onMousePressed(self, instance, touch):
        if touch.button == 'left':
            self.tank.shoot(self)
        
class CannonApp(App):
    def build(self):
        game = CannonGame()
        Clock.schedule_interval(game.update, 1 / game.fps)
        return game


if __name__ == '__main__':
    CannonApp().run()