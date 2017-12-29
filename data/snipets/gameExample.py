# s!/usr/bin/python
# import pygame and everything else
try:
    import sys
    import random
    import math
    import os
    import getopt
    import pygame
    import pickle
    import copy
    from collections import *
    from functools import cmp_to_key
    # from socket import *
    from pygame.locals import *
    from vector import *
    import yaml
    import pygame.mixer

except ImportError as err:
    print("couldn't load module. %s" % (err))
    sys.exit(2)

# level handling
# Load image function
def load_png(name):
    """ Load image and return image object"""
    fullname = os.path.join('data/images', name)
    try:
        image = pygame.image.load_basic(fullname)
        if image.get_alpha() is None:
            image = image.convert()
        else:
            image = image.convert_alpha()
    except pygame.error as message:
        print('Cannot load image:', fullname)
        raise SystemExit(message)
    return image


# load sound function
def load_sound(name):
    class NoneSound:
        def play(self): pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join('data/sounds', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error as err:
        print('Cannot load sound: %s' % fullname)
        raise SystemExit(err)
    return sound


# load tile set function
def load_tile_table(filename, width, height):
    image = pygame.image.load_basic(os.path.join('data/images', filename))
    image_width, image_height = image.get_size()
    tile_table = []
    for tile_x in range(0, image_width / width):
        line = []
        tile_table.append(line)
        for tile_y in range(0, image_height / height):
            rect = (tile_x * width, tile_y * height, width, height)
            line.append(image.subsurface(rect))
    return tile_table


# count files in directiory
def count_files(in_directory):
    joiner = (in_directory + os.path.sep).__add__
    return sum(
        os.path.isfile(filename)
        for filename
        in map(joiner, os.listdir(in_directory))
    )


# calculate depth of collision
def GetIntersectionDepth(rect_A, rect_B):
    # Calculate half sizes.
    halfWidthA = rect_A.width / 2
    halfHeightA = rect_A.height / 2
    halfWidthB = rect_B.width / 2
    halfHeightB = rect_B.height / 2

    # calculate centers
    center_A = AVector(rect_A.left + halfWidthA, rect_A.top + halfHeightA)
    center_B = AVector(rect_A.left + halfWidthA, rect_A.top + halfHeightA)

    # Calculate current and minimum-non-intersecting distances between centers.
    distance_x = center_A.x - center_B.x
    distance_y = center_A.y - center_B.y
    minDistance_x = halfWidthA + halfWidthB
    minDistance_y = halfHeightA + halfHeightB

    # If we are not intersecting at all, return (0, 0).
    if distance_x >= minDistance_x and distance_y >= minDistance_y:
        return AVector(0,0)

    # Calculate and return intersection depths
    if distance_x > 0:
        depth_x = minDistance_x - distance_x
    else:
        depth_x = -minDistance_x - distance_x

    if distance_x > 0:
        depth_y = minDistance_y - distance_y
    else:
        depth_y = -minDistance_y - distance_y

    return AVector(depth_x, depth_y)


def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse

    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1, x2 = rect.left, rect.right
    y1, y2 = rect.top, rect.bottom
    if vertical:
        h = y2 - y1
    else:
        h = x2 - x1
    if forward:
        a, b = color, gradient
    else:
        b, a = color, gradient
    rate = (
        float(b[0] - a[0]) / h,
        float(b[1] - a[1]) / h,
        float(b[2] - a[2]) / h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1, y2):
            color = (
                min(max(a[0] + (rate[0] * (line - y1)), 0), 255),
                min(max(a[1] + (rate[1] * (line - y1)), 0), 255),
                min(max(a[2] + (rate[2] * (line - y1)), 0), 255)
            )
            fn_line(surface, color, (x1, line), (x2, line))
    else:
        for col in range(x1, x2):
            color = (
                min(max(a[0] + (rate[0] * (col - x1)), 0), 255),
                min(max(a[1] + (rate[1] * (col - x1)), 0), 255),
                min(max(a[2] + (rate[2] * (col - x1)), 0), 255)
            )
            fn_line(surface, color, (col, y1), (col, y2))


# game class
class Game(object):
    def __init__(self):
        pygame.mixer.init()

        self.clock = pygame.time.Clock()

        self.game_state = "menu_main"

        # initialize Keyboard() class
        self.keyboard = Keyboard()

        self.list_update_always = [self.keyboard]
        self.list_update = []
        self.list_draw = []

        # The number of times our engine should update per second.
        self.preferred_fps = 60

        # Used to print the fps of the game onto the console window.
        self.fpsTimer = 0.0

        # Should Ragnarok print the number of frames the game is running at?
        self.print_frames = False

        # The number of milliseconds between printing out the frame rate
        self.print_fps_frequency = 1000

        # self.level_1 = Level("data/maps/level_1.map")
        self.level_menu_main = Level_menu_main()

    def get_keyboard(self):
        return self.keyboard

    def go(self):
        running = True
        while running:
            # print frame
            # This is the main game loop
            # Update our clock
            self.clock.tick(self.preferred_fps)
            elapsed_milliseconds = self.clock.get_time()

            # Print the fps that the game is running at.
            if self.print_frames:
                self.fpsTimer += elapsed_milliseconds
                if self.fpsTimer > self.print_fps_frequency:
                    print("FPS: ", self.clock.get_fps())
                    self.fpsTimer = 0.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            function = getattr(self, self.game_state)
            function()

            # drawing and updating
            for obj in self.list_update_always:
                obj.update(17)  # put elapsed_milliseconds instead of 17 if you want it to be affected by time
            for obj in self.list_update:
                obj.update(17)  # put elapsed_milliseconds instead of 17 if you want it to be affected by time

            # screen.fill((230, 255, 255))

            for obj in self.list_draw:
                obj.draw(17, screen)  # put elapsed_milliseconds instead of 17 if you want it to be affected by time

            ### debug ###
            #
            # pygame.draw.line(screen, (0,0,0), (0,windowHeight/2), (windowWidth,windowHeight/2), 1)
            # pygame.draw.line(screen, (0,0,0), (windowWidth/2,0), (windowWidth/2,windowHeight), 1)
            #
            #############

            pygame.display.flip()
        pygame.quit()

    def menu_main(self):
        self.list_update = [self.level_menu_main]
        self.list_draw = [self.level_menu_main]

    def menu_info(self):
        self.list_update = []
        self.list_draw = []

    def game(self):
        # self.list_update = [self.debug_info, self.camera]
        # self.list_draw = [self.debug_info, self.camera]
        pass

    def menu_loadlevel(self):
        self.list_update = [self.menu_level_loader]
        self.list_draw = [self.menu_level_loader]

#######################################################################################################################
# out of main game classes


class AVector(Vector):
    """
    Adapter class for the old Vector to the new vector class
    """
    Zero = {'x':0, 'y':0}

    def __init__(self, x, y):
        self.x = x
        self.y = y
        super(Vector, self).__init__({'x': self.x, 'y': self.y})


class UpdatableObj(object):
    """
    The base class of our game engine.
    Represents an object that can be updated.
    """
    # The number of objects that have existed so far. Used to create a unique object id.
    __total_id = 0

    def __init__(self, level, update_order=0):
        self.level = level
        # The order in which this object should update relative to the other objects.
        self.update_order = update_order

        # Represents the unique identifer for this object.
        self.obj_id = self.__total_id

        # Keeps track of the total number of object created since game start.
        UpdatableObj.__total_id += 1

        # Is the object allowed to update druing the update loop?
        self.is_enabled = True

        # Does the object stay in one place even if the camera is moving?
        self.is_static = True

        # Represents the location of the object in world space.
        self.position = AVector(0, 0)

        # Allows the user to define the object as they want.
        self.tag = ""

        # allows to add commands
        self.commands = None

        # variables to be used by self.commands
        self.variable_1 = 0
        self.variable_2 = 0
        self.variable_3 = 0

    def __str__(self):
        return "{ \nUpdateableObj: \t Update Order: " + str(self.update_order) + "\t Object ID: " \
               + str(self.obj_id) + "\t Is Enabled: " + str(self.is_enabled) + "\n}"

    def update(self, milliseconds):
        # Update the object.
        if not self.commands == None:
            exec(self.commands)


class DrawableObj(UpdatableObj):
    """An object that represents something that can be drawn."""

    def __init__(self, level, update_order=0, draw_order=0):
        super(DrawableObj, self).__init__(level, update_order)
        self.draw_order = draw_order

        # Should the object draw during the update loop?
        self.is_visible = True

        # The surface rendered onto the screen when draw is called.
        self.image = pygame.Surface((0, 0))

        self.offset = AVector(0, 0)

        try:
            self.scale_factor
        except AttributeError:
            self.scale_factor = 1

    def show(self):
        """Enable and show the object."""
        self.is_enabled = True
        self.is_visible = True

    def hide(self):
        """Disable and hide the object."""
        self.is_enabled = False
        self.is_visible = False

    def is_visible_to_camera(self, camera):
        """Is the object visible to the camera?"""
        # if self.image.get_rect().colliderect(camera.rect):
        #   return True
        # ^ doesn't work, don't know why
        return True

    def draw(self, milliseconds, surface):
        # Draw the object
        if self.is_static:
            surface.blit(self.image, self.position + self.offset)
        else:
            relative_position = (self.position + self.offset) - self.level.camera.position
            # glich fix, the render makes weird jumps (only for some objects) between two pixels if you dont do this
            relative_position = AVector(relative_position.x, relative_position.y - 0.2)
            surface.blit(self.image, relative_position)


# keyboard and keystate class from ragnarok engine
class KeyState(object):
    def __init__(self):
        # Contains a reference to all pressed status of all the keys
        self.key_states = []

    def copy(self):
        new_keys = []
        for key in self.key_states:
            new_keys.append(key)
        state_cpy = KeyState()
        state_cpy.key_states = new_keys
        return state_cpy

    def query_state(self, key):
        """
        Query the state of a key. True if the key is down, false if it is up.
        key is a pygame key.
        """
        return self.key_states[key]


class Keyboard(UpdatableObj):
    def __init__(self):
        super(Keyboard, self).__init__(None)
        self.current_state = KeyState()
        self.previous_state = KeyState()
        self.current_state.key_states = pygame.key.get_pressed()

    def is_down(self, key):
        return self.current_state.query_state(key)

    def is_up(self, key):
        return not self.current_state.query_state(key)

    def is_clicked(self, key):
        return self.current_state.query_state(key) and (not self.previous_state.query_state(key))

    def is_released(self, key):
        return self.previous_state.query_state(key) and (not self.current_state.query_state(key))

    def is_any_down(self):
        """Is any button depressed?"""
        for key in range(len(self.current_state.key_states)):
            if self.is_down(key):
                return True
        return False

    def is_any_clicked(self):
        """Is any button clicked?"""
        for key in range(len(self.current_state.key_states)):
            if self.is_clicked(key):
                return True
        return False

    def update(self, milliseconds):
        keys = pygame.key.get_pressed()
        self.previous_state = self.current_state.copy()
        self.current_state.key_states = keys
        super(Keyboard, self).update(milliseconds)


class Camera(UpdatableObj):
    def __init__(self, level, position):
        super(Camera, self).__init__(level)

        self.offset = AVector(windowWidth / 2, windowHeight / 2)
        self.scale = AVector(windowWidth, windowHeight)
        self.position = position - self.offset + self.level.player.scale / 2
        self.rect = pygame.Rect(self.position, self.scale)
        self.velocity = AVector(0, 0)

        self.image = pygame.Surface((10, 10)).convert()
        self.image.fill((0, 0, 255))

    def update(self, milliseconds):
        # time = (milliseconds / 1000.0)
        # self.velocity.y = 0
        # self.velocity.x = 0
        # if main_game.keyboard.is_down(K_w):
        #    self.velocity.y = -200
        # if main_game.keyboard.is_down(K_s):
        #    self.velocity.y = 200
        # if main_game.keyboard.is_down(K_d):
        #    self.velocity.x = 200
        # if main_game.keyboard.is_down(K_a):
        #    self.velocity.x = -200
        # self.position += self.velocity * time
        camera_position = self.position + self.offset
        player_position = self.level.player.position + self.level.player.scale / 2
        distance = player_position - camera_position
        cam_x = 0  # 150 # allowed_distance_x_from_camera

        camera_position.y = player_position.y
        if distance.x > cam_x:
            camera_position.x = player_position.x - cam_x
        if distance.x < -cam_x:
            camera_position.x = player_position.x + cam_x

        self.position = camera_position - self.offset

        self.rect.topleft = self.position  # - self.offset


# blueprint
class Level(UpdatableObj):
    def __init__(self, level_file=None, player_position=None):
        super(Level, self).__init__(self)

        self.list_update = []
        self.list_draw = []

        # Do we need to sort our list of updatable objects?
        self.__do_need_sort_up = False

        # Do we need to sort our list of drawable objects?
        self.__do_need_sort_draw = False

        self.player_position = player_position

        if level_file:
            self.load_level(level_file)

    def load_level(self, level_file):
        self.load_level_file(level_file)
        self.parse_level_file()

    def find_obj_in_list(self, search_list, value, tag_or_id):
        if tag_or_id == "tag":
            for obj in search_list:
                if obj.tag == value:
                    return obj
        elif tag_or_id == "id":
            for obj in search_list:
                if obj.obj_id == value:
                    return obj
        else:
            print("error tag_or_id")

    def load_level_file(self, level_file):
        filename = "data/maps/" + level_file  # filename
        stream = open(filename, 'r')  # opening stream
        yaml_file = yaml.load(stream)  # loading stream
        # print yaml_file

        ########################################################
        # this is becaus YAML doesn't load dicts in the order it
        # was written and python only does it with OrderedDict()
        begin_dict = OrderedDict(yaml_file[0])
        for index, dictionary in enumerate(yaml_file):
            if not index == 0:
                begin_dict.update(dictionary)

        ########################################################
        self.level = begin_dict

    def parse_level_file(self):
        self.list_collision = []

        camera_position = AVector(0, 0)

        ###### temporary ############

        self.background = DrawableObj(self)
        surface = copy.copy(screen)
        fill_gradient(surface, (170, 255, 255), (255, 255, 255))
        self.background.image = surface
        self.list_draw.append(self.background)

        #############################
        self.scale_factor = 3.0  # best to use integer or 1/2 because of rounding faults of the program
        scale_factor = self.scale_factor

        for obj in self.level:

            obj_postion = AVector(0, 0)
            if "position" in self.level[obj]:
                obj_position = AVector(self.level[obj]["position"][0] * scale_factor,
                                      self.level[obj]["position"][1] * scale_factor)
            obj_offset = AVector(0, 0)
            if "offset" in self.level[obj]:
                obj_offset = AVector(self.level[obj]["offset"][0] * scale_factor,
                                    self.level[obj]["offset"][1] * scale_factor)
            obj_scale = AVector(0, 0)
            if "scale" in self.level[obj]:
                obj_scale = AVector(self.level[obj]["scale"][0] * scale_factor,
                                   self.level[obj]["scale"][1] * scale_factor)
                obj_scale_int = AVector(int(self.level[obj]["scale"][0] * scale_factor),
                                       int(self.level[obj]["scale"][1] * scale_factor))  # scale values in integers
            if "image" in self.level[obj]:
                if isinstance(self.level[obj]["image"], str):
                    obj_image = load_png(self.level[obj]["image"])
                elif isinstance(self.level[obj]["image"][1], list):
                    tile_scale_x = self.level[obj]["image"][1][0]
                    tile_scale_y = self.level[obj]["image"][1][1]
                    tileset = load_tile_table(self.level[obj]["image"][0], tile_scale_x, tile_scale_y)
                    tile_pos_x = self.level[obj]["image"][2][0]
                    tile_pos_y = self.level[obj]["image"][2][1]
                    obj_image = tileset[tile_pos_x][tile_pos_y]
            obj_commands = None
            if "commands" in self.level[obj]:
                obj_commands = self.level[obj]["commands"]

            if "randomclouds" in self.level[obj]:
                tileset_file = self.level[obj]["randomclouds"]
                self.create_clouds(tileset_file)

            if obj == "player":
                if self.player_position == None:
                    self.player_position = obj_position
                    camera_position = copy.copy(obj_position)
                    self.player = Player(self, obj_position)
                    self.list_update.append(self.player)
                    self.list_draw.append(self.player)
                else:
                    camera_position = copy.copy(self.player_position)
                    self.player = Player(self, copy.copy(self.player_position))
                    self.list_update.append(self.player)
                    self.list_draw.append(self.player)

            elif "cloud" in self.level[obj]:
                layer = self.level[obj]["cloud"]
                cloud_image = pygame.transform.scale(obj_image, obj_scale_int)
                cloud = Cloud(self, obj_position, obj_scale, cloud_image, layer)
                self.list_draw.append(cloud)

            elif "interactive" in self.level[obj]:
                if self.level[obj]["interactive"] == "npc":
                    npc_image_transformed = pygame.transform.scale(obj_image, obj_scale_int)
                    npc_dialog_file = self.level[obj]["dialog"]
                    npc = NPC(self, obj_position, obj_scale, npc_image_transformed, npc_dialog_file)

                    self.list_collision.append(npc)
                    self.list_draw.append(npc)

            elif "animation" in self.level[obj]:
                if self.level[obj]["animation"] == "loop":
                    image_sequence = self.level[obj]["image"]
                    tpf = self.level[obj]["tpf"]
                    ani_obj = AnimationLoopObj(self, obj_position, obj_scale, image_sequence, tpf)
                    ani_obj.commands = obj_commands
                    self.list_update.append(ani_obj)
                    self.list_draw.append(ani_obj)

                elif self.level[obj]["animation"] == "oncollision":
                    image_sequence = self.level[obj]["image"]
                    tpf = self.level[obj]["tpf"]
                    condition = self.level[obj]["condition"]
                    ani_obj = AnimationOnCollisionObj(self, obj_position, obj_scale, image_sequence, tpf, condition)
                    ani_obj.commands = obj_commands
                    self.list_collision.append(ani_obj)
                    self.list_update.append(ani_obj)
                    self.list_draw.append(ani_obj)

            elif "tile_solids" in self.level[obj]:
                thing = DrawableObj(self)
                thing.position = obj_position
                thing.image = pygame.transform.scale(obj_image, obj_scale_int)
                thing.is_static = False
                self.list_draw.append(thing)
                if "tile_solids" in self.level[obj]:
                    # tile_scale_without_scale_factor = Vector(self.level[obj]["tile_scale"][0], self.level[obj]["tile_scale"][1])
                    tile_scale = AVector(self.level[obj]["tile_scale"][0] * scale_factor,
                                        self.level[obj]["tile_scale"][1] * scale_factor)
                    solid_tiles = self.level[obj]["tile_solids"].split()
                    # print solid_tiles
                    for map_y, line in enumerate(solid_tiles):
                        for map_x, character in enumerate(line):
                            if character == "#":
                                tile_pos = AVector(map_x * tile_scale.x, map_y * tile_scale.y)
                                collision_obj = SolidObj(self, tile_pos, tile_scale)
                                self.list_collision.append(collision_obj)
                                # self.list_draw.append(collision_obj) # for debugging
                                # self.list_update.append(collision_obj) # for debugging
                            if character == "^":
                                tile_pos = AVector(map_x * tile_scale.x, map_y * tile_scale.y)
                                collision_obj = PlatformObj(self, tile_pos, tile_scale)
                                self.list_collision.append(collision_obj)
                                # self.list_draw.append(collision_obj) # for debugging
                                # self.list_update.append(collision_obj) # for debugging

            elif "solid" in self.level[obj]:
                try:
                    thing = SolidObj(self, obj_position, AVector(int(self.level[obj]["solid"][0] * scale_factor),
                                                                int(self.level[obj]["solid"][1] * scale_factor)))
                    thing.image = pygame.transform.scale(obj_image, obj_scale_int)
                    thing.commands = obj_commands
                    thing.offset = obj_offset
                    self.list_collision.append(thing)
                    if not obj_commands == None:
                        self.list_update.append(thing)
                    self.list_draw.append(thing)
                except TypeError:
                    thing = PlatformObj(self, obj_position, AVector(int(self.level[obj]["solid"] * scale_factor), 0))
                    thing.image = pygame.transform.scale(obj_image, obj_scale_int)
                    thing.commands = obj_commands
                    thing.offset = obj_offset
                    self.list_collision.append(thing)
                    if not obj_commands == None:
                        self.list_update.append(thing)
                    self.list_draw.append(thing)
            else:
                thing = DrawableObj(self)
                thing.position = obj_position
                thing.image = pygame.transform.scale(obj_image, obj_scale_int)
                thing.is_static = False
                thing.commands = obj_commands
                if not obj_commands == None:
                    self.list_update.append(thing)
                self.list_draw.append(thing)

        self.camera = Camera(self, camera_position)
        self.list_update.append(self.camera)

    def get_tile(self, x, y):
        try:
            char = self.map[y][x]
        except IndexError:
            return {}
        try:
            return self.key[char]
        except KeyError:
            return {}

    def get_bool(self, x, y, name):
        """Tell if the specified flag is set for position on the map."""

        value = self.get_tile(x, y).get(name)  # return value
        return value in (True, 1, 'true', 'yes', 'True', 'Yes', '1', 'on', 'On')

    def get_attribute(self, x, y, name):
        """Tell if the specified flag is set for position on the map."""

        value = self.get_tile(x, y).get(name)  # return value of that name
        return value

    def create_clouds(self, tileset_image):
        # simple extra function too randomly create clouds on the background of the level
        for cloud in range(7):
            tileset = load_tile_table(tileset_image, 48, 48)
            tile_pos_x = random.randint(0, 2)
            tile_pos_y = 0
            obj_image = tileset[tile_pos_x][tile_pos_y]
            obj_position = AVector(random.randint(0, 3200), random.randint(0, 1600))
            scale = random.randint(250, 360)
            obj_scale = AVector(scale, scale)
            layer = random.randint(4, 9) / 10.0
            cloud_image = pygame.transform.scale(obj_image, obj_scale)
            cloud = Cloud(self, obj_position, obj_scale, cloud_image, layer)
            self.list_draw.append(cloud)

    def create_gradient_background(self, color_1, color_2):
        self.background = DrawableObj(self)
        surface = copy.copy(screen)
        fill_gradient(surface, color_1, color_2)
        self.background.image = surface
        self.list_draw.append(self.background)

    def __draw_cmp(self, obj1, obj2):
        """Defines how our drawable objects should be sorted"""
        if obj1.draw_order > obj2.draw_order:
            return 1
        elif obj1.draw_order < obj2.draw_order:
            return -1
        else:
            return 0

    def __up_cmp(self, obj1, obj2):
        """Defines how our updatable objects should be sorted"""
        if obj1.update_order > obj2.update_order:
            return 1
        elif obj1.update_order < obj2.update_order:
            return -1
        else:
            return 0

    def __sort_up(self):
        """Sort the updatable objects according to ascending order"""
        if self.__do_need_sort_up:
            self.list_update.sort(key=cmp_to_key(self.__up_cmp))
            self.__do_need_sort_up = False

    def __sort_draw(self):
        """Sort the drawable objects according to ascending order"""
        if self.__do_need_sort_draw:
            self.list_draw.sort(key=cmp_to_key(self.__draw_cmp))
            self.__do_need_sort_draw = False

    def update(self, milliseconds):
        """Updates all of the objects in our world."""
        self.__sort_up()
        for obj in self.list_update:
            obj.update(milliseconds)

    def draw(self, milliseconds, surface):
        """Draws all of the objects in our world."""
        self.__sort_draw()
        for obj in self.list_draw:
            # Check to see if the object is visible to the camera before doing anything to it.
            if obj.is_static or obj.is_visible_to_camera(self.camera):
                obj.draw(milliseconds, surface)


class Level_2(Level):
    def __init__(self):
        super(Level_2, self).__init__("level_1_YAML.map")

        #        self.load_level("level_1_YAML.map")

        # put debug in only for debugging (obviously)
        debug = Debug(self)
        self.list_update.append(debug)
        self.list_draw.append(debug)


class Level_menu_main(Level):
    def __init__(self):
        super(Level_menu_main, self).__init__()

        self.create_gradient_background((170, 255, 255), (255, 255, 255))

        self.menu = Menu_main(self)
        self.list_draw.append(self.menu)
        self.list_update.append(self.menu)


class Level_1(Level):
    def __init__(self):
        super(Level_1, self).__init__()

        self.background = DrawableObj(self)
        surface = copy.copy(screen)
        fill_gradient(surface, (170, 255, 255), (255, 255, 255))
        self.background.image = surface
        self.list_draw.append(self.background)
        self.load_level("data/maps/level_1.map")

        cloud_1 = Cloud(self, AVector(-200, 0), AVector(0, 0))
        cloud_2 = Cloud(self, AVector(1600, 400), AVector(1, 0))
        cloud_3 = Cloud(self, AVector(1200, -200), AVector(2, 0))
        self.list_clouds = [cloud_1, cloud_2, cloud_3]

        self.list_update.append(self.player)
        self.list_update.append(self.camera)

        self.list_draw.extend(self.list_clouds)
        self.list_draw.append(self.image_background)
        self.list_draw.extend(self.list_npc)
        # self.list_draw.extend(self.list_interactive_tiles)
        self.list_draw.append(self.player)
        self.list_draw.append(self.image_overlay)
        # self.list_draw.extend(self.list_collidables) # used for debug to know where solid tiles are

        # debug is above everything
        # can't seem to get it to work properly
        # name = "main.game." + str(main_game.list_update[0]) + ".player.collision_y"
        debug = Debug(self)
        self.list_update.append(debug)
        self.list_draw.append(debug)


# menu and button classes
# blueprint
class Button(DrawableObj):
    def __init__(self, level, scale, position, image_deselect, image_select, image_selected=None):
        super(Button, self).__init__(level)

        self.scale = scale
        self.position = position
        if image_selected == None:
            image_selected = image_select
        self.image_deselect = pygame.transform.scale(image_deselect, scale)
        self.image_select = pygame.transform.scale(image_select, scale)
        self.image_selected = pygame.transform.scale(image_selected, scale)
        self.image = self.image_deselect
        self.selected = False

    def select(self):
        self.selected = True
        self.image = self.image_select

    def deselect(self):
        self.selected = False
        self.image = self.image_deselect

    def clicked_action(self):
        self.image = self.image_selected
        ''' needs to be overwritten'''
        pass


class Button_main_menu(Button):
    def __init__(self, level, scale, position, image_deselect, image_select):
        super(Button_main_menu, self).__init__(level, scale, position, image_deselect, image_select)

        self.sound_select = load_sound("menu/menu_select.wav")
        self.sound_select.set_volume(0.04)
        self.sound_selected = load_sound("menu/menu_selected.wav")
        self.sound_selected.set_volume(0.04)

    def select(self):
        super(Button_main_menu, self).select()
        self.sound_select.play()

    def clicked_action(self):
        super(Button_main_menu, self).clicked_action()
        self.sound_selected.play()


class Button_new_game(Button_main_menu):
    def __init__(self, level):
        scale = AVector(38 * 10, 7 * 10)
        position = AVector(50, 5 * 10)
        image_deselect = load_png("menu/button_new_game_deselected.png")
        image_select = load_png("menu/button_new_game_selected.png")

        super(Button_new_game, self).__init__(level, scale, position, image_deselect, image_select)

    def clicked_action(self):
        super(Button_new_game, self).clicked_action()
        main_game.game_state = "game"

        level_2 = Level_2()
        main_game.list_update = [level_2]
        main_game.list_draw = [level_2]  # main_game.player is drawn in level_1 so you can use layers
        # for debug put main_game.debug_info, main_game.camera in the list
        # game.list_draw.extend(level_1.list_solid_tiles)


class Button_load_level(Button_main_menu):
    def __init__(self, level):
        scale = AVector(41 * 10, 7 * 10)
        position = AVector(50, 13 * 10)
        image_deselect = load_png("menu/button_load_level_deselected.png")
        image_select = load_png("menu/button_load_level_selected.png")

        super(Button_load_level, self).__init__(level, scale, position, image_deselect, image_select)

    def clicked_action(self):
        super(Button_load_level, self).clicked_action()
        print("level loading begins")
        main_game.game_state = "menu_loadlevel"


class Button_info(Button_main_menu):
    def __init__(self, level):
        scale = AVector(17 * 10, 7 * 10)
        position = AVector(50, 21 * 10)
        image_deselect = load_png("menu/button_info_deselected.png")
        image_select = load_png("menu/button_info_selected.png")

        super(Button_info, self).__init__(level, scale, position, image_deselect, image_select)

    def clicked_action(self):
        super(Button_info, self).clicked_action()
        print("main main_game begins")
        main_game.game_state = "menu_info"


# blueprint
class Menu(DrawableObj):
    def __init__(self, level):
        super(Menu, self).__init__(level)

        # The keyboard button that selects the button above the currently selected button.
        self.move_up_button = K_UP

        # The keyboard button that selects the button below the currently selected button.
        self.move_down_button = K_DOWN

        # The keyboard button we will querty for clicked events.
        self.select_button = K_SPACE

        # The index of the currently selected button.
        self.current_index = -1

        # List of buttons
        self.buttons = []

    def update(self, milliseconds):
        # Set the default selected button. This is necessary to to get correct behavior when the menu first starts running.
        if self.current_index == -1:
            self.current_index = 0
            self.buttons[self.current_index].select()

        if main_game.keyboard.is_clicked(self.move_up_button):
            self.move_up()
        if main_game.keyboard.is_clicked(self.move_down_button):
            self.move_down()
        if main_game.keyboard.is_released(self.select_button):
            self.buttons[self.current_index].clicked_action()

        super(Menu, self).update(milliseconds)

    def move_up(self):
        """
        Try to select the button above the currently selected one.
        If a button is not there, wrap down to the bottom of the menu and select the last button.
        """
        old_index = self.current_index
        self.current_index -= 1
        self.__wrap_index()
        self.__handle_selections(old_index, self.current_index)

    def move_down(self):
        """
        Try to select the button under the currently selected one.
        If a button is not there, wrap down to the top of the menu and select the first button.
        """
        old_index = self.current_index
        self.current_index += 1
        self.__wrap_index()
        self.__handle_selections(old_index, self.current_index)

    def __wrap_index(self):
        """Wraps the current_index to the other side of the menu."""
        if self.current_index < 0:
            self.current_index = len(self.buttons) - 1
        elif self.current_index >= len(self.buttons):
            self.current_index = 0

    def __handle_selections(self, old_index, new_index):
        # Don't perform any deselections or selections if the currently selected button hasn't changed.
        if old_index is not new_index:
            # Deselect the old button
            self.buttons[old_index].deselect()
            ##            print("Button " + str(old_index) + " deselected.")

            # Select the new button.
            self.buttons[new_index].select()

    ##            print("Button " + str(new_index) + " selected.")

    def draw(self, milliseconds, surface):
        for button in self.buttons:
            button.draw(milliseconds, surface)
        super(Menu, self).draw(milliseconds, surface)


class Menu_main(Menu):
    def __init__(self, level):
        super(Menu_main, self).__init__(level)

        self.button_new_game = Button_new_game(level)
        self.button_load_level = Button_load_level(level)
        self.button_info = Button_info(level)
        self.buttons = [self.button_new_game, self.button_load_level, self.button_info]


class Button_level_1(Button):
    def __init__(self, level):
        scale = AVector(48 * 10, 7 * 10)
        position = AVector(100, 10 * 10)
        image_deselect = load_png("menu/button_level_1_deselected.png")
        image_select = load_png("menu/button_level_1_selected.png")

        super(Button_level_1, self).__init__(level, scale, position, image_deselect, image_select)

    def clicked_action(self):
        print("main game begins")
        main_game.game_state = "game"

        level_1 = Level("data/maps/level_1.map")
        main_game.list_update = [main_game.debug_info, main_game.camera, main_game.player]
        main_game.list_draw = [level_1, main_game.debug_info]  # game.player is drawn in level_1 so you can use layers
        # for debug put game.debug_info, game.camera in the list
        # game.list_draw.extend(level_1.list_solid_tiles)


class Menu_level_loader(Menu):
    def __init__(self, level):
        super(Menu_level_loader, self).__init__()

        self.button_level_1 = Button_level_1(level)
        self.buttons = [self.button_level_1]


#######################################################################################################################
# in game classes
class PhysicsObj(DrawableObj):
    """A class with basic physics implemented."""

    def __init__(self, level, position=AVector(0, 0), scale=AVector(0, 0), velocity=AVector(0, 0),
                 acceleration=AVector(0, 0)):
        super(PhysicsObj, self).__init__(level)

        self.is_static = False
        self.position = copy.copy(position)
        self.velocity = copy.copy(velocity)
        self.acceleration = copy.copy(acceleration)

        self.scale = AVector(int(scale.x), int(scale.y))
        self.rect = pygame.Rect(self.position, self.scale)

        self.scale_factor = copy.copy(self.level.scale_factor)

    def update(self, milliseconds):
        super(PhysicsObj, self).update(milliseconds)
        # vf = vi + a * t
        time = (milliseconds / 1000.0)
        self.velocity += self.acceleration * time
        self.position += self.velocity * time
        self.rect.topleft = self.position


class SolidObj(PhysicsObj):
    """A class for solid tiles etc..."""

    def __init__(self, level, position, scale):
        super(SolidObj, self).__init__(level, position, scale)

        self.image = pygame.Surface((int(self.scale.x), int(self.scale.y)))
        self.image.fill((0, 255, 0))

    def collision_response(self, player, xvel, yvel):
        if not self.velocity.x == 0:
            relative_velocity = player.velocity - self.velocity
            if self.velocity.x < 0:
                if relative_velocity.x > 0:
                    player.velocity.x -= relative_velocity.x
                    player.velocity.x -= 18
                if relative_velocity.x < 0:
                    player.velocity.x += relative_velocity.x
            if self.velocity.x > 0:
                if relative_velocity.x > 0:
                    player.velocity.x += relative_velocity.x + 10
                if relative_velocity.x < 0:
                    player.velocity.x -= relative_velocity.x
                    player.velocity.x += 80

        if xvel > 0:
            player.position.x = self.rect.left - player.scale.x
            player.rect.left = player.position.x
            player.velocity.x = 0
            player.collision_x = 2
        if xvel < 0:
            player.position.x = self.rect.right
            player.rect.left = player.position.x
            player.velocity.x = 0
            player.collision_x = 1
        if yvel > 0:
            player.position.y = self.rect.top - player.scale.y
            player.rect.top = player.position.y
            player.velocity.y = 0
            player.collision_y = 1
        if yvel < 0:
            player.position.y = self.rect.bottom
            player.rect.top = player.position.y
            player.velocity.y = 0
            player.collision_y = 2


class PlatformObj(PhysicsObj):
    """A class for platform tiles etc..."""

    def __init__(self, level, position, scale):
        super(PlatformObj, self).__init__(level, position, scale)

        self.image = pygame.Surface((self.scale.x, self.scale.y))
        self.image.fill((0, 0, 255))

        self.scale_factor = copy.copy(self.level.scale_factor)

    def collision_response(self, player, xvel, yvel):
        if yvel > 0:
            if 0.1 * yvel > 15:
                variable = 15
            else:
                variable = 0.1 * yvel
            if (player.position.y + player.scale.y) < self.rect.top + variable * self.scale_factor:
                player.position.y = self.rect.top - player.scale.y
                player.rect.top = player.position.y
                player.velocity.y = 0
                player.collision_y = 1

                # this part is for moving platforms
                if not self.velocity.x == 0:
                    ##                    relative_velocity = player.velocity - self.velocity
                    ##                    if self.velocity.x < 0:
                    ##                        if relative_velocity.x > 0:
                    ##                            player.velocity.x -= relative_velocity.x
                    ##                            #player.velocity.x /= 0.7
                    ##                            #player.velocity.x -= 18
                    ##                        if relative_velocity.x < 0:
                    ##                            player.velocity.x += relative_velocity.x
                    ##                            #player.velocity.x /= 0.7
                    ##                    if self.velocity.x > 0:
                    ##                        if relative_velocity.x > 0:
                    ##                            player.velocity.x += relative_velocity.x # + 10
                    ##                            #player.velocity.x /= 0.7
                    ##                        if relative_velocity.x < 0:
                    ##                            player.velocity.x -= relative_velocity.x
                    ##                            #player.velocity.x /= 0.7
                    ##                            #player.velocity.x += 80
                    if self.scale_factor == 1.0:
                        player.position.x += self.velocity.x / 10
                    elif self.scale_factor == 2.0:
                        player.position.x += self.velocity.x / 15
                    elif self.scale_factor == 3.0:
                        player.position.x += self.velocity.x / 20
                    elif self.scale_factor == 4.0:
                        player.position.x += self.velocity.x / 20
                    else:
                        print("no number specified for this specific scale_factor "
                              "in the PlatformObj.collision_response()")


class AnimationLoopObj(DrawableObj):
    """A class for animations that loop"""

    def __init__(self, level, position, scale, image_sequence, tpf):
        super(AnimationLoopObj, self).__init__(level)

        self.scale_factor = copy.copy(self.level.scale_factor)
        self.is_static = False
        self.position = copy.copy(position)
        self.scale = copy.copy(scale)
        self.rect = pygame.Rect(self.position, self.scale)

        scale = AVector(int(scale.x), int(scale.y))

        self.image_sequence = []
        images_folder = os.path.join('data/images', image_sequence[0])
        for i in range(count_files(images_folder)):
            path_1 = os.path.join(image_sequence[0], image_sequence[1])
            path_2 = path_1 + str(i + 1) + ".png"
            image = pygame.transform.scale(load_png(path_2), scale)
            self.image_sequence.append(image)

        self.image = self.image_sequence[0]

        # variables for animation
        self.pause = 0
        self.frame = 0
        self.delay = tpf  # ticks per frame

    def update(self, milliseconds):
        super(AnimationLoopObj, self).update(milliseconds)

        self.pause += 1
        if self.pause > self.delay:
            self.pause = 0
            self.frame += 1
            if self.frame >= len(self.image_sequence):
                self.frame = 0

        self.image = self.image_sequence[self.frame]


class AnimationOnCollisionObj(SolidObj):
    """A class for animations that animate on collision"""

    def __init__(self, level, position, scale, image_sequence, tpf, condition):
        super(AnimationOnCollisionObj, self).__init__(level, position, scale)

        self.position.x += 1  # glitch fix these objects are 1 pixel off
        self.position.y += 1  # glitch fix these objects are 1 pixel off

        self.scale_factor = copy.copy(self.level.scale_factor)

        scale = AVector(int(scale.x), int(scale.y))

        self.image_sequence = []
        images_folder = os.path.join('data/images', image_sequence[0])
        for i in range(count_files(images_folder)):
            path_1 = os.path.join(image_sequence[0], image_sequence[1])
            path_2 = path_1 + str(i + 1) + ".png"
            image = pygame.transform.scale(load_png(path_2), scale)
            self.image_sequence.append(image)

        self.image = self.image_sequence[0]

        # variables for animation
        self.pause = 0
        self.frame = 0
        self.delay = tpf  # ticks per frame
        self.timer = 0

        self.condition = condition

        self.animation_done = False
        self.animation_loop = True

    def collision_response(self, player, xvel, yvel):
        exec(self.condition)

    def update(self, milliseconds):
        super(AnimationOnCollisionObj, self).update(milliseconds)

        if self.timer == 1:
            self.pause += 1
            if self.pause > self.delay:
                self.pause = 0
                self.frame += 1
                if self.frame >= len(self.image_sequence):
                    if self.animation_loop:
                        self.frame = 0
                        self.timer = 0
                    else:
                        self.frame = len(self.image_sequence) - 1
                        self.animation_done = True

            self.image = self.image_sequence[self.frame]


class Timer(UpdatableObj):
    def __init__(self, alarm_time=0.0):
        super(Timer, self).__init__()

        # The timer at which the timer is currently at (in milliseconds)
        self.__current_time = 0.0

        # The time at which the timer should begin ringing (in milliseconds)
        self.alarm_time = alarm_time

    # Define our getter methods
    def get_current_time(self):
        """Get the current time that the timer is at."""
        return self.__current_time

    # Define our wrapper properties
    current_time = property(get_current_time)

    def is_ringing(self):
        """Is the timer ringing?"""
        if self.__current_time >= self.alarm_time:
            return True

        return False

    def reset(self):
        """Reset the time inside of the timer."""
        self.__current_time = 0.0

    def update(self, milliseconds):
        super(Timer, self).update(milliseconds)
        if not self.is_ringing():
            self.__current_time += milliseconds


class NPC(SolidObj):
    """A class for NPC's"""

    def __init__(self, level, position, scale, image, dialog_file):
        super(NPC, self).__init__(level, position, scale)

        self.image = image
        self.dialog_file = dialog_file
        self.dialog_tree = DialogTree(level, self, dialog_file)

        self.likes_player = 0

    def collision_response(self, player, xvel, yvel):
        # dialog test
        if not self.level.find_obj_in_list(self.level.list_draw, "dialog", "tag"):
            if main_game.keyboard.is_clicked(K_DOWN):
                self.dialog_tree.load_node(0)

                self.level.list_draw.append(self.dialog_tree)
                self.level.list_update.append(self.dialog_tree)


class AABoundingBox(PhysicsObj):
    """Represents an axis aligned bounding box."""

    def __init__(self, level, position, scale, velocity=AVector(0, 0), acceleration=AVector(0, 0)):
        super(AABoundingBox, self).__init__(level, position, scale, velocity, acceleration)

        self.collision_x = 0
        self.collision_y = 0

    def collision_detection(self, objects, xvel=None, yvel=None):
        if xvel == None:
            xvel = self.velocity.x
        if yvel == None:
            yvel = self.velocity.y

        for obj in objects:
            if self.rect.colliderect(obj.rect):
                function = getattr(obj, "collision_response")
                function(self, xvel, yvel)

    def update(self, milliseconds):
        # print(int(self.velocity.x))
        # print(self.position.x)

        self.collision_x = 0
        self.collision_y = 0
        time = (milliseconds / 1000.0)

        self.velocity.y += self.acceleration.y
        self.position.y += self.velocity.y * time * self.scale_factor
        # self.position.y = int(self.position.y) # so he doesn't sometimes bounce 1 pixel on y or x axis
        self.rect.top = self.position.y
        self.collision_detection(self.level.list_collision, 0, self.velocity.y)

        self.velocity.x += self.acceleration.x
        self.position.x += self.velocity.x * time * self.scale_factor
        # self.position.x = int(self.position.x) # so he doesn't sometimes bounce 1 pixel on y or x axis
        self.rect.left = self.position.x
        self.collision_detection(self.level.list_collision, self.velocity.x, 0)


class ClickableObject(DrawableObj):
    def __init__(self, level, scale, position, image, image_select, image_selected=None):
        super(Button, self).__init__(level)

        self.scale = scale
        self.position = position

        if not image_select:
            image_select = image
        if not image_selected:
            image_selected = image_select

        self.image_deselect = pygame.transform.scale(image, scale)
        self.image_select = pygame.transform.scale(image_select, scale)
        self.image_selected = pygame.transform.scale(image_selected, scale)
        self.image = self.image_deselect
        self.selected = False

    def select(self):
        self.selected = True
        self.image = self.image_select

    def deselect(self):
        self.selected = False
        self.image = self.image_deselect

    def clicked_action(self):
        self.image = self.image_selected
        ''' needs to be overwritten'''
        pass


class Sprite(DrawableObj):
    def __init__(self, update_order=0, draw_order=0):
        super(Sprite, self).__init__(update_order, draw_order)

        # The surface rendered onto the screen when draw is called.
        self.image = pygame.Surface((0, 0))

        # Our unrotated and unscaled image. This must be used, else PyGame will grind to a halt and crash if many rotations and/or scales are used.
        self.untransformed_image = self.image

        # Determines the area of the image that will be drawn out
        ##        self.rect = pygame.Rect(0, 0, 0, 0)
        self.source = pygame.Rect(0, 0, 0, 0)

        # Basic transformation data
        # Used to set the origin when the surface is scaled or rotated. Contains the
        # original origin (in a value between 0 - 1) that was set by the user or Ragnarok.
        self.__untransformed_nor_origin = AVector(0, 0)
        self.__origin = AVector(0, 0)
        self.__rotation = 0.0
        self.__scale = AVector(1, 1)
        self.tint_color = pygame.Color(255,255,255,255)

        # Is a scale operation pending?
        self.__is_scale_pending = False

        # Is a rotation operation pending?
        self.__is_rot_pending = False

        self.__horizontal_flip = False
        self.__vertical_flip = False

    def get_origin(self):
        return self.__origin

    def set_origin(self, orig):
        # Do not continue if setting the origin would result in division by zero.
        if self.untransformed_image.get_width() == 0 \
                or self.untransformed_image.get_height() == 0:
            return

        self.__origin = orig
        self.__untransformed_nor_origin = AVector(self.__origin.X / self.untransformed_image.get_width(),
                                                  self.__origin.Y / self.untransformed_image.get_height())

    def center_origin(self):
        """Sets the origin to the center of the image."""
        self.set_origin(AVector(self.image.get_width() / 2.0, self.image.get_height() / 2.0))

    def get_rotation(self):
        return self.__rotation

    def set_rotation(self, degrees):
        if degrees > 360:
            degrees -= 360
        elif degrees < 0:
            degrees -= 360

        self.__rotation = degrees
        self.__is_rot_pending = True

    def get_scale(self):
        return self.__scale

    def scale_to(self, width_height=AVector(1,1)):
        """Scale the texture to the specfied width and height."""
        scale_amt = AVector(1,1)
        scale_amt.X = float(width_height.X) / self.image.get_width()
        scale_amt.Y = float(width_height.Y) / self.image.get_height()
        self.set_scale(scale_amt)

    def set_scale(self, scale_amt):
        """
        Scale the texture.
        scale_amt is a Vector2 whose values are between 0 and 1, where 1 is the full texture, and 0 is scaled so that the texture is invisible.
        A scale_amt value greater than one will scale the texture to a greater size.
        """
        self.__scale = scale_amt
        self.__is_scale_pending = True

    def get_hflip(self):
        return self.__horizontal_flip

    def set_hflip(self, val):
        """val is True or False that determines if we should horizontally flip the surface or not."""
        if self.__horizontal_flip is not val:
            self.__horizontal_flip = val
            self.image = pygame.transform.flip(self.untransformed_image, val, self.__vertical_flip)

    def get_vflip(self):
        return self.__vertical_flip

    def set_vflip(self, val):
        """val is True or False that determines if we should vertically flip the surface or not."""
        if self.__vertical_flip is not val:
            self.__vertical_flip = val
            self.image = pygame.transform.flip(self.untransformed_image, self.__horizontal_flip, val)

    origin = property(get_origin, set_origin)
    rotation = property(get_rotation, set_rotation)
    scale = property(get_scale, set_scale)
    h_flip = property(get_hflip, set_hflip)
    v_flip = property(get_vflip, set_vflip)

    def load_texture(self, file_path):
        """Generate our sprite's surface by loading the specified image from disk.
         Note that this automatically centers the origin."""
        self.image = pygame.image.load(file_path)
        self.apply_texture(self.image)

    def apply_texture(self, image):
        """Place a preexisting texture as the sprite's texture."""
        self.image = image.convert_alpha()
        self.untransformed_image = self.image.copy()
        self.source.x = 0
        self.source.y = 0
        self.source.width = self.image.get_width()
        self.source.height = self.image.get_height()
        center = AVector(self.source.width / 2.0,
                         self.source.height / 2.0)
        self.set_origin(center)

    def __resize_surface_extents(self):
        """Handles surface cleanup once a scale or rotation operation has been performed."""
        # Set the new location of the origin, as the surface size may increase with rotation
        self.__origin.X = self.image.get_width() * self.__untransformed_nor_origin.X
        self.__origin.Y = self.image.get_height() * self.__untransformed_nor_origin.Y

        # We must now resize the source rectangle to prevent clipping
        self.source.width = self.image.get_width()
        self.source.height = self.image.get_height()

    def __execute_scale(self, surface, size_to_scale_from):
        """Execute the scaling operation"""
        x = size_to_scale_from[0] * self.__scale[0]
        y = size_to_scale_from[1] * self.__scale[1]
        scaled_value = (int(x), int(y))

        self.image = pygame.transform.scale(self.image, scaled_value)

        self.__resize_surface_extents()

    def __execute_rot(self, surface):
        """Executes the rotating operation"""
        self.image = pygame.transform.rotate(surface, self.__rotation)
        self.__resize_surface_extents()

    def __handle_scale_rot(self):
        """Handle scaling and rotation of the surface"""
        if self.__is_rot_pending:
            self.__execute_rot(self.untransformed_image)
            self.__is_rot_pending = False

            # Scale the image using the recently rotated surface to keep the orientation correct
            self.__execute_scale(self.image, self.image.get_size())
            self.__is_scale_pending = False

        # The image is not rotating while scaling, thus use the untransformed image to scale.
        if self.__is_scale_pending:
            self.__execute_scale(self.untransformed_image, self.untransformed_image.get_size())
            self.__is_scale_pending = False

    def is_visible_to_camera(self, camera):
        if self.coords.X > camera.view_bounds.right:
            return False

        if (self.coords.X + self.image.get_width()) < camera.view_bounds.left:
            return False

        height = self.image.get_height()
        if (self.coords.Y - height) > camera.view_bounds.bottom:
            return False

        if (self.coords.Y + height) < camera.view_bounds.top:
            return False

        return True

    def update(self, milliseconds):
        """Update the sprite and its nodes."""
        if self.is_enabled:
            # Scale and rotate the sprite as necessary
            self.__handle_scale_rot()

    def draw(self, milliseconds, render_surface):
        """Draw the image to the specified surface."""
        if self.is_visible:
            if not (self.__scale[0] == 0 or self.__scale[1] == 0):
                if self.image is not None:
                    # Create our rectangle to describe our sprite.
                    tmpRect = pygame.Rect(self.coords.X - self.__origin.X,
                                          self.coords.Y - self.__origin.Y,
                                          self.image.get_width(),
                                          self.image.get_height())
                    # Apply tinting to the sprite.
                    # tintedSurface = self.image.copy()
                    # self.image.fill(self.tint_color, special_flags = pygame.BLEND_RGB_MULT)
                    render_surface.blit(self.image, tmpRect, self.source, special_flags=0)


class Text(DrawableObj):
    def __init__(self, update_order=0, draw_order=0, font_path="", font_size=0, color=(0, 0, 0)):
        super(Text, self).__init__(update_order, draw_order)

        # We use a sprite to provide text rotation and scaling capibilities.
        self.__font_sprite = Sprite(update_order, draw_order)
        self.__font = None
        self.__text = ""
        self.__font_size = font_size
        self.__font_path = font_path
        self.__color = color
        self.load_font(font_path, font_size)

    def load_font(self, font_path, font_size):
        """Load the specified font from a file."""
        self.__font_path = font_path
        self.__font_size = font_size
        if font_path != "":
            self.__font = pygame.font.Font(font_path, font_size)
            self.__set_text(self.__text)

    def __set_font_size(self, font_size):
        """Sets the size of the font."""
        # We need to reload the font in order to change the font's size.
        self.load_font(self.__font_path, font_size)

    def __get_font_size(self):
        """Gets the current size of the font."""
        return self.__font_size

    def __render_onto_sprite(self):
        """Render the font onto a surface and store the surface into a sprite so we can do more complex stuff with it.
        (such as rotation and scale)"""
        font_surface = self.__font.render(self.__text, True, self.color)
        self.__font_sprite.apply_texture(font_surface)
        self.__font_sprite.center_origin()

    def __set_text(self, string):
        """Set the text that displays."""
        self.__text = string

        # Render the new text into a sprite.
        self.__render_onto_sprite()

    def __get_text(self):
        """Get the text that is currently displaying."""
        return self.__text

    def __set_scale(self, scale):
        """Set the scale of the font."""
        self.__font_sprite.scale = scale

    def __get_scale(self):
        """Get the scale of the font."""
        return self.__font_sprite.scale

    def __set_rotation(self, rotation):
        """Rotate the font."""
        self.__font_sprite.rotation = rotation

    def __get_rotation(self):
        """Get the rotation of the font."""
        return self.__font_sprite.rotation

    def __set_color(self, color):
        self.__color = color
        self.__render_onto_sprite()

    def __get_color(self):
        return self.__color

    # Create our properties.
    text = property(__get_text, __set_text)
    scale = property(__get_scale, __set_scale)
    rotation = property(__get_scale, __set_scale)
    font_size = property(__get_font_size, __set_font_size)
    color = property(__get_color, __set_color)

    def update(self, milliseconds):
        self.__font_sprite.update(milliseconds)
        super(Text, self).update(milliseconds)

    def draw(self, milliseconds, surface):
        # print self.__font_sprite.image.get_size()
        self.__font_sprite.coords = self.coords
        self.__font_sprite.draw(milliseconds, surface)
        super(Text, self).draw(milliseconds, surface)



# PLAYER class
class Player(AABoundingBox):
    def __init__(self, level, position, velocity=AVector(0, 0), acceleration=AVector(0, 0)):
        self.scale_factor = copy.copy(level.scale_factor)
        scale = AVector(int(8 * self.scale_factor), int(18 * self.scale_factor))  # Vector(80,180)
        super(Player, self).__init__(level, position, scale, velocity, acceleration)
        # AABoundingBox.__init__(self, level, position, scale, velocity, acceleration)

        self.image_offset = AVector(int(2 * self.scale_factor), int(3 * self.scale_factor))  # Vector(20,30)
        self.image_scale = AVector(int(12 * self.scale_factor), int(24 * self.scale_factor))  # Vector(120,240)
        self.image = pygame.transform.scale(load_png("characters/player/player.png"), self.image_scale)

        # self.scale_factor *= 2

        self.acceleration = AVector(0, 3.75)
        self.terminal_velocity = 175
        self.terminal_velocity_wall = 25
        self.sliding_down_wall_speed = 75
        self.jump_power = 125
        self.jump_power_side = 125
        self.horizontal_terminal_velocity = 200
        self.horizontal_acceleration = 30
        self.jumped = False
        self.move_wait_time = 10  # used to configure
        self.move_wait_variable_left = 0  # actually used by the class
        self.move_wait_variable_right = 0  # actually used by the class

        self.sound_init()
        self.animation_init()

    def sound_init(self):
        self.sound_channel_walking = pygame.mixer.Channel(0)
        self.sound_walking = load_sound("walking_test_1.ogg")

        self.sound_channel_jump = pygame.mixer.Channel(1)
        self.sound_jump_list = [load_sound("jump/jump_sound_0.ogg"), load_sound("jump/jump_sound_1.ogg"),
                                load_sound("jump/jump_sound_2.ogg"), load_sound("jump/jump_sound_3.ogg"),
                                load_sound("jump/jump_sound_4.ogg")]
        self.sound_jump_variable = 0

        self.sound_channel_landing = pygame.mixer.Channel(2)
        self.sound_landing = load_sound("landing/landing_1.ogg")
        self.sound_landing.set_volume(0.6)
        self.sound_landing_list = [0, 0]

        self.sound_channel_glide = pygame.mixer.Channel(3)
        self.sound_glide = load_sound("glide.ogg")

    def animation_init(self):

        # pygame.transform.scale(load_png("characters/player.png"),self.image_scale)

        self.standing_frame1 = pygame.transform.scale(load_png('characters/player/standing_frame1.png'),
                                                      self.image_scale)
        self.falling_frame1 = pygame.transform.scale(load_png('characters/player/falling_frame1.png'), self.image_scale)
        self.jumping_frame1 = pygame.transform.scale(load_png('characters/player/jumping_frame1.png'), self.image_scale)
        self.jumping_frame2 = pygame.transform.scale(load_png('characters/player/jumping_frame2.png'), self.image_scale)
        self.hanging_frame1 = pygame.transform.scale(load_png('characters/player/hanging_frame1.png'), self.image_scale)

        running_frame1 = pygame.transform.scale(load_png('characters/player/running_frame1.png'), self.image_scale)
        running_frame2 = pygame.transform.scale(load_png('characters/player/running_frame2.png'), self.image_scale)
        running_frame3 = pygame.transform.scale(load_png('characters/player/running_frame3.png'), self.image_scale)
        running_frame4 = pygame.transform.scale(load_png('characters/player/running_frame4.png'), self.image_scale)
        running_frame5 = pygame.transform.scale(load_png('characters/player/running_frame5.png'), self.image_scale)
        running_frame6 = pygame.transform.scale(load_png('characters/player/running_frame6.png'), self.image_scale)
        running_frame7 = pygame.transform.scale(load_png('characters/player/running_frame7.png'), self.image_scale)
        running_frame8 = pygame.transform.scale(load_png('characters/player/running_frame8.png'), self.image_scale)

        self._images = [running_frame1, running_frame2, running_frame3, running_frame4, running_frame5, running_frame6,
                        running_frame7, running_frame8]

        fps = 20  # 15

        # Track the time we started, and the time between updates.
        # Then we can figure out when we have to switch the image.
        self._start = pygame.time.get_ticks()
        self._delay = 1000 / fps
        self._last_update = 0
        self._frame = 0

        self.state_animation = 0  # 0 = standing still, 1 = jumping, 2 = falling, 3 = running, 4 = hanging
        self.leftorright = 0  # 0 = right, 1 = left
        self.variable = 0  # needed for collision check in animation()

        # for jump animation
        self.jump_variable = False
        self.jump_counter = 0

        # Call update to set our first image.
        self.update_animation(pygame.time.get_ticks())

    def update(self, milliseconds):
        self.handle_event(main_game.keyboard)
        self.velocity.x *= 0.7

        self.move_wait_variable_left -= 1
        self.move_wait_variable_right -= 1

        if self.collision_y == 0:
            if self.collision_x == 0:
                if self.velocity.y > self.terminal_velocity:
                    self.velocity.y = self.terminal_velocity
            else:
                if main_game.keyboard.is_down(K_DOWN):
                    self.velocity.y = self.sliding_down_wall_speed
                elif self.velocity.y > self.terminal_velocity_wall:
                    # self.sound_channel_glide.play(self.sound_glide)
                    self.velocity.y = self.terminal_velocity_wall

        super(Player, self).update(milliseconds)

        self.update_animation(pygame.time.get_ticks())
        self.update_sound()

    def update_sound(self):
        if self.sound_jump_variable > 4:
            self.sound_jump_variable = 0

        self.sound_landing_list.pop()
        self.sound_landing_list.insert(0, self.state_animation)

        if (self.sound_landing_list[0] == 0 or self.sound_landing_list[0] == 3 or self.sound_landing_list[0] == 4) and \
                self.sound_landing_list[1] == 2:
            self.sound_channel_landing.play(self.sound_landing)

    def update_animation(self, t):
        if self.collision_y == 1:
            self.variable = 0
            if main_game.keyboard.is_down(K_LEFT) or main_game.keyboard.is_down(K_RIGHT):
                self.state_animation = 3
            if not (main_game.keyboard.is_down(K_LEFT) or main_game.keyboard.is_down(K_RIGHT)) or (
                    main_game.keyboard.is_down(K_LEFT) and main_game.keyboard.is_down(K_RIGHT)):
                self.state_animation = 0

        if self.collision_y != 1:
            self.variable += 1
            if self.variable > 3:
                if self.velocity.y < 0:
                    # jumping
                    self.state_animation = 1
                if self.velocity.y > 0:
                    # falling
                    self.state_animation = 2

        if self.collision_x == 1 or self.collision_x == 2:
            self.state_animation = 4

        if self.collision_x == 2:
            self.leftorright = 0
            if self.collision_x == 1:
                self.leftorright = 1

        if self.state_animation == 0:
            # standing still
            self.image = self.standing_frame1
            if self.leftorright == 1:
                self.image = pygame.transform.flip(self.image, True, False)
        if self.state_animation == 1:
            # jumping
            if self.jump_variable == False:
                self.jump_variable = True
                self.jump_counter = 0
            self.image = self.jumping_frame1
            if 10 < self.jump_counter < 20:
                self.image = self.jumping_frame2
            if self.jump_counter >= 20:
                self.image = self.falling_frame1
            self.jump_counter += 1

            if self.leftorright == 1:
                self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.jump_variable = False
        if self.state_animation == 2:
            # falling
            self.image = self.falling_frame1
            if self.leftorright == 1:
                self.image = pygame.transform.flip(self.image, True, False)
        if self.state_animation == 4:
            # falling
            self.image = self.hanging_frame1
            if self.leftorright == 1:
                self.image = pygame.transform.flip(self.image, True, False)
        if self.state_animation == 3:
            if not self.sound_channel_walking.get_busy():
                self.sound_channel_walking.play(self.sound_walking)
            if t - self._last_update > self._delay:
                self._frame += 1
                if self._frame >= len(self._images): self._frame = 0
                self.image = self._images[self._frame]
                self._last_update = t
                if self.leftorright == 1:
                    self.image = pygame.transform.flip(self.image, True, False)
        else:
            if self.sound_channel_walking.get_busy():
                self.sound_channel_walking.stop()

    def draw(self, milliseconds, surface):
        # Draw the object
        if self.is_static:
            surface.blit(self.image, self.position)
        else:
            relative_position = self.position - self.level.camera.position - self.image_offset
            surface.blit(self.image, relative_position)

    def handle_event(self, keyboard):
        if keyboard.is_down(K_LEFT):
            self.leftorright = 1
            if self.move_wait_variable_left < 0:
                if self.velocity.x > -self.horizontal_terminal_velocity:
                    self.velocity.x -= self.horizontal_acceleration
        if keyboard.is_down(K_RIGHT):
            self.leftorright = 0
            if self.move_wait_variable_right < 0:
                if self.velocity.x < self.horizontal_terminal_velocity:
                    self.velocity.x += self.horizontal_acceleration
        if keyboard.is_down(K_UP):
            self.velocity.y = -62.5
        if keyboard.is_down(K_SPACE):
            if self.jumped == False:
                if self.collision_y == 1:
                    self.velocity.y = -self.jump_power
                    self.jumped = True
                    self.sound_channel_jump.play(self.sound_jump_list[self.sound_jump_variable])
                    self.sound_jump_variable += 1
                elif self.collision_x == 1:
                    self.velocity.y = -self.jump_power
                    self.velocity.x = self.jump_power_side
                    self.jumped = True
                    self.move_wait_variable_left = self.move_wait_time
                    self.sound_channel_jump.play(self.sound_jump_list[self.sound_jump_variable])
                    self.sound_jump_variable += 1
                elif self.collision_x == 2:
                    self.velocity.y = -self.jump_power
                    self.velocity.x = -self.jump_power_side
                    self.jumped = True
                    self.move_wait_variable_right = self.move_wait_time
                    self.sound_channel_jump.play(self.sound_jump_list[self.sound_jump_variable])
                    self.sound_jump_variable += 1

        if keyboard.is_up(K_SPACE) and (self.collision_y == 1 or self.collision_x == 1 or self.collision_x == 2):
            self.jumped = False
        if keyboard.is_down(K_LSHIFT):
            self.velocity.y = 1
        if keyboard.is_down(K_LEFT) and keyboard.is_down(K_RIGHT):
            pass

    def collision_response(self, obj, xvel, yvel):
        obj.collision_response()


class Debug(DrawableObj):
    """simple debug class that shows variables realtime on screen"""

    def __init__(self, level):
        super(Debug, self).__init__(level)

        pixel_art_font = "/Library/Fonts/pixel-art_1.ttf"  # other option: "/Library/Fonts/pixel-art_2.ttf"
        self.font = pygame.font.Font(pixel_art_font, 15)

        self.text = "variable = "
        self.image = self.font.render(self.text, True, (255, 255, 255), (0, 0, 0))

    def update(self, milliseconds):
        self.text = "variable = " + str(
            main_game.clock.get_fps())  # put main_game.clock.get_fps() in the str() if you want the fps
        self.image = self.font.render(self.text, True, (255, 255, 255), (0, 0, 0))


class TextBox(DrawableObj):
    def __init__(self, level, position, width, text, scroll=False, font_size=5,
                 font_path="/Library/Fonts/pixel-art_1.ttf"):  # other option: "/Library/Fonts/pixel-art_2.ttf"
        super(TextBox, self).__init__(level)

        self.scale_factor = copy.copy(self.level.scale_factor)

        self.tag = "TextBox"
        self.position = position
        self.font = pygame.font.Font(font_path, int(font_size * self.scale_factor))
        self.is_static = False
        self.dialog = []
        self.width = int(width * self.scale_factor)

        self.timer = 0

        self.text_color = (0, 0, 0)
        self.background_color = (255, 255, 255)
        self.border_color = (0, 0, 0)

        self.border_width = int(1.25 * self.scale_factor)
        self.margin = int(2 * self.scale_factor)
        self.space_between_lines = int(0.75 * self.scale_factor)

        self.character_number = 0
        self.scroll = scroll
        self.done_with_scroll = False

        self.set_text(text)

    def set_text(self, text):
        if self.scroll:
            self.final_text = text
            self.text = ""
        else:
            self.final_text = text
            self.text = self.final_text

        self.make_box(self.width)
        self.make_text(self.width)

    def make_box(self, width=None):
        if width is None:
            width = self.width

        # calculate the height of the message box width the given width
        xpos = copy.copy(self.margin)
        ypos = copy.copy(self.margin)
        for word in self.final_text.split(" "):
            ren = self.font.render(word + " ", True, self.text_color)
            w = ren.get_width()
            if xpos > width - w:
                ypos += ren.get_height() + self.space_between_lines
                xpos = copy.copy(self.margin)
            xpos += w

        if ypos == self.margin:
            width = xpos

        height = ypos + ren.get_height() + self.margin
        self.image = pygame.Surface((width, height))
        self.scale = AVector(width, height)
        self.image.fill(self.background_color)
        if self.border_width != 0:
            pygame.draw.rect(self.image, self.border_color, (0, 0, width, height), self.border_width)

    def make_text(self, width=None):
        if width == None:
            width = self.width

        # actually draw the text on the created surface (above)
        xpos = copy.copy(self.margin)
        ypos = copy.copy(self.margin)
        for word in self.text.split(" "):
            ren = self.font.render(word + " ", True, self.text_color)
            w = ren.get_width()
            if xpos > width - w:
                ypos += ren.get_height() + self.space_between_lines
                xpos = copy.copy(self.margin)
            self.image.blit(ren, (xpos, ypos))
            xpos += w

    def update(self, milliseconds):
        if self.scroll:
            if self.character_number < len(self.final_text):
                self.character_number += 0.5
                if main_game.keyboard.is_down(K_SPACE):
                    self.character_number += 1.0
                self.text = self.final_text[:int(self.character_number)]
                self.make_box()
                self.make_text()
            else:
                self.done_with_scroll = True


class ButtonDialog(Button):
    def __init__(self, level, scale, position, image_deselect, image_select, dialog_tree, node_to_go, commands,
                 npc_owner):
        super(ButtonDialog, self).__init__(level, scale, position, image_deselect, image_select)

        self.node_to_go = node_to_go
        self.dialog_tree = dialog_tree
        self.commands = commands
        self.npc_owner = npc_owner

    def clicked_action(self):
        if not self.commands == None:
            exec(self.commands)

        self.dialog_tree.load_node(self.node_to_go)


class NodeDialog(Menu):
    def __init__(self, level, dialog_tree, data_list, position, npc_owner):
        super(NodeDialog, self).__init__(level)

        self.scale_factor = copy.copy(self.level.scale_factor)

        self.npc_owner = npc_owner
        data_list = copy.copy(data_list)
        position = copy.copy(position)

        self.move_up_button = K_UP
        self.move_down_button = K_DOWN
        self.select_button = K_RETURN

        # print(data_list)

        self.parse_data_list(data_list)

        distance_between_choices = 10

        self.message_TextBox = TextBox(level, position, 50, self.message_text, True)
        choice_position = position + AVector(0, self.message_TextBox.scale.y)

        for choice in self.choice_list:
            choice_position += AVector(0, distance_between_choices)  # + Vector(0,self.choice_list.index(choice))
            choice_TextBox = TextBox(level, copy.copy(choice_position), 50, choice[0])
            choice_position += AVector(0, choice_TextBox.scale.y)

            scale = choice_TextBox.scale
            commands = choice[2]
            image_deselect = choice_TextBox.image

            # make image select by changing background color
            choice_TextBox.background_color = (200, 200, 200)
            choice_TextBox.make_box()
            choice_TextBox.make_text()
            image_select = choice_TextBox.image

            node_to_go = choice[1]

            button_position = copy.copy(choice_TextBox.position)

            choice_button = ButtonDialog(level, scale, button_position, image_deselect, image_select, dialog_tree,
                                         node_to_go, commands, self.npc_owner)
            choice_button.is_static = False
            self.buttons.append(choice_button)

        self.height = -(position.y - (button_position.y + choice_TextBox.scale.y))
        message_offset = AVector(0, 0)
        message_offset.x = -self.message_TextBox.scale.x / 2 + self.npc_owner.scale.x / 2
        message_offset.y = -self.message_TextBox.scale.y - (3.75 * self.scale_factor) + 0.2  # + 0.5 is against wobbling
        choices_offset = AVector(0, 0)
        choices_offset.x = -self.message_TextBox.scale.x / 2 + self.npc_owner.scale.x / 2 + (
                self.message_TextBox.scale.x - (9.5 * self.scale_factor))
        choices_offset.y = -self.message_TextBox.scale.y - (3.75 * self.scale_factor) + 0.2  # + 0.5 is against wobbling

        self.message_TextBox.position += message_offset
        for buttons in self.buttons:
            buttons.position += choices_offset

    def parse_data_list(self, data_list):
        self.message_text = data_list[0]
        self.choice_list = data_list
        self.choice_list.remove(self.message_text)

    def draw(self, milliseconds, surface):
        self.message_TextBox.draw(milliseconds, surface)
        if self.message_TextBox.done_with_scroll:
            super(NodeDialog, self).draw(milliseconds, surface)

    def update(self, milliseconds):
        self.message_TextBox.update(milliseconds)
        if self.message_TextBox.done_with_scroll:
            super(NodeDialog, self).update(milliseconds)


class DialogTree(DrawableObj):
    def __init__(self, level, npc_owner, dialog_file):
        super(DialogTree, self).__init__(level)

        self.tag = "dialog"
        self.npc_owner = npc_owner
        self.position = npc_owner.position
        self.parse_dialog_file(dialog_file)
        self.load_node(0)

    def load_node(self, node):
        if node == "end":
            self.level.list_update.remove(self)
            self.level.list_draw.remove(self)
        else:
            data_list = self.dialog[node]
            self.node = NodeDialog(self.level, self, data_list, self.position, self.npc_owner)

    def parse_dialog_file(self, dialog_file):
        # Using the PyYAML parser
        # It makes a dialog in this structure:
        # {'node_start':
        #               ["message_start", ['choice_1', node_to_be_sent_to_if_choice_1_is_chosen], ['choice_2', node_to_be_sent_to_if_choice_2_is_chosen]],
        #  'node_01':
        #               ["message", ['choice_1', node_to_be_sent_to_if_choice_1_is_chosen]]
        # }
        filename = "data/dialog/" + dialog_file  # filename
        stream = open(filename, 'r')  # opening stream
        yaml_file = yaml.load(stream)  # loading stream
        # print(yaml_file)

        self.dialog = yaml_file

    def update(self, milliseconds):
        self.node.update(milliseconds)

        super(DialogTree, self).update(milliseconds)

    def draw(self, milliseconds, surface):
        self.node.draw(milliseconds, surface)

        super(DialogTree, self).draw(milliseconds, surface)


class Cloud(DrawableObj):
    def __init__(self, level, position, scale, image, layer=0.7):
        super(Cloud, self).__init__(level)
        self.position = position
        self.scale = scale
        self.layer = layer
        self.is_static = False

        self.image = image

    def draw(self, milliseconds, surface):
        # Draw the object
        relative_position = self.position - self.level.camera.position
        relative_position *= self.layer
        surface.blit(self.image, relative_position)


#######################################################################################################################

pygame.init()
pygame.display.set_icon(pygame.image.load("data/images/icon_low.png"))
windowWidth, windowHeight = 854, 480  # 854, 480 #640, 360 #750, 500 #1280, 720
window = pygame.display.set_mode(
    (windowWidth, windowHeight))  # put ",pygame.FULLSCREEN" after "windowHeight)" for fulscreen
pygame.display.set_caption('First Game')
screen = pygame.display.get_surface()
pygame.mouse.set_visible(True)

# initialize Game()
main_game = Game()


# main function
def main():
    main_game.go()


# import cProfile as profile
# profile.run('main()')
main()