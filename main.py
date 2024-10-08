from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Rotate, Line, Ellipse
from kivy.uix.button import Button
from kivy.core.window import Window, Keyboard
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
import math
import random
import time
import threading
import json
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
import os

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
    radius = NumericProperty(3)
    effectRadius = NumericProperty(10)
    attraction = NumericProperty(3)
    repulsive = BooleanProperty(False)
    wormhole_exit = ListProperty([])

    def __init__(self, cell_size, gravity=False, wormhole=False, wormhole_exit=[0, 0], color=(0, 0, 0), repulsive=False, effectRadius=0, **kwargs):
        super().__init__(**kwargs)
        self.cell_size = cell_size
        self.gravity = gravity
        self.wormhole = wormhole
        self.wormhole_exit = wormhole_exit
        self.repulsive = repulsive
        self.effectRadius = effectRadius

        with self.canvas:
            if self.repulsive:
                circle_color = (1, 1, 1)
            else:
                circle_color = (0, 0, 0)
                
            if wormhole:
                circle_color = color

            # Draw the obstacle (circle)
            Color(*circle_color)
            self.obstacle = Ellipse(pos=(self.center_x - self.radius * self.cell_size, self.center_y - self.radius * self.cell_size), 
                                    size=(self.radius * 2 * self.cell_size, self.radius * 2 * self.cell_size))

            if self.gravity or self.wormhole:
                # Draw the effect radius ring around the obstacle
                Color(1, 1, 1) if self.repulsive else Color(0, 0, 0)  # White for repulsive, black for not repulsive
                self.effect_radius_ring = Line(circle=(self.center_x, self.center_y, self.effectRadius * self.cell_size), width=2)

            if self.wormhole:
                # Draw the wormhole exit
                Color(*circle_color)
                self.wormhole_exit_circle = Ellipse(pos=(self.wormhole_exit[0] - self.radius * self.cell_size, self.wormhole_exit[1] - self.radius * self.cell_size), 
                                                    size=(self.radius * 2 * self.cell_size, self.radius * 2 * self.cell_size))
                if self.gravity:
                    # Draw the effect radius ring around the wormhole exit
                    Color(1, 1, 1) if self.repulsive else Color(0, 0, 0)  # White for repulsive, black for not repulsive
                    self.effect_radius_exit_ring = Line(circle=(self.wormhole_exit[0], self.wormhole_exit[1], self.effectRadius * self.cell_size), width=2)

        self.bind(pos=self.update_obstacle_position, size=self.update_obstacle_position)

    def update_obstacle_position(self, *args):
        # Update the position of the obstacle and effect radius ring when the widget's position changes
        self.obstacle.pos = (self.center_x - self.radius * self.cell_size, self.center_y - self.radius * self.cell_size)
        self.obstacle.size = (self.radius * 2 * self.cell_size, self.radius * 2 * self.cell_size)
        self.effect_radius_ring.circle = (self.center_x, self.center_y, self.effectRadius * self.cell_size)
        
        if self.wormhole:
            self.wormhole_exit_circle.pos = (self.wormhole_exit[0] - self.radius * self.cell_size, self.wormhole_exit[1] - self.radius * self.cell_size)
            self.wormhole_exit_circle.size = (self.radius * 2 * self.cell_size, self.radius * 2 * self.cell_size)
            self.effect_radius_exit_ring.circle = (self.wormhole_exit[0], self.wormhole_exit[1], self.effectRadius * self.cell_size)

    def apply_gravity(self, bullet):
        dist_x = self.center_x - bullet.center_x
        dist_y = self.center_y - bullet.center_y
        distance = max(1, math.sqrt(dist_x ** 2 + dist_y ** 2))

        unit_vector_x = dist_x / distance
        unit_vector_y = dist_y / distance

        if distance < self.effectRadius * self.cell_size:
            force_direction = -1 if self.repulsive else 1
            force = (self.attraction * self.cell_size)
            bullet.x += force * unit_vector_x * bullet.mass * force_direction 
            bullet.y += force * unit_vector_y * bullet.mass * force_direction

        # Apply repulsive force at wormhole exit
        dist_x_exit = self.wormhole_exit[0] - bullet.center_x
        dist_y_exit = self.wormhole_exit[1] - bullet.center_y
        distance_exit = max(1, math.sqrt(dist_x_exit ** 2 + dist_y_exit ** 2))

        unit_vector_x_exit = dist_x_exit / distance_exit
        unit_vector_y_exit = dist_y_exit / distance_exit

        if distance_exit < self.effectRadius * self.cell_size:
            force_direction = -1 if self.repulsive else 1
            force = (self.attraction * self.cell_size)
            bullet.x += force * unit_vector_x_exit * bullet.mass * force_direction
            bullet.y += force * unit_vector_y_exit * bullet.mass * force_direction

    def wormholeCheck(self, bullet):
        # Check distance from entrance
        dist_x_entrance = self.center_x - bullet.center_x
        dist_y_entrance = self.center_y - bullet.center_y
        distance_entrance = math.sqrt(dist_x_entrance ** 2 + dist_y_entrance ** 2)

        if distance_entrance < self.radius * 2 * self.cell_size / 2:
            bullet.x = self.wormhole_exit[0] + self.wormhole_exit_circle.size[0] / 2
            bullet.y = self.wormhole_exit[1] + self.wormhole_exit_circle.size[1] / 2
            return
        
        # Check distance from exit
        dist_x_exit = self.wormhole_exit[0] - bullet.center_x
        dist_y_exit = self.wormhole_exit[1] - bullet.center_y
        distance_exit = math.sqrt(dist_x_exit ** 2 + dist_y_exit ** 2)

        if distance_exit < self.radius * 2 * self.cell_size / 2:
            bullet.x = self.center_x + self.obstacle.size[0] / 2
            bullet.y = self.center_y + self.obstacle.size[1] / 2
                        
#-------------------------------------------------------------------------enemy target-------------------------------------------------------------------------#
class Enemy(Widget):
    cannon_angle = NumericProperty(math.pi)
    speed = NumericProperty(0.2)
    mass = NumericProperty(0.3)
    last_shot_time = NumericProperty(0)

    bullet_preds = ListProperty([])
    num_preds = 3
    dot_size = 1
    
    #ai_settings
    direct_hitter = BooleanProperty(False)
    imprecision = NumericProperty(0.1)
    weapon_range = NumericProperty(50)
    moving = BooleanProperty(True)
    
    reloading = BooleanProperty(False)
    reload_bar_lenght = NumericProperty(0)

    def __init__(self, ammo, max_ammo, reload_time, health=1, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Draw the tank body (rectangle)
            Color(0.9, 0.9, 0.9)
            self.tank_image_source = "Tank 1 copy.png"
            self.rect = Rectangle(source=self.tank_image_source, pos=self.pos, size=self.size)
        
            # Draw the cannon
            self.cannon_length = self.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.size[0] * 0.03  # Adjust the width of the cannon as needed
            self.cannon = Line(points=(self.center_x, self.center_y, 
                                    self.center_x + self.cannon_length, self.center_y + self.cannon_width), width=self.cannon_width)
            
            self.ammo = ammo
            self.max_ammo = max_ammo
            self.reload_time = reload_time
            self.health=health
            self.max_health = health

            self.cannon_length = self.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.size[0] * 0.02  # Adjust the width of the cannon as needed
            self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
            self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
            self.max_bar_lenght = self.width * 1.6 

            Color(1, 0.9, 0, 0.3)
            self.max_reload_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.3, self.right+self.width*0.1, self.top + self.height*0.3), width=self.height*0.05)

            Color(1,0.9,0,1)
            self.reload_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.3, self.right+self.width*0.1, self.top + self.height*0.3), width=self.height*0.05)

            Color(1,0,0,0.3)
            self.max_health_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.7, self.right+self.width*0.1, self.top + self.height*0.7), width=self.height*0.05)

            Color(1,0,0)
            self.health_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.7, self.right+self.width*0.1, self.top + self.height*0.7), width=self.height*0.05)



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
        
        if not self.reloading:
            self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
            
        self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
        self.max_bar_lenght = self.width * 1.6 

                
        # Update the reload bar
        reload_bar_height = self.height * 0.12  # Adjust the width of the reload bar as needed
        self.reload_bar.points = (self.x + self.width +self.width * 0.3 - self.reload_bar_lenght, self.top + self.height * 0.3,
                                 self.x + self.width * 1.3 , self.top + self.height * 0.3)
        
        self.max_reload_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.3,
                            self.x - self.width * 0.3 + self.max_bar_lenght, self.top + self.height * 0.3)

        health_bar_height = self.height * 0.12  # Adjust the width of the reload bar as needed
        self.health_bar.points = (self.x + self.width +self.width * 0.3 - self.health_bar_lenght, self.top + self.height * 0.7,
                                 self.x + self.width * 1.3 , self.top + self.height * 0.7)
        
        self.max_health_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.7,
                                self.x - self.width * 0.3 + self.max_bar_lenght, self.top + self.height * 0.7)

        self.health_bar.width = health_bar_height        
        self.reload_bar.width = reload_bar_height 
        self.max_health_bar.width = health_bar_height   
        self.max_reload_bar.width = reload_bar_height   
        
    def update_health_bar(self):
        self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
        self.health_bar.points = (self.x + self.width +self.width * 0.3 - self.health_bar_lenght, self.top + self.height * 0.3,
                                 self.x + self.width * 1.3 , self.top + self.height * 0.3)

    def shoot(self, game):
        weapon = game.enemy_weapon

        firerate = weapon.get("firerate")
        
        if time.time() - self.last_shot_time >= 1 / firerate and not self.reloading:
            bullet = Bullet(radius=weapon.get("radius", None)*game.cell_size)
            
            bullet.angle = self.cannon_angle
            bullet.pos = [self.center_x + (self.cannon_length +5) * math.cos(self.cannon_angle)-bullet.radius, self.center_y + (self.cannon_length +5) * math.sin(self.cannon_angle)-bullet.radius]
            bullet.color = (0.5, 0.5, 0.5, 1)
                        
            bullet.effect_diameter = weapon.get("effect_diameter", None)
            bullet.mass = weapon.get("mass", None)*game.cell_size
            bullet.speed = weapon.get("speed", None)*game.cell_size
            bullet.drill = weapon.get("drill", None)
            bullet.repeat_explosions = weapon.get("repeat_explosions", None)
            bullet.laser = weapon.get("laser", None)
            
            game.bullets.add(bullet)
            game.add_widget(bullet)
            
            self.last_shot_time = time.time()
            
            self.ammo -= 1
            
            self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
            self.reload_bar.points = (self.x + self.width +self.width * 0.3 - self.reload_bar_lenght, self.top + self.height * 0.3,
                                self.x + self.width * 1.3 , self.top + self.height * 0.3)

            if self.ammo <= 0:
                self.reload_weapon()
            
            self.last_timepoint = time.time()

    def enemy_ai(self, game, start_x, start_y, target_x, target_y, speed, g):
        x = target_x - start_x
        y = target_y - start_y

        distance_to_target = math.sqrt(x ** 2 + y ** 2)  # Calculate distance to target
        
        weapon = game.enemy_weapon
        firerate = weapon.get("firerate")
        
        if distance_to_target <= self.weapon_range * game.cell_size and time.time() - self.last_shot_time >= 1 / firerate and not self.reloading:
            discriminant = speed ** 4 - g * (g * x ** 2 + 2 * y * speed ** 2)

            if discriminant < 0:
                self.cannon_angle = math.pi
            else:
                numerator = speed ** 2 - math.sqrt(discriminant) if self.direct_hitter else speed ** 2 + math.sqrt(discriminant)
                denominator = g * x

                if denominator == 0:
                    self.cannon_angle = math.pi / 2 if numerator > 0 else -math.pi / 2
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
            
    def move_right(self, cell_size):
        self.x += self.speed*cell_size
    
    def move_left(self, cell_size):
        self.x -= self.speed*cell_size
    
    def fall(self, cell_size):
        self.y -= self.mass*cell_size
        
    def hit(self, damage = 1):
        self.health -= damage
        self.update_health_bar()
            
    def reload_weapon(self):
        if not self.reloading:
            self.reloading = True
            self.last_timepoint = time.time()
            self.ammo = 0  # Reset ammunition count when reloading

    def check_reloading(self):
        if self.reloading:
            if time.time() - self.last_timepoint >= self.reload_time:
                self.reloading = False
                self.ammo = self.max_ammo  # Refill ammunition count after reloading  
                self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
                self.reload_bar.points = (self.x + self.width +self.width * 0.3 - self.reload_bar_lenght, self.top + self.height * 0.3,
                                self.x + self.width * 1.3 , self.top + self.height * 0.3)

                
            self.reload_bar_lenght = self.width * 1.6 * (time.time() - self.last_timepoint)/self.reload_time
            self.reload_bar.points = (self.x + self.width +self.width * 0.3 - self.reload_bar_lenght, self.top + self.height * 0.3,
                                 self.x + self.width * 1.3 , self.top + self.height * 0.3)

            
#-------------------------------------------------------------------------tank-------------------------------------------------------------------------#

class Tank(Widget):
    cannon_angle = NumericProperty(0)
    speed = NumericProperty(0.2)
    mass = NumericProperty(0.3)
    last_timepoint = NumericProperty(0)
    
    bullet_preds = ListProperty([])
    num_preds = NumericProperty(3)
    dot_size = NumericProperty(1)
    dot_step_size = NumericProperty(5)
    
    reloading = BooleanProperty(False)
    reload_bar_lenght = NumericProperty(0)

    is_shooting = BooleanProperty(False)
    shoot_start_time = NumericProperty(0)
    
    total_shots = NumericProperty(0)
        
    def __init__(self, health = 50, ammo=10, max_ammo = 10, reload_time = 10, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Draw the tank body (rectangle)
            Color(0.9, 0.9, 0.9)
            self.tank_image_source = "Tank 1.png"
            self.rect = Rectangle(source=self.tank_image_source, pos=self.pos, size=self.size)
            
            self.health = health
            self.max_health = health
            self.ammo = ammo
            self.max_ammo = max_ammo
            self.reload_time = reload_time
            
            Color(0.0, 0.05, 0.0)
            # Draw the cannon
            self.cannon_length = self.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.size[0] * 0.02  # Adjust the width of the cannon as needed
            self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
            self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
            self.max_bar_lenght = self.width * 1.6

            self.cannon = Line(points=(self.x - self.width * 0.3, self.top + self.height * 0.3,
                                 self.x - self.width * 0.3 + self.reload_bar_lenght, self.top + self.height * 0.3), width=self.cannon_width)
            
            Color(1,0.9,0,0.3)
            self.max_reload_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.3, self.right+self.width*0.1, self.top + self.height*0.3), width=self.height*0.05)
            
            Color(1,0.9,0,1)
            self.reload_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.3, self.right+self.width*0.1, self.top + self.height*0.3), width=self.height*0.05)
            
            Color(1,0,0,0.3)
            self.max_health_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.7, self.right+self.width*0.1, self.top + self.height*0.7), width=self.height*0.05)

            Color(1,0,0,1)
            self.health_bar = Line(points=(self.x-self.width*0.1, self.top + self.height*0.7, self.right+self.width*0.1, self.top + self.height*0.7), width=self.height*0.05)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Update the cannon length and width
        self.cannon_length = self.size[1] * 1  # Adjust the length of the cannon as needed
        self.cannon_width = self.size[0] * 0.06  # Adjust the width of the cannon as needed
        
        # Update the cannon points
        self.cannon.points = (self.center_x, self.center_y, 
                            self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                            self.center_y + self.cannon_length * math.sin(self.cannon_angle))
        self.cannon.width = self.cannon_width
        
        if not self.reloading:
            self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
        
        self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
        self.max_bar_lenght = self.width * 1.6

        # Update the reload bar
        reload_bar_height = self.height * 0.12  # Adjust the width of the reload bar as needed
        self.reload_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.3,
                                 self.x - self.width * 0.3 + self.reload_bar_lenght, self.top + self.height * 0.3)
        
        self.max_reload_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.3,
                                 self.x - self.width * 0.3 + self.max_bar_lenght, self.top + self.height * 0.3)

        health_bar_height = self.height * 0.12  # Adjust the width of the reload bar as needed
        self.health_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.7,
                                 self.x - self.width * 0.3 + self.health_bar_lenght, self.top + self.height * 0.7)
        
        self.max_health_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.7,
                                 self.x - self.width * 0.3 + self.max_bar_lenght, self.top + self.height * 0.7)


        self.health_bar.width = health_bar_height
        self.reload_bar.width = reload_bar_height 
        self.max_health_bar.width = health_bar_height   
        self.max_reload_bar.width = reload_bar_height   
            
    def update_health_bar(self):
        self.health_bar_lenght = self.width * 1.6 * self.health/self.max_health
        self.health_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.7,
                                 self.x - self.width * 0.3 + self.health_bar_lenght, self.top + self.height * 0.7)
        
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
        
        if time.time() - self.last_timepoint >= 1 / firerate and not self.reloading:
            bullet = Bullet(radius=weapon.get("radius", None) * game.cell_size)
            
            bullet.angle = self.cannon_angle
            bullet.pos = [
                self.center_x + (self.cannon_length * 2) * math.cos(self.cannon_angle) - bullet.radius,
                self.center_y + (self.cannon_length * 2) * math.sin(self.cannon_angle) - bullet.radius
            ]
            bullet.color = (0.5, 0.5, 0.5, 1)
            
            bullet.effect_diameter = weapon.get("effect_diameter", None)
            bullet.mass = weapon.get("mass", None) * game.cell_size
            bullet.speed = weapon.get("speed", None) * game.cell_size * self.calculate_shoot_speed_multiplier()
            bullet.drill = weapon.get("drill", None)
            bullet.repeat_explosions = weapon.get("repeat_explosions", None)
            bullet.laser = weapon.get("laser", None)
            
            game.bullets.add(bullet)
            game.add_widget(bullet)
            
            self.ammo -= 1
            self.total_shots += 1  # Increment the total shots counter
            
            self.reload_bar_lenght = self.width * 1.6 * self.ammo / self.max_ammo
            self.reload_bar.points = (
                self.x - self.width * 0.3, self.top + self.height * 0.3,
                self.x - self.width * 0.3 + self.reload_bar_lenght, self.top + self.height * 0.3
            )
            
            if self.ammo <= 0:
                self.reload_weapon()
            
            self.last_timepoint = time.time()
            self.shoot_start_time = 0
            
    def calculate_shoot_speed_multiplier(self):
        hold_duration = time.time() - self.shoot_start_time
        return min(1, hold_duration*0.5)  # Cap the speed multiplier at 2x
    
    def move_right(self, cell_size):
        self.x += self.speed*cell_size
    
    def move_left(self, cell_size):
        self.x -= self.speed*cell_size
    
    def fall(self, cell_size):
        self.y -= self.mass*cell_size
        
    def draw_preds(self, game):
        
        if len(self.bullet_preds) > 1:
            for pred in self.bullet_preds:
                self.canvas.remove(pred)
            self.bullet_preds.clear()
        
        if self.shoot_start_time != 0:

            for i in range(self.num_preds):
                i = i + 1
                weapon = game.weapons[game.current_weapon]
                mass = weapon.get("mass", None) * game.cell_size
                speed = weapon.get("speed", None) * game.cell_size * self.calculate_shoot_speed_multiplier()
                radius = weapon.get("radius", None) * game.cell_size
                cannon_pos = [
                    self.center_x + self.cannon_length * math.cos(self.cannon_angle) - self.dot_size / 2,
                    self.center_y + self.cannon_length * math.sin(self.cannon_angle) - self.dot_size / 2
                ]
                
                with self.canvas:
                    Color(1, 1, 1, 1 / i)
                    
                    dot_x = cannon_pos[0] + speed * math.cos(self.cannon_angle) * i * self.dot_step_size
                    dot_y = cannon_pos[1] + i * self.dot_step_size * (speed * math.sin(self.cannon_angle)) - 0.5 * mass * i * self.dot_step_size * i * self.dot_step_size
                    
                    dot = Ellipse(pos=(dot_x - radius, dot_y - radius), size=(self.dot_size * game.cell_size, self.dot_size * game.cell_size))
                    self.bullet_preds.append(dot)
                    
    def hit(self, game, damage=1):
        self.health -= damage
        self.update_health_bar()
        if self.health < 1:
            self.save_score(game.level)
            App.get_running_app().root.current = 'game_over'
            game_over_screen = App.get_running_app().root.get_screen('game_over')
            game_over_screen.ids.shots_label.text = f'{self.total_shots}'
            game_over_screen.ids.level_label.text = f'{game.level}'
            
    def save_score(self, level):
        score_data = {
            "level": level,
            "total_shots": self.total_shots
        }

        try:
            with open('scores.json', 'r') as file:
                scores = json.load(file)
        except FileNotFoundError:
            scores = []

        scores.append(score_data)
        scores = sorted(scores, key=lambda x: x['level'], reverse=True)[:5]

        with open('scores.json', 'w') as file:
            json.dump(scores, file)
            
    def reload_weapon(self):
        if not self.reloading:
            self.reloading = True
            self.last_timepoint = time.time()
            self.ammo = 0  # Reset ammunition count when reloading

    def check_reloading(self):
        if self.reloading:
            if time.time() - self.last_timepoint >= self.reload_time:
                self.reloading = False
                self.ammo = self.max_ammo  # Refill ammunition count after reloading  
                self.reload_bar_lenght = self.width * 1.6 * self.ammo/self.max_ammo
                self.reload_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.3, self.x - self.width * 0.3 + self.reload_bar_lenght, self.top + self.height * 0.3)
                
            self.reload_bar_lenght = self.width * 1.6 * (time.time() - self.last_timepoint)/self.reload_time
            self.reload_bar.points = (self.x - self.width * 0.3, self.top + self.height * 0.3,
                                self.x - self.width * 0.3 + self.reload_bar_lenght, self.top + self.height * 0.3)
            
    def switch_weapon(self, weapon):
        self.ammo = 0
        self.max_ammo = weapon["ammo_number"]
        self.reload_time = weapon["reload_speed"]
        self.reloading = False
        self.last_timepoint = time.time()
        self.reload_weapon()
        
        
#------------------------------------------------------------------------- bullets -------------------------------------------------------------------------#

class Bullet(Widget):
    mass = NumericProperty(1)
    effect_diameter = NumericProperty(300)
    speed = NumericProperty(2)
    flighttime = NumericProperty(0)
    angle = NumericProperty(0)
    radius = NumericProperty(5)
    drill = NumericProperty(0)
        
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
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle) - self.mass*(self.flighttime+1)
        self.flighttime += 1
            
    def explode(self, game):
        explosion = Explosion(effect_diameter=self.effect_diameter * game.cell_size, pos=self.pos)
        game.add_widget(explosion)
        game.explosions.add(explosion)
        
    def recalculate_angle(self, normal_vector):
        # Calculate the angle of incidence based on the bullet's current velocity
        angle_of_incidence = math.atan2(self.speed * math.sin(self.angle), self.speed * math.cos(self.angle))

        # Calculate the angle between the normal vector and the horizontal axis
        angle_normal = math.atan2(normal_vector[1], normal_vector[0])

        # Calculate the angle of reflection using the angle of incidence and the angle between the normal vector and the horizontal axis
        angle_reflection = 2 * angle_normal - angle_of_incidence + math.pi
        
        # Normalize the angle to ensure it falls within the appropriate range
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
    chunk_number = NumericProperty(random.randint(50, 75))
    chunks = ListProperty([])

    level = NumericProperty(1)
    
    def __init__(self, **kwargs):
#------------------------------------------------------------------------- Weapons -------------------------------------------------------------------------#

        self.weapons = [{
            "name": "Bullet",
            "mass": 0.025,
            "effect_diameter": 3,
            "speed": 2,
            "firerate": 2,
            "reload_speed": 1,
            "ammo_number": 5,
            "radius": 0.5,
            "drill": 0,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Bombshell",
            "mass": 0.05,
            "effect_diameter": 10,
            "speed": 1.3,
            "firerate": 3,
            "reload_speed": 1,
            "ammo_number": 30,
            "radius": 0.3,
            "drill": 10,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Laser",
            "mass": 0.0,
            "effect_diameter": 1,
            "speed": 1,
            "firerate": 3,
            "reload_speed": 1,
            "ammo_number": 30,
            "radius": 0.5,
            "drill": 500,
            "repeat_explosions": False,
            "laser": True,
        }]
        
        self.current_weapon = 0
        
        self.enemy_weapon = {
            "name": "sniper",
            "mass": 0.0001,
            "effect_diameter": 5,
            "speed": 2,
            "firerate": 0.0001,
            "reload_speed": 6,
            "ammo_number": 300,
            "radius": 0.6,
            "drill": 0,
            "repeat_explosions": False,
            "laser": False,
        }

#------------------------------------------------------------------------- Init Game -------------------------------------------------------------------------#

        super().__init__(**kwargs)        
        self.grid_size_x = self.chunk_number*self.chunk_size-1  # Define the size of the grid
        self.grid_size_y = 50 # Define the size of the grid
        self.cell_size = self.width / self.grid_size_x
        self.prev_cell_size = self.cell_size

        for i in range(self.chunk_number):
            
            self.chunks.append({"ground":[], "explosions":[], "bullets":[], "obstacles":[], "x_limit":(((i+1)*self.chunk_size-self.chunk_size)*self.cell_size, ((i+1)*self.chunk_size)*self.cell_size)})
        
        # Define the parameters for scaling
        amplitude = random.randint(3, 5)  # Half of the peak-to-peak height (from -1 to 1)
        frequency = random.randint(1, 3)
        offset_y = amplitude +10
        offset_x = random.randint(0, int(self.grid_size_x/frequency))
        # Calculate the heights using a sine function
        self.heights = []
        for x in range(self.grid_size_x):
            # Scale the sine function to fit within [0, 10]
            y = math.sin(((x+offset_x) * (2 * math.pi / self.grid_size_x))*frequency) * amplitude + offset_y

            self.heights.append(round(y))  # Round the result to the nearest integer
        
        self.ground_tiles = set()
        self.bullets = set()
        self.explosions = set()
        self.obstacles = set()
        
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
        self.bind(on_touch_up=self.onMouseReleased)

#-------------------------------------------------------------------------map generation-------------------------------------------------------------------------#
    def draw_background(self):
        # Draw the blue sky background
        with self.canvas.before:
            current_stage = (self.level // 5) % 5
            if current_stage == 0:
                Rectangle(source="./trincea.png", spos=(0, 0), size=(Window.width, Window.height))   
            elif current_stage == 1:
                Rectangle(source="./città.png", spos=(0, 0), size=(Window.width, Window.height))   
            elif current_stage == 2:
                Rectangle(source="./luna.png", spos=(0, 0), size=(Window.width, Window.height))   
                    
    def terrain_gen(self):
        # Generate terrain

        x_offset = (self.width - self.grid_size_x * self.cell_size) / 2

        x = 0
        chunk = 0

        wormhole_colors = {}

        # Create a group for ground objects
        while x < len(self.heights):
            if (x + 1) % self.chunk_size == 0:
                chunk += 1
                c = 0

            for y in range(self.heights[x]):
                ground = Ground()
                current_stage = (self.level // 5) % 5

                if y == self.heights[x] - 1:
                    if current_stage == 0:
                        ground_color = Color(0.93, 0.79, 0.69)  # light sand color
                    elif current_stage == 1:
                        ground_color = Color(0.05, 0.05, 0.05)  # light concrete color
                    elif current_stage == 2:
                        ground_color = Color(0.6, 0.6, 0.6)  # light moon color

                elif y == self.heights[x] - 2:
                    if current_stage == 0:
                        ground_color = Color(0.91, 0.76, 0.65)  # slightly darker sand color
                    elif current_stage == 1:
                        ground_color = Color(0.1, 0.1, 0.1)  # light concrete color
                    elif current_stage == 2:
                        ground_color = Color(0.55, 0.55, 0.55)  # light moon color

                elif y == self.heights[x] - 3:
                    if current_stage == 0:
                        ground_color = Color(0.89, 0.69, 0.53)  # darker sand color
                    elif current_stage == 1:
                        ground_color = Color(0.15, 0.15, 0.15)  # even darker concrete color
                    elif current_stage == 2:
                        ground_color = Color(0.5, 0.5, 0.5)  # light moon color

                elif y < 1:
                    ground.bulletproof = True
                    if current_stage == 0:
                        ground_color = Color(0.55, 0.47, 0.37)  # rocky ground
                    elif current_stage == 1:
                        ground_color = Color(0.1, 0.1, 0.1)  # even darker concrete color
                    elif current_stage == 2:
                        ground_color = Color(0.1, 0.1, 0.1)  # light moon color

                else:
                    if current_stage == 0:
                        ground_color = Color(0.82, 0.71, 0.55)  # base desert color
                    elif current_stage == 1:
                        ground_color = Color(0.2, 0.2, 0.2)  # base street color
                    elif current_stage == 2:
                        ground_color = Color(0.4, 0.4, 0.4)  # light moon color

                ground.canvas.add(ground_color)
                ground_pos_y = (y * self.cell_size)
                ground_rectangle = Rectangle(
                    pos=((x * self.cell_size) + x_offset, ground_pos_y), size=(self.cell_size, self.cell_size))
                ground.canvas.add(ground_rectangle)
                ground.size_hint = (None, None)
                ground.size = (self.cell_size, self.cell_size)
                ground.pos = ((x * self.cell_size) + x_offset, ground_pos_y)

                self.chunks[chunk]["ground"].append(ground)
                self.ground_tiles.add(ground)  # Add ground to the group
                self.add_widget(ground)
            x += 1

        x = 0
        chunk = 0

        while x < len(self.heights):
            if (x + 1) % self.chunk_size == 0:
                chunk += 1
                c = 0

            if x % 4 == 0 and x != 0 and x > 15:
                rand = random.randint(0, max(100-self.level, 20)) 
                if rand < 10:
                    # Generate a mirror obstacle
                    h = self.heights[x]
                    mirror_height = random.randint(10, 20)

                    # Randomly choose if the mirror is reflective (blue) or elastic (red gum)
                    is_reflective = random.choice([True, False])

                    for i in range(mirror_height):
                        obstacle = Ground()

                        if is_reflective:
                            obstacle_color = Color(0, 0.2, 0.8, 0.4)  # Reflective: blue
                            obstacle.reflective = True
                            obstacle.elastic = False
                        else:
                            obstacle_color = Color(0.8, 0.1, 0.1, 0.6)  # Elastic: red gum
                            obstacle.reflective = False
                            obstacle.elastic = True

                        obstacle.canvas.add(obstacle_color)
                        obstacle_pos_y = (h * self.cell_size + i * self.cell_size)
                        obstacle_rectangle = Rectangle(
                            pos=((x * self.cell_size) + x_offset, obstacle_pos_y), size=(self.cell_size, self.cell_size))
                        obstacle.canvas.add(obstacle_rectangle)
                        obstacle.size = (self.cell_size, self.cell_size)
                        obstacle.pos = ((x * self.cell_size) + x_offset, obstacle_pos_y)

                        self.chunks[chunk]["ground"].append(obstacle)
                        self.ground_tiles.add(obstacle)  # Add ground to the group
                        self.add_widget(obstacle)

                elif 11 <= rand <= 12:
                    radius = random.randint(2, 3)
                    height_above_ground = random.randint(4, 6)

                    # Generate a gravity obstacle
                    obstacle = Obstacle(
                        cell_size=self.cell_size,
                        gravity=True,
                        pos=((x * self.cell_size), (self.heights[x] + height_above_ground) * self.cell_size),
                        radius=radius,
                        effectRadius=radius*3,
                    )
                    self.obstacles.add(obstacle)
                    self.add_widget(obstacle)

                elif 13 <= rand <= 14:
                    # Generate a wormhole obstacle with random height above ground and random radius
                    height_above_ground = random.randint(5, 10)
                    radius = random.randint(2, 3)
                    wormhole_exit_x = (x * self.cell_size) + random.randint(15, 20) * self.cell_size
                    wormhole_exit_y = ((self.heights[x] + height_above_ground) * self.cell_size) + random.randint(-3, 3) * self.cell_size
                    
                    if wormhole_exit_x > self.grid_size_x * self.cell_size:
                        wormhole_exit_x = (self.grid_size_x-20) * self.cell_size
                    
                    color = (random.randint(0, 10)*0.1, random.randint(0, 10)*0.1, random.randint(0, 10)*0.1)

                    obstacle = Obstacle(
                        cell_size=self.cell_size,
                        wormhole=True,
                        gravity=False,
                        wormhole_exit=(wormhole_exit_x, wormhole_exit_y),
                        radius=radius,
                        color=color,
                        pos=((x * self.cell_size), (self.heights[x] + height_above_ground) * self.cell_size)
                    )
                    self.obstacles.add(obstacle)
                    self.add_widget(obstacle)

                elif 15 <= rand <= 16:
                    radius = random.randint(2, 3)
                    height_above_ground = random.randint(3, 6)

                    # Generate a gravity obstacle
                    obstacle = Obstacle(
                        cell_size=self.cell_size,
                        gravity=True,
                        pos=((x * self.cell_size), (self.heights[x] + height_above_ground) * self.cell_size),
                        radius=radius,
                        effectRadius=radius*3,
                        repulsive=True
                    )
                    self.obstacles.add(obstacle)
                    self.add_widget(obstacle)

            x += 1  
                            
    def create_tank(self, new_pos = None):
        weapon = self.weapons[self.current_weapon]

        self.tank = Tank(health=10, ammo=weapon["ammo_number"], max_ammo=weapon["ammo_number"], reload_time=weapon["reload_speed"])
        self.tank.size_hint = (None, None)
        
        
        if new_pos == None:
            self.tank.pos = (self.cell_size, (self.heights[0]+1)*(self.cell_size))
        else:
            self.tank.pos = (new_pos[0], new_pos[1])  # Center tank horizontally

            
        self.tank.size = (self.cell_size*2, self.cell_size*2)
        
        self.add_widget(self.tank)  # Add tank widget to the game
    
    def spawn_enemy(self, new_pos=None):
        self.enemy = Enemy(self.enemy_weapon["ammo_number"], self.enemy_weapon["ammo_number"], self.enemy_weapon["reload_speed"])
        self.enemy.size_hint = (None, None)
        self.enemy.size = (self.cell_size*2, self.cell_size*2)

        if new_pos == None:
            self.enemy.pos = (self.width - self.cell_size*10 - self.enemy.size[0], (self.heights[-5] + 2) * self.cell_size)
        else:
            self.enemy.pos = (new_pos[0], new_pos[1])  # Center tank horizontally        

        self.add_widget(self.enemy)  # Add tank widget to the game
        
        # Randomize enemy stats based on the current level
        self.randomize_enemy_stats()
                
    def randomize_enemy_stats(self):
        # Increase enemy stats based on the current level
        level_multiplier = 1 + (self.level * 0.3)
        
        self.enemy.speed = random.uniform(1, 4) * level_multiplier
        self.enemy.mass = random.uniform(1, 1.5) * level_multiplier
        self.enemy.moving = random.choice([False, False])
        self.enemy.health = random.randint(1, 2) * level_multiplier
        self.enemy.max_health = self.enemy.health
        self.enemy.weapon_range = random.uniform(200, 300) * level_multiplier
        self.enemy.direct_hitter = random.choice([True, False])
        self.enemy.imprecision = random.uniform(0.01, 0.1) / level_multiplier
        
        # Increase enemy weapon stats based on the current level
        self.enemy_weapon["speed"] = random.uniform(1, 2)
        self.enemy_weapon["mass"] = random.uniform(0.01, 0.05) / level_multiplier
        self.enemy_weapon["effect_diameter"] = random.randint(1, 3) * level_multiplier
        self.enemy_weapon["firerate"] = random.uniform(0.1, 0.5) * level_multiplier
        self.enemy_weapon["reload_speed"] = random.uniform(1, 3) * level_multiplier
        self.enemy_weapon["ammo_number"] = random.randint(1, 3) * level_multiplier
        self.enemy_weapon["radius"] = random.uniform(0.3, 0.8) * level_multiplier
        self.enemy_weapon["drill"] = random.randint(0, 2) * level_multiplier
        self.enemy_weapon["repeat_explosions"] = random.choice([True, False])
        self.enemy_weapon["laser"] = False
        
        # Apply the new stats to the enemy
        self.enemy.ammo = self.enemy_weapon["ammo_number"]
        self.enemy.max_ammo = self.enemy_weapon["ammo_number"]
        self.enemy.reload_time = self.enemy_weapon["reload_speed"]  
        
    def store_level_stats(self):
        level_stats = {
            "level": self.level,
            "enemy": {
                "speed": self.enemy.speed,
                "mass": self.enemy.mass,
                "moving": self.enemy.moving,
                "health": self.enemy.health,
                "max_health": self.enemy.max_health,
                "weapon_range": self.enemy.weapon_range,
                "direct_hitter": self.enemy.direct_hitter,
                "imprecision": self.enemy.imprecision,
                "ammo": self.enemy.ammo,
                "max_ammo": self.enemy.max_ammo,
                "reload_time": self.enemy.reload_time
            },
            "enemy_weapon": self.enemy_weapon,
            "terrain": {
                "chunk_number": self.chunk_number,
                "heights": self.heights,
                "chunk_size": self.chunk_size
            }
        }

        with open('current_level_stats.json', 'w') as file:
            json.dump(level_stats, file, indent=4)
            
    def load_game(self, game_stats):
        self.level = game_stats['level']
        self.enemy_weapon = game_stats['enemy_weapon']

        # Set enemy stats
        self.enemy.speed = game_stats['enemy']['speed']
        self.enemy.mass = game_stats['enemy']['mass']
        self.enemy.moving = game_stats['enemy']['moving']
        self.enemy.health = game_stats['enemy']['health']
        self.enemy.max_health = game_stats['enemy']['max_health']
        self.enemy.weapon_range = game_stats['enemy']['weapon_range']
        self.enemy.direct_hitter = game_stats['enemy']['direct_hitter']
        self.enemy.imprecision = game_stats['enemy']['imprecision']
        self.enemy.ammo = game_stats['enemy']['ammo']
        self.enemy.max_ammo = game_stats['enemy']['max_ammo']
        self.enemy.reload_time = game_stats['enemy']['reload_time']

        # Set terrain stats
        self.chunk_number = game_stats['terrain']['chunk_number']
        self.heights = game_stats['terrain']['heights']
        self.chunk_size = game_stats['terrain']['chunk_size']

        # Clear all previous level objects
        self.canvas.clear()
        self.clear_widgets()
        self.ground_tiles.clear()
        self.bullets.clear()
        self.explosions.clear()
        self.obstacles.clear()
        
        # Initialize chunks and cell_size
        self.chunks.clear()
        self.grid_size_x = self.chunk_number * self.chunk_size - 1
        self.cell_size = self.width / self.grid_size_x
        
        for i in range(self.chunk_number):
            self.chunks.append({"ground":[], "explosions":[], "bullets":[], "obstacles":[], "x_limit":(((i+1)*self.chunk_size-self.chunk_size)*self.cell_size, ((i+1)*self.chunk_size)*self.cell_size)})
        
        # Generate the terrain and initialize the game objects
        self.draw_background()
        self.terrain_gen()
        self.create_tank()
        self.spawn_enemy()
                        
    def regenerate_map(self):
        # Call store_level_stats before regenerating the map
        self.store_level_stats()
        
        # Clear all previous level objects
        self.canvas.clear()
        self.clear_widgets()
        self.ground_tiles.clear()
        self.bullets.clear()
        self.explosions.clear()
        self.obstacles.clear()
        
        # Generate new parameters for the new map
        self.chunk_number = random.randint(50, 75)
        self.chunks.clear()

        amplitude = random.randint(3, 6)
        frequency = random.randint(1, 3)
        offset_y = amplitude + 10
        offset_x = random.randint(0, int(self.grid_size_x/frequency))
        
        self.heights = []
        self.grid_size_x = self.chunk_number * self.chunk_size - 1  # Redefine grid size based on new chunk_number
        self.cell_size = self.width / self.grid_size_x
        
        for i in range(self.chunk_number):
            self.chunks.append({"ground":[], "explosions":[], "bullets":[], "obstacles":[], "x_limit":(((i+1)*self.chunk_size-self.chunk_size)*self.cell_size, ((i+1)*self.chunk_size)*self.cell_size)})

        for x in range(self.grid_size_x):
            y = math.sin(((x+offset_x) * (2 * math.pi / self.grid_size_x)) * frequency) * amplitude + offset_y
            self.heights.append(round(y))
        
        self.draw_background()
        self.terrain_gen()
        self.create_tank()
        self.spawn_enemy()
        
        # Randomize enemy stats based on the new level
        self.randomize_enemy_stats()
                
#-------------------------------------------------------------------------system functions-------------------------------------------------------------------------#
    def on_size(self, *args):
        
        prev_cell_size = self.prev_cell_size
        self.cell_size = self.width / self.grid_size_x
        self.prev_cell_size = self.cell_size
                        
        # Redraw grid and background when the size of the widget changes
        self.remove_widget(self.tank)
        self.canvas.clear()
        self.ground_tiles.clear()
        self.bullets.clear()
        self.explosions.clear()
        self.obstacles.clear()
        
        
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
        movement_distance = self.tank.speed*self.cell_size # Adjust speed based on screen size
        tank_falling_distance = self.tank.mass*self.cell_size
        
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
        
        enemy_dead = False

        for i in range(self.chunk_number):
            if self.chunks[i]["x_limit"][0] <= self.tank.x <= self.chunks[i]["x_limit"][1] or self.chunks[i]["x_limit"][0] <= self.tank.x + self.tank.width <= self.chunks[i]["x_limit"][1]:
                # Check if the current chunk has already been processed
                if i not in tank_processed_chunks:
                    tank_ground_to_render.extend(self.chunks[i]["ground"])
                    tank_processed_chunks.add(i)

                if i - 1 > -1 and (i - 1) not in tank_processed_chunks and ("left" in self.keys_pressed or "a" in self.keys_pressed):
                    tank_ground_to_render.extend(self.chunks[i - 1]["ground"])
                    tank_processed_chunks.add(i - 1)

                if i + 1 < self.chunk_number and (i + 1) not in tank_processed_chunks and ("right" in self.keys_pressed or "d" in self.keys_pressed):
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

            for bullet in self.bullets:
                if self.chunks[i]["x_limit"][0] <= bullet.x <= self.chunks[i]["x_limit"][1] or self.chunks[i]["x_limit"][0] <= bullet.x + bullet.width <= self.chunks[i]["x_limit"][1]:
                    # Check if the current chunk has already been processed
                    if i not in bullet_processed_chunks:
                        bullet_ground_to_render.extend(self.chunks[i]["ground"])
                        bullet_processed_chunks.add(i)

                    if i - 1 > -1 and (i - 1) not in bullet_processed_chunks and bullet.prev_coordinates[0] > bullet.x:
                        bullet_ground_to_render.extend(self.chunks[i - 1]["ground"])
                        bullet_processed_chunks.add(i - 1)

                    if i + 1 < self.chunk_number and (i + 1) not in bullet_processed_chunks and bullet.prev_coordinates[0] < bullet.x:
                        bullet_ground_to_render.extend(self.chunks[i + 1]["ground"])
                        bullet_processed_chunks.add(i + 1)
                        
            for explosion in self.explosions:

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
                        
                                
        for explosion in self.explosions:
            if explosion.radius*2 < explosion.effect_diameter:
                    explosion.increase_explosion_radius()
            else:
                explosions_to_remove.append(explosion)
                
                touching, rect2 = self.check_collision_circle(circle=explosion, rect=self.tank) 
                if touching:
                    self.tank.hit(game = self)
                
                touching, rect2 = self.check_collision_circle(circle=explosion, rect=self.enemy) 
                if touching:
                    self.enemy.hit()
                    if self.enemy.health <= 0:
                        self.level += 1
                        enemy_dead = True    
                                        
                for ground in explosions_ground_to_render:
                    if not ground.elastic and not ground.bulletproof:
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
        
        enemy_left, enemy_right = self.enemy.enemy_ai(game=self, 
                        start_x = self.enemy.cannon.points[2], 
                        start_y = self.enemy.cannon.points[3], 
                        target_x = self.tank.center_x, 
                        target_y = self.tank.center_y, 
                        speed = self.enemy_weapon["speed"]*self.cell_size, 
                        g = self.enemy_weapon["mass"]*self.cell_size)#move the player cannon

        enemy_range_x = (self.enemy.x - self.cell_size * 2, self.enemy.x + self.cell_size * 2)#we use theese to improve performance by checking collision of only neraby objects
        enemy_range_y = (self.enemy.y - self.cell_size * 2, self.enemy.y + self.cell_size * 2)
        
        enemy_movement_distance = self.enemy.speed*self.cell_size # Adjust speed based on screen size
        enemy_falling_distance = self.enemy.mass*self.cell_size

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
            self.tank.move_right(cell_size=self.cell_size)

        if left:
            self.tank.move_left(cell_size=self.cell_size)

        self.tank.set_cannon_angle(self.mouse)#move the player cannon
            
        if enemy_falling:
            self.enemy.fall(self.cell_size)
            if self.enemy.y < 0:
                self.enemy.y = self.cell_size+1
        
        if enemy_right:
            self.enemy.move_right(cell_size=self.cell_size)

        if enemy_left:
            self.enemy.move_left(cell_size=self.cell_size)
            

        #-------------neutral functions --------------------------------        
        #bullet physics
        for bullet in self.bullets:
            bullet.trajectory()  # move all the bullets
            
            touching, rect2 = self.check_collision_circle(circle=bullet, rect=self.tank) 
            if touching:
                if bullet.laser:
                    self.tank.hit(game = self)                    

                bullets_to_remove.append(bullet)
            
            touching, rect2 = self.check_collision_circle(circle=bullet, rect=self.enemy)
            if touching:
                if bullet.laser:
                    self.enemy.hit()
                    if self.enemy.health <= 0:
                        self.level += 1
                        enemy_dead = True                    

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
                        
                        nearest = self.nearest_side([bullet.prev_coordinates[0] + bullet.radius, bullet.prev_coordinates[1] + bullet.radius], ground.pos, ground.size[0])
                        
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
                                                
                        nearest = self.nearest_side([bullet.prev_coordinates[0] + bullet.radius, bullet.prev_coordinates[1] + bullet.radius], ground.pos, ground.size[0])
                        
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
                            normal_vector = [0, 0]  # Normal vector pointing to the left   

                        bullet.speed=bullet.speed*0.95
                        bullet.pos=bullet.prev_coordinates
                        bullet.flighttime=0
            
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
            
        
            for obstacle in self.obstacles:
                if obstacle.gravity and not bullet.laser:
                    obstacle.apply_gravity(bullet=bullet)
                if obstacle.wormhole:
                    obstacle.wormholeCheck(bullet)

            
        if "tab" in self.keys_up:
            if self.current_weapon >= len(self.weapons) -1:
                self.current_weapon = 0
            else:
                self.current_weapon += 1
            self.tank.switch_weapon(self.weapons[self.current_weapon])    
            
                            

        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                
                if bullet.laser:
                    for r in bullet.rays:
                        self.canvas.remove(r)
                else:                
                    bullet.explode(self) # remove bullet
                self.bullets.remove(bullet)
                self.remove_widget(bullet)
        
        for explosion in explosions_to_remove:
            self.explosions.remove(explosion)
            self.remove_widget(explosion)
            
        for ground in ground_to_remove:
            if ground in self.ground_tiles:
                self.ground_tiles.remove(ground)
                self.remove_widget(ground)
                
            for chunk in self.chunks:
                if ground in chunk["ground"]:
                    chunk["ground"].remove(ground)

#-------------------------------------------------------------------------reload functions-------------------------------------------------------------------------#    
    
        self.tank.check_reloading()
        
        self.enemy.check_reloading()
        
        if "r" in self.keys_pressed:
            self.tank.reload_weapon()
        
        self.keys_up = []
        
        if enemy_dead:  
            self.regenerate_map()
            
                
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
        half_width = width / 2
        
        # Calculate distances to each corner of the square
        distances_to_corners = [
            math.sqrt((x - bx) ** 2 + (y - by) ** 2),  # Bottom-left corner
            math.sqrt((x - bx - width) ** 2 + (y - by) ** 2),  # Bottom-right corner
            math.sqrt((x - bx) ** 2 + (y - by - width) ** 2),  # Top-left corner
            math.sqrt((x - bx - width) ** 2 + (y - by - width) ** 2)  # Top-right corner
        ]
        
        # Find the minimum distance to any corner
        min_distance_to_corner = min(distances_to_corners)
        
        # Define a threshold for corner detection
        corner_threshold = 0.5 * width  # Adjust as needed
        
        if min_distance_to_corner <= corner_threshold:
            # Projectile is close to a corner
            min_distance_index = distances_to_corners.index(min_distance_to_corner)
            # Determine the sides involved based on the closest corner
            if min_distance_index == 0:  # Bottom-left corner
                # Determine if the projectile is closer to the left or bottom side
                if x - bx < y - by:
                    return "left"
                else:
                    return "bottom"
            elif min_distance_index == 1:  # Bottom-right corner
                # Determine if the projectile is closer to the right or bottom side
                if bx + width - x < y - by:
                    return "right"
                else:
                    return "bottom"
            elif min_distance_index == 2:  # Top-left corner
                # Determine if the projectile is closer to the left or top side
                if x - bx < by + width - y:
                    return "left"
                else:
                    return "top"
            else:  # Top-right corner
                # Determine if the projectile is closer to the right or top side
                if bx + width - x < by + width - y:
                    return "right"
                else:
                    return "top"
        else:
            # No corner collision, proceed with detecting the nearest side
            # Calculate distances to each side of the square
            distance_top = abs(y - (by + width))
            distance_bottom = abs(y - by)
            distance_left = abs(x - bx)
            distance_right = abs(x - (bx + width))

            # Find the minimum distance
            min_distance = min(distance_top, distance_bottom, distance_left, distance_right)

            # Determine the nearest side based on the minimum distance
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
        if keycode[1] == 'escape':
            if App.get_running_app().root.current == 'game':
                App.get_running_app().switch_to_menu()
            return True  # Indicate that the key event has been handled
                            
    def on_key_up(self, keyboard, keycode):
        self.keys_pressed.remove(keycode[1])
        self.keys_up.append(keycode[1])

    def on_mouse_move(self, window, pos):
        self.mouse = Vector(pos)  # Update mouse position vector
        
    def onMousePressed(self, instance, touch):
        if touch.button == 'left':
            self.tank.is_shooting = True
            self.tank.shoot_start_time = time.time()
    
    def onMouseReleased(self, instance, touch):
        if touch.button == 'left':
            self.tank.is_shooting = False
            self.tank.shoot(self)
            
class CannonApp(App):
    def build(self):
        game = CannonGame()
        fps = 1 / game.fps if game.fps != 0 else 0
        Clock.schedule_interval(game.update, fps)
        return game

class OpenWindow(BoxLayout):
    pass

class MenuWindow(BoxLayout):
    pass

class HelpWindow(BoxLayout):
    pass

class SaveWindow(BoxLayout):
    pass

class Tutorial1Window(BoxLayout):
    pass

class Tutorial2Window(BoxLayout):
    pass

class Tutorial3Window(BoxLayout):
    pass

class Tutorial4Window(BoxLayout):
    pass

class Tutorial5Window(BoxLayout):
    pass

class Tutorial6Window(BoxLayout):
    pass

class Tutorial7Window(BoxLayout):
    pass

class GamecommandsWindow(BoxLayout):
    pass

class OpenScreen(Screen):
    pass

class MenuScreen(Screen):
    pass

class HelpScreen(Screen):
    pass

class SaveScreen(Screen):
    pass

class Tutorial1Screen(Screen):
    pass

class Tutorial2Screen(Screen):
    pass

class Tutorial3Screen(Screen):
    pass

class Tutorial4Screen(Screen):
    pass

class Tutorial5Screen(Screen):
    pass

class Tutorial6Screen(Screen):
    pass

class Tutorial7Screen(Screen):
    pass

class GamecommandsScreen(Screen):
    pass

class HallWindow(Screen):
    def on_pre_enter(self, *args):
        self.load_scores()

    def load_scores(self):
        try:
            with open('scores.json', 'r') as file:
                scores = json.load(file)
        except FileNotFoundError:
            scores = []

        # Sort scores by 'level' descending, then by 'total_shots' ascending
        top_scores = sorted(scores, key=lambda x: (-x['level'], x['total_shots']))[:6]

        score_labels = [
            self.ids.score_1,
            self.ids.score_2,
            self.ids.score_3,
            self.ids.score_4,
            self.ids.score_5,
            self.ids.score_6
        ]

        for i, score in enumerate(top_scores):
            score_labels[i].clear_widgets()
            label = Label(text=f"Score: {score['level']}    Shots: {score['total_shots']}", color=(1, 1, 1, 1))
            score_labels[i].add_widget(label)

        # Clear any remaining labels if there are less than 6 scores
        for i in range(len(top_scores), 6):
            score_labels[i].clear_widgets()

class GameScreen(Screen):
    pass

class GameOverScreen(Screen):
    pass

class InterfaceApp(App):
    def build(self):
        Builder.load_file('open.kv')
        Builder.load_file('menu.kv')
        Builder.load_file('help.kv')
        Builder.load_file('save.kv')
        Builder.load_file('hall.kv')
        Builder.load_file('game_over.kv')
        Builder.load_file('tutorial1.kv')
        Builder.load_file('tutorial2.kv')
        Builder.load_file('tutorial3.kv')
        Builder.load_file('tutorial4.kv')
        Builder.load_file('tutorial5.kv')
        Builder.load_file('tutorial6.kv')
        Builder.load_file('tutorial7.kv')
        Builder.load_file('gamecommands.kv')
        self.sm = ScreenManager()
        self.sm.add_widget(OpenScreen(name='open'))
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(HelpScreen(name='help'))
        self.sm.add_widget(SaveScreen(name='save'))
        self.sm.add_widget(HallWindow(name='hall'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(GameOverScreen(name='game_over'))
        self.sm.add_widget(Tutorial1Screen(name='tutorial1'))
        self.sm.add_widget(Tutorial2Screen(name='tutorial2'))
        self.sm.add_widget(Tutorial3Screen(name='tutorial3'))
        self.sm.add_widget(Tutorial4Screen(name='tutorial4'))
        self.sm.add_widget(Tutorial5Screen(name='tutorial5'))
        self.sm.add_widget(Tutorial6Screen(name='tutorial6'))
        self.sm.add_widget(Tutorial7Screen(name='tutorial7'))
        self.sm.add_widget(GamecommandsScreen(name='gamecommands'))
        Window.fullscreen = 'auto'
        Window.bind(on_key_down=self.on_key_down)
        return self.sm

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # 27 is the keycode for the escape key
            if self.sm.current != 'game':
                return True  # Block escape key outside the game screen
        return False

    def switch_to_menu(self):
        self.sm.current = 'menu'

    def switch_to_help(self):
        self.sm.current = 'help'

    def switch_to_save(self):
        self.sm.current = 'save'

    def switch_to_hall(self):
        self.sm.current = 'hall'

    def switch_to_tutorial1(self):
        self.sm.current = 'tutorial1'

    def switch_to_tutorial2(self):
        self.sm.current = 'tutorial2'

    def switch_to_tutorial3(self):
        self.sm.current = 'tutorial3'

    def switch_to_tutorial4(self):
        self.sm.current = 'tutorial4'

    def switch_to_tutorial5(self):
        self.sm.current = 'tutorial5'
    
    def switch_to_tutorial6(self):
        self.sm.current = 'tutorial6'

    def switch_to_tutorial7(self):
        self.sm.current = 'tutorial7'

    def switch_to_gamecommands(self):
        self.sm.current = 'gamecommands'


    def start_new_game(self):
        self.sm.current = 'game'
        game_screen = self.sm.get_screen('game')
        game_screen.clear_widgets()
        game = CannonGame()
        game_screen.add_widget(game)
        fps = 1 / game.fps if game.fps != 0 else 0
        Clock.schedule_interval(game.update, fps)

    def load_game(self):
        try:
            with open('current_level_stats.json', 'r') as file:
                game_stats = json.load(file)
        except FileNotFoundError:
            print("Save file not found.")
            return
        
        self.sm.current = 'game'
        game_screen = self.sm.get_screen('game')
        game_screen.clear_widgets()
        game = CannonGame()
        game.load_game(game_stats)
        game_screen.add_widget(game)
        fps = 1 / game.fps if game.fps != 0 else 0
        Clock.schedule_interval(game.update, fps)

    def close_app(self):
        self.stop()

if __name__ == '__main__':
    sample_app = InterfaceApp()
    sample_app.run()