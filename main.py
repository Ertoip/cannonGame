from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Rotate, InstructionGroup, Line, Ellipse
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.window import Keyboard
import math

class Ground(Widget):
    pass

class GroundGroup(Widget):
    pass    
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
            self.cannon_length = self.rect.size[1] * 0.3  # Adjust the length of the cannon as needed
            self.cannon_width = self.rect.size[0] * 0.03  # Adjust the width of the cannon as needed
            self.cannon = Line(points=(self.center_x, self.center_y, 
                                        self.center_x + self.cannon_length, self.center_y + self.cannon_width), width=self.cannon_width)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        

    def set_cannon_angle(self, mouse_pos):
        """Set the angle of the cannon based on the mouse position."""
        dx = mouse_pos[0] - self.center_x
        dy = mouse_pos[1] - self.center_y
        self.cannon_angle = math.atan2(dy, dx)        
        
        if self.cannon_angle < 0 and self.cannon_angle > -math.pi/2:
            self.cannon_angle = 0
        elif self.cannon_angle < 0:
            self.cannon_angle = math.pi
        
        self.cannon.points = (self.center_x, self.center_y, 
                            self.center_x + self.cannon_length * math.cos(self.cannon_angle),
                            self.center_y + self.cannon_length * math.sin(self.cannon_angle))
        
    def shoot(self, BulletGroup):
        bullet = Bullet()
        
        bullet.angle = self.cannon_angle
        bullet.pos = [self.center_x + self.cannon_length * math.cos(self.cannon_angle), self.center_y + self.cannon_length * math.sin(self.cannon_angle)]
        bullet.color = (0.5, 0.5, 0.5, 1)  # Green color
        bullet.size_hint = (None, None)
        bullet.size = (20)
        
        BulletGroup.add_widget(bullet)

        print("shoot")
        
#------------------------------------------------------------------------- bullets -------------------------------------------------------------------------#
class BulletGroup(Widget):
    pass

class Bullet(Widget):
    mass = NumericProperty(10)
    effect_radius = NumericProperty(10)
    speed = NumericProperty(6)
    flighttime = NumericProperty(0)
    angle = NumericProperty(0)
    size = NumericProperty(20)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            # Draw the bullet (circle)
            Color(0.4, 0.4, 0.4)
            self.bullet = Ellipse(pos=self.pos, size=(self.size, self.size))

        self.bind(pos=self.update_bullet_position)

    def update_bullet_position(self, *args):
        # Update the position of the bullet when the widget's position changes
        self.bullet.pos = self.pos
        
    def trajectory(self):
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y += self.speed * math.cos(math.radians(self.angle)) - self.mass * self.flighttime
        self.flighttime += 0.5


#-------------------------------------------------------------------------class game-------------------------------------------------------------------------#
class CannonGame(Widget):
    tank = ObjectProperty(None)
    tank_speed = NumericProperty(10)  # Speed of the tank
    gravity = NumericProperty(10)
    fps = NumericProperty(60)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_group = InstructionGroup()  # InstructionGroup for background graphics
        self.canvas.before.add(self.bg_group)  # Add the background graphics to canvas.before
        
        self.heights = [5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,6,7,6,8,9,5,5,5,5,5,5,5,5,5,6,6,6,6,8,8,8,8,8,8,8,8,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7, 9,10,11,12,]
        self.grid_size_x = len(self.heights)  # Define the size of the grid
        self.grid_size_y = 50  # Define the size of the grid
        
        self.initial_window_width = self.width
        self.initial_window_height = self.height #helpful for keeping the original speed

        self.draw_background()  # Draw the background
        self.terrain_gen()  # Draw the grid
        self.create_tank()  # Create the tank
        
        bulletgroup = BulletGroup()
        self.add_widget(bulletgroup)#add the bullet group to group all the bulllets
        
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
        

#-------------------------------------------------------------------------map generation-------------------------------------------------------------------------#
    def draw_background(self):
        # Draw the background
        with self.canvas:
            Color(0.529, 0.808, 0.922, 1)  # RGBA values (blue)
            self.bg = Rectangle(size=self.size, pos=self.pos)
            self.bg_group.add(Color(0, 0, 1, 1))  # Add color to the InstructionGroup
            self.bg_group.add(self.bg)  # Add the Rectangle to the InstructionGroup
            

    def terrain_gen(self):
        # Generate terrain
        cell_size = min(self.width / self.grid_size_x, self.height / self.grid_size_y)
        
        x_offset = (self.width - self.grid_size_x * cell_size) / 2
        y_offset = (self.height - self.grid_size_y * cell_size) / 2

        x = 0
        ground_group = GroundGroup()  # Create a group for ground objects
        while x < len(self.heights):
            for y in range(self.heights[x]):
                ground = Ground()
                ground_color = Color(0.6, 0.3, 0) if y+1 != self.heights[x] else Color(0.2, 1, 0.2) # set color
                ground.canvas.add(ground_color)
                ground_pos_y = (y * cell_size) + y_offset
                ground_rectangle = Rectangle(pos=((x * cell_size)+x_offset, ground_pos_y), size=(cell_size, cell_size))
                ground.canvas.add(ground_rectangle)
                ground.size_hint = (None, None)
                ground.size = (cell_size, cell_size)
                ground.pos=((x * cell_size)+x_offset, ground_pos_y)
                ground_group.add_widget(ground)  # Add ground to the group
            x += 1
        self.add_widget(ground_group)  # Add the ground group to the game widget
        
    def create_tank(self, pos = (0, 200)):
        cell_size = min(self.width / self.grid_size_x, self.height / self.grid_size_y)
        self.tank = Tank()
        self.tank.color = (0, 1, 0, 1)  # Green color
        self.tank.size_hint = (None, None)
        self.tank.pos = (50, 500)  # Center tank horizontally
        self.tank.size = (cell_size*2, cell_size*2)
        self.add_widget(self.tank)  # Add tank widget to the game
        
        
#-------------------------------------------------------------------------system functions-------------------------------------------------------------------------#
    def on_size(self, *args):
        # Redraw grid and background when the size of the widget changes
        self.bg_group.clear()  # Clear the background graphics
        self.canvas.clear()
        self.draw_background()  # Redraw the background
        self.terrain_gen()  # Redraw the grid
        self.create_tank()  # Create the tank


    def update(self, dt):
        # Calculate normalization factors based on the initial window size
        normalization_factor_distance = self.width / self.initial_window_width  # for movement distance
        normalization_factor_gravity = self.height / self.initial_window_height  # for gravity force

        # Calculate movement distance based on normalized speed
        movement_distance = self.tank_speed * normalization_factor_distance * dt
        ground_group = self.children[1]  # Assuming the ground group is the first child widget
        bullet_group = self.children[2] # Assuming the bullet group is the second
        
        falling = True #wheater the tank can fall or move
        right = False
        left = False
        gravity_force = self.gravity * dt * normalization_factor_gravity
        
        #check collisions between tank and ground
        for ground in ground_group.children:
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, gravity=gravity_force)
            if touching:
                falling = False
                if self.tank.y > rect2[3]:
                    self.tank.y = rect2[3]
            
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = movement_distance)
            if ("right" in self.keys_pressed or "d" in self.keys_pressed) and self.tank.x + self.tank.width + movement_distance < self.width and not touching:
                right = True
            elif touching:    
                self.tank.right = rect2[0] - 3

                
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = -movement_distance)
            if ("left" in self.keys_pressed or "a" in self.keys_pressed) and self.tank.x - movement_distance > 0 and not touching:
                left = True
            elif touching:
                self.tank.x = rect2[2]+3 #the 1 one is to avoid intersection with the origin of the tank
                
        if falling:
            self.tank.y -= gravity_force

        # Move tank horizontally
        if right:
            self.tank.x += movement_distance

        if left:
            self.tank.x -= movement_distance

        self.tank.set_cannon_angle(self.mouse)#move the cannon
        
        for bullet in bullet_group.children:
            bullet.trajectory() #move all the bullets
            
        self.tank.shoot(bullet_group)

        
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

#-------------------------------------------------------------------------keyboard control functions-------------------------------------------------------------------------#    
    def keyboard_closed(self):
        self.keyboard.unbind(on_key_down=self.on_key_down)
        self.keyboard.unbind(on_key_up=self.on_key_up)
        self.keyboard = None

    def on_key_down(self, keyboard, keycode, text, modifiers):
        self.keys_pressed.add(keycode[1])

    def on_key_up(self, keyboard, keycode):
        self.keys_pressed.remove(keycode[1])

    def on_mouse_move(self, window, pos):
        self.mouse = Vector(pos)  # Update mouse position vector
        
class CannonApp(App):
    def build(self):
        game = CannonGame()
        Clock.schedule_interval(game.update, 1 / game.fps)
        return game


if __name__ == '__main__':
    CannonApp().run()