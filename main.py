from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Rotate, InstructionGroup, Line, Ellipse
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.window import Keyboard
import math
import random


class Ground(Widget):
    reflective = BooleanProperty(False)
    bulletproof = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            Color(0.6, 0.3, 0)        
    

#-------------------------------------------------------------------------tank-------------------------------------------------------------------------#

class Tank(Widget):
    cannon_angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            # Draw the tank body (rectangle)
            Color(0.9, 0.9, 0.9)
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

        bullet = Bullet()
        
        bullet.angle = self.cannon_angle
        bullet.pos = [self.center_x + self.cannon_length * math.cos(self.cannon_angle), self.center_y + self.cannon_length * math.sin(self.cannon_angle)]
        bullet.color = (0.5, 0.5, 0.5, 1)
        
        bullet.effect_diameter = weapon.get("effect_diameter", None)
        bullet.mass = weapon.get("mass", None)*game.cell_size
        bullet.speed = weapon.get("speed", None)*game.cell_size
        bullet.diameter = weapon.get("diameter", None)*game.cell_size
        bullet.drill = weapon.get("drill", None)
        bullet.speed_falloff = weapon.get("speed_falloff", None)*game.cell_size
        bullet.repeat_explosions = weapon.get("repeat_explosions", None)
        bullet.laser = weapon.get("laser", None)
        
        game.bullet_group.add(bullet)
        game.add_widget(bullet)
        
        
#------------------------------------------------------------------------- bullets -------------------------------------------------------------------------#

class Bullet(Widget):
    mass = NumericProperty(1)
    effect_diameter = NumericProperty(300)
    speed = NumericProperty(2)
    flighttime = NumericProperty(0)
    angle = NumericProperty(0)
    diameter = NumericProperty(5)
    drill = NumericProperty(0)
    speed_falloff = NumericProperty(0.00)
    repeat_explosions = BooleanProperty(False)
    laser = BooleanProperty(False)
    rays = ListProperty([])
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            # Draw the bullet (circle)
            Color(0.4, 0.4, 0.4)
            self.bullet = Ellipse(pos=self.pos, size=(self.diameter, self.diameter))

        self.bind(pos=self.update_bullet_position)

    def update_bullet_position(self, *args):
        # Update the position of the bullet when the widget's position changes
        self.bullet.pos = self.pos
        
    def trajectory(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle) - self.mass * self.flighttime
        self.flighttime += 0.1
            
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
    diameter = NumericProperty(0)#this is the actual diameter of the explosion
    radius_steps = NumericProperty(0)
    explosion_speed = NumericProperty(7)
    
    def __init__(self, effect_diameter, **kwargs):
        super().__init__(**kwargs)
        self.effect_diameter = effect_diameter 
        self.radius_steps = self.effect_diameter/self.explosion_speed
        with self.canvas:
            Color(1, 0, 0)
            self.fire = Ellipse(pos=(self.x - self.diameter/2, self.y - self.diameter/2), size=(self.diameter, self.diameter))

    def increase_explosion_radius(self):
        self.diameter += self.radius_steps
        self.fire.pos = (self.x - self.diameter/2, self.y - self.diameter/2)
        self.fire.size = (self.diameter, self.diameter)
        self.size = (self.diameter, self.diameter)
        
#-------------------------------------------------------------------------class game-------------------------------------------------------------------------#
class CannonGame(Widget):
    tank = ObjectProperty(None)
    tank_speed = NumericProperty(20)  # Speed of the tank
    gravity = NumericProperty(30)
    fps = NumericProperty(60)
    keys_up = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.grid_size_x = 100  # Define the size of the grid
        self.grid_size_y = self.grid_size_x/4 # Define the size of the grid
        
        # Define the parameters for scaling
        amplitude = 3  # Half of the peak-to-peak height (from -1 to 1)
        frequency = 5
        offset = amplitude*3
        # Calculate the heights using a sine function
        self.heights = []
        for x in range(self.grid_size_x):
            # Scale the sine function to fit within [0, 10]
            y = math.sin((x * (2 * math.pi / self.grid_size_x))*frequency) * amplitude + offset


            self.heights.append(round(y))  # Round the result to the nearest integer
        
        self.cell_size = self.width / self.grid_size_x

        
        self.initial_window_width = self.width
        self.initial_window_height = self.height #helpful for keeping the original speed

        self.ground_tiles = set()
        self.bullet_group = set()
        self.explosion_group = set()
        
        self.draw_background() # Draw the background
        self.terrain_gen()  # Draw the grid
        self.create_tank()  # Create the tank
        
        Window.minimum_width = 800
        Window.minimum_height = 600
        Window.maximum_width = 800
        Window.maximum_height = 600

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
            "mass": 0.2,
            "effect_diameter": 10,
            "speed": 1,
            "diameter": 1,
            "drill": 0,
            "speed_falloff": 0,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Bombshell",
            "mass": 1,
            "effect_diameter": 10,
            "speed": 0.8,
            "diameter": 1,
            "drill": 10,
            "speed_falloff": 0.05,
            "repeat_explosions": False,
            "laser": False,
        },
        {
            "name": "Laser",
            "mass": 0,
            "effect_diameter": 3,
            "speed": 1,
            "diameter": 0.1,
            "drill": 1000,
            "speed_falloff": 0.0,
            "repeat_explosions": True,
            "laser": True,
        }]
        
        self.current_weapon = 0

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
        # Create a group for ground objects
        while x < len(self.heights):
            for y in range(self.heights[x]):
                ground = Ground()
                ground_color = Color(0.6, 0.3, 0) if y+3 < self.heights[x] else Color(0.2, 1, 0.2) # set color
                ground.canvas.add(ground_color)
                ground_pos_y = (y * self.cell_size) + y_offset
                ground_rectangle = Rectangle(pos=((x * self.cell_size)+x_offset, ground_pos_y), size=(self.cell_size, self.cell_size))
                ground.canvas.add(ground_rectangle)
                ground.size_hint = (None, None)
                ground.size = (self.cell_size, self.cell_size)
                ground.pos=((x * self.cell_size)+x_offset, ground_pos_y)
                self.ground_tiles.add(ground)  # Add ground to the group
                self.add_widget(ground)
                
            if x == len(self.heights)-13 or x == len(self.heights)-12:
                for i in range(30):
                    ground = Ground()
                    
                    ground_color = Color(0.4, 0.4, 0.7)
                    ground.canvas.add(ground_color)
                    ground_pos_y = (i * self.cell_size) + (y * self.cell_size) + self.cell_size*3
                    ground_rectangle = Rectangle(pos=((x * self.cell_size)+x_offset, ground_pos_y), size=(self.cell_size, self.cell_size))
                    ground.canvas.add(ground_rectangle)
                    
                    ground.size_hint = (None, None)
                    ground.size = (self.cell_size, self.cell_size)
                    ground.pos=ground_rectangle.pos
                    ground.reflective = True
                    self.ground_tiles.add(ground)  # Add ground to the group
                    self.add_widget(ground)

            x += 1
        
    def create_tank(self):
        self.tank = Tank()
        self.tank.color = (0, 1, 0, 1)  # Green color
        self.tank.size_hint = (None, None)
        self.tank.pos = (1, self.heights[0]*(self.cell_size+2)+(self.height - self.grid_size_y * self.cell_size) / 2)  # Center tank horizontally
        self.tank.size = (self.cell_size*2, self.cell_size*2)
        
        self.add_widget(self.tank)  # Add tank widget to the game
        
        
#-------------------------------------------------------------------------system functions-------------------------------------------------------------------------#
    def on_size(self, *args):
        # Redraw grid and background when the size of the widget changes
        self.canvas.clear()
        self.ground_tiles.clear()
        self.bullet_group.clear()
        self.cell_size = self.width / self.grid_size_x
        self.draw_background()  # Redraw the background
        self.terrain_gen()  # Redraw the grid
        self.create_tank()  # Create the tank


    def update(self, dt):
        # Calculate movement distance based on normalized speed
        movement_distance = self.tank_speed*self.cell_size*dt # Adjust speed based on screen size

        bullets_to_remove = []
        explosions_to_remove = []
        ground_to_remove = []

        falling = True #wheater the tank can fall or move
        right = False
        left = False
        gravity_force = self.gravity*self.cell_size*dt
        
        for explosion in self.explosion_group:
            if explosion.diameter < explosion.effect_diameter:
                explosion.increase_explosion_radius()
            else:
                explosions_to_remove.append(explosion)
            
        range_x = (self.tank.x - self.cell_size * 2, self.tank.x + self.cell_size * 2)#we use theese to improve performance by checking collision of only neraby objects
        range_y = (self.tank.y - self.cell_size * 2, self.tank.y + self.cell_size * 2)
        
        #tank collisions
        for ground in self.ground_tiles:
            if range_x[0] <= ground.x <= range_x[1] and range_y[0] <= ground.y <= range_y[1]:                
                touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, gravity=gravity_force)
                if touching:
                    falling = False
                    if self.tank.y > rect2[3]:
                        self.tank.y = rect2[3]

                
                touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = movement_distance)
                if (("right" in self.keys_pressed or "d" in self.keys_pressed) 
                    and self.tank.x + self.tank.width + movement_distance < self.width 
                    and not touching):
                    right = True
                elif touching and not self.is_widget_at_coordinate(group=self.ground_tiles, x=rect2[0]+3,y=rect2[1]+self.cell_size+3 ):#this allows to climb to the right
                    self.tank.y = rect2[1]+self.cell_size+1
                elif touching:    
                    self.tank.right = rect2[0] - 3

                    
                touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = -movement_distance)
                if ("left" in self.keys_pressed or "a" in self.keys_pressed) and self.tank.x - movement_distance > 0 and not touching:
                    left = True
                elif touching and not self.is_widget_at_coordinate(group=self.ground_tiles, x=rect2[0]+3,y=rect2[1]+self.cell_size+1 ): #this allows to climb to the left
                    self.tank.y = rect2[1]+self.cell_size+1
                elif touching:
                    self.tank.x = rect2[2]+3 #the 1 one is to avoid intersection with the origin of the tank
            
            else:
                if ("right" in self.keys_pressed or "d" in self.keys_pressed) and self.tank.x + self.tank.width + movement_distance < self.width:
                    right = True
                
                elif ("left" in self.keys_pressed or "a" in self.keys_pressed) and self.tank.x - movement_distance > 0:
                    left = True
                        
            for explosion in explosions_to_remove:
                touching, rect2 = self.check_collision_circle(circle=explosion, rect=ground) 
                if touching:
                    ground_to_remove.append(ground)
                    
        #bullet collisions
        for bullet in self.bullet_group:
            bullet_range_x = (bullet.x - self.cell_size, bullet.x + self.cell_size)#we use theese to improve performance by checking collision of only neraby objects
            bullet_range_y = (bullet.y - self.cell_size, bullet.y + self.cell_size)

            for ground in self.ground_tiles:
                if (bullet_range_x[0] <= ground.x <= bullet_range_x[1]) and (bullet_range_y[0] <= ground.y <= bullet_range_y[1]):
                    touching, g = self.check_collision_bullet(bullet=bullet, rect=ground)
                    if touching and bullet.laser and ground.reflective:
                        
                        prev_x = bullet.x - bullet.speed * math.cos(bullet.angle)
                        prev_y = bullet.y - (bullet.speed * math.sin(bullet.angle) - bullet.mass * (bullet.flighttime-0.1))
                        
                        top_side = ((g[0], g[3]), (g[2], g[3]))
                        bottom_side = ((g[0], g[1]), (g[2], g[1]))
                        left_side = ((g[0], g[1]), (g[0], g[3]))
                        right_side = ((g[2], g[1]), (g[2], g[3]))
                        
                        normal_vector = [0, 1]
                        
                        if self.intersect((prev_x, prev_y), (bullet.x, bullet.y), *top_side):
                            # Collision with the top side
                            normal_vector = [0, 1]  # Normal vector pointing upwards
                            bullet.pos = (ground.x+ground.width/2, ground.y+ground.width+10)
                            print("top side collision")                            
                        
                        elif self.intersect((prev_x, prev_y), (bullet.x, bullet.y), *bottom_side):
                            # Collision with the bottom side
                            normal_vector = [0, -1]  # Normal vector pointing downwards
                            bullet.pos = (ground.x+ground.width/2, ground.y-10)                            
                            print("bottom side collision")                            
                            
                        elif self.intersect((prev_x, prev_y), (bullet.x, bullet.y), *right_side):
                            # Collision with the right side
                            normal_vector = [1, 0]  # Normal vector pointing to the right
                            bullet.pos = (ground.x+ground.width+10, ground.y+ground.width/2)
                            print("right side collision")                            
                            
                        elif self.intersect((prev_x, prev_y), (bullet.x, bullet.y), *left_side):
                            # Collision with the left side
                            normal_vector = [-1, 0]  # Normal vector pointing to the left   
                            bullet.pos = (ground.x-10, ground.y+ground.width/2)
                            print("left side collision")                            
                            
                        bullet.recalculate_angle(normal_vector)
                        
                    elif touching and bullet.drill <= 0:
                        bullets_to_remove.append(bullet)
                        break  # No need to check further collisions for this bullet if it has already collided  
                        
                    elif touching and bullet.drill > 0:
                        bullet.drill -= 1
                        if bullet.speed > 0:
                            bullet.speed -= bullet.speed_falloff
                            if bullet.repeat_explosions:
                                bullet.explode(self) # remove bullet
                        break  # No need to check further collisions for this bullet if it has already collided                        
        
        if "tab" in self.keys_up:
            if self.current_weapon >= len(self.weapons)-1:
                self.current_weapon = 0
            else:
                self.current_weapon += 1
            print(self.weapons[self.current_weapon]["name"])
            
        
        if falling:
            self.tank.y -= gravity_force
            if self.tank.x < 0:
                self.tank.x = 0
            if self.tank.y < 0:
                self.tank.y = Window.height

        # Move tank horizontally
        if right:
            self.tank.x += movement_distance

        if left:
            self.tank.x -= movement_distance

        self.tank.set_cannon_angle(self.mouse)#move the cannon
        

        for bullet in self.bullet_group:
            prev_coordinates = [bullet.x+bullet.diameter/2, bullet.y+bullet.diameter/2]
            bullet.trajectory()  # move all the bullets

            if bullet.laser:
                # Calculate new coordinates after moving the bullet
                new_coordinates = [bullet.x+bullet.diameter/2 , bullet.y+bullet.diameter/2]
                
                # Draw a line from previous coordinates to new coordinates
                with self.canvas:
                    Color(1,0,0)
                    laser_ray = Line(points=prev_coordinates + new_coordinates, width=bullet.diameter)
                    bullet.rays.append(laser_ray)
                    if len(bullet.rays) > 3:
                        self.canvas.remove(bullet.rays[0])
                        bullet.rays.pop(0)

                
            if (bullet.y < 0 or bullet.x < 0 or bullet.x > Window.width) and bullet not in bullets_to_remove:
                bullets_to_remove.append(bullet)
            

        for bullet in bullets_to_remove:
            if bullet in self.bullet_group:
                if bullet.laser:
                    for r in bullet.rays:
                        self.canvas.remove(r)
                        
                        
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
                
        self.keys_up = []
                
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
        if (distance <= (circle.diameter+rect.width)/2):
            return True, [rect.x, rect.y, rect.x + rect.width, rect.y + rect.height]
        
        return False, []
    
    #basically the same as check_collision_circle
    def check_collision_bullet(self, bullet, rect):
        # Calculate center coordinates of the rectangle
        rect_center_x = (rect.x + rect.width / 2)
        rect_center_y = (rect.y + rect.height / 2)
        
        bullet_center_x = bullet.x
        bullet_center_y = bullet.y
        # Calculate the distance between the centers of the circle and rectangle
        distance = math.hypot(bullet_center_x - rect_center_x, bullet_center_y - rect_center_y)

        # Check if the distance between the centers is less than or equal to the maximum allowed distance
        # and if all corners of the rectangle are within the circle
        if (distance <= (bullet.diameter+rect.width)/2):
            return True, [rect.x, rect.y, rect.x + rect.width, rect.y + rect.height]
        
        return False, []

    
    def is_widget_at_coordinate(self, group, x, y):
        """
        Check if there is a widget at the specified coordinate (x, y).
        
        Args:
            widget: The parent widget to search within.
            x: The x-coordinate.
            y: The y-coordinate.
            
        Returns:
            True if a widget is found at the coordinate, False otherwise.
        """
        for child in group:
            if isinstance(child, Widget):
                if child.collide_point(x, y):
                    return True
        return False
    
    def ccw(self, A, B, C):
        """Check if three points are in counter-clockwise order."""
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    def intersect(self, A, B, C, D):
        """Check if two line segments AB and CD intersect."""
        return self.ccw(A, C, D) != self.ccw(B, C, D) and self.ccw(A, B, C) != self.ccw(A, B, D)
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