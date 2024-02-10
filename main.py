from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, InstructionGroup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.window import Keyboard


class Ground(Widget):
    pass

class GroundGroup(Widget):
    pass    
#-------------------------------------------------------------------------map generation-------------------------------------------------------------------------#

class Tank(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.9, 0.9, 0.9)  # Green color
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


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
        
        Window.minimum_width = 800
        Window.minimum_height = 600
        Window.maximum_width = 800
        Window.maximum_height = 600

        self.keyboard = Window.request_keyboard(self.keyboard_closed, self)
        self.keyboard.bind(on_key_down=self.on_key_down)
        self.keyboard.bind(on_key_up=self.on_key_up)
        self.keys_pressed = set()

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
        self.tank.size = (cell_size, cell_size)
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
        falling = True #wheater the tank can fall or move
        right = False
        left = False
        gravity_force = self.gravity * dt * normalization_factor_gravity
        
        for ground in ground_group.children:
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, gravity=gravity_force)
            if touching:
                falling = False
                if self.tank.y > rect2[3]:
                    print("skipped from " + str(self.tank.y) + "to " + str(rect2[3]))
                    self.tank.y = rect2[3]
            
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = movement_distance)
            if "right" in self.keys_pressed and self.tank.x + self.tank.width + movement_distance < self.width and not touching:
                right = True
            elif touching:    
                self.tank.right = rect2[0]

                
            touching, rect2 = self.check_collision(rect1=self.tank, rect2=ground, speed = -movement_distance)
            if "left" in self.keys_pressed and self.tank.x - movement_distance > 0 and not touching:
                left = True
            elif touching:
                self.tank.x = rect2[2]+1 #the 1 one is to avoid intersection with the origin of the tank
                
        if falling:
            self.tank.y -= gravity_force

        # Move tank horizontally
        if right:
            self.tank.x += movement_distance

        if left:
            self.tank.x -= movement_distance

            
        
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


class CannonApp(App):
    def build(self):
        game = CannonGame()
        Clock.schedule_interval(game.update, 1 / game.fps)
        return game


if __name__ == '__main__':
    CannonApp().run()