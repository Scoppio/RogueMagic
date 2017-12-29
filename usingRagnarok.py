from RagnarokEngine3.RE3 import Ragnarok, Camera, Timer, GUIButton, \
    GUIMenu, Keyboard, Mouse, MouseState, DrawableObj, Sprite, Pool, Vector2, Text
import pygame
import copy
import yaml

# blueprint

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
        self.scale = Vector2(width, height)
        self.image.fill(self.background_color)
        if self.border_width != 0:
            pygame.draw.rect(self.image, self.border_color, (0, 0, width, height), self.border_width)

    def make_text(self, width=None):
        if width is None:
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
                if Game.keyboard.is_down(pygame.K_SPACE):
                    self.character_number += 1.0
                self.text = self.final_text[:int(self.character_number)]
                self.make_box()
                self.make_text()
            else:
                self.done_with_scroll = True


class Menu(DrawableObj):
    def __init__(self, level):
        super(Menu, self).__init__(level)

        # The keyboard button that selects the button above the currently selected button.
        self.move_up_button = pygame.K_UP

        # The keyboard button that selects the button below the currently selected button.
        self.move_down_button = pygame.K_DOWN

        # The keyboard button we will querty for clicked events.
        self.select_button = pygame.K_SPACE

        # The index of the currently selected button.
        self.current_index = -1

        # List of buttons
        self.buttons = []

    def update(self, milliseconds):
        # Set the default selected button. This is necessary to to get correct behavior when the menu first starts running.
        if self.current_index == -1:
            self.current_index = 0
            self.buttons[self.current_index].select()

        if Game.get_world().Keyboard.is_clicked(self.move_up_button):
            self.move_up()
        if Game.get_world().Keyboard.is_clicked(self.move_down_button):
            self.move_down()
        if Game.get_world().Keyboard.is_released(self.select_button):
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

            # Select the new button.
            self.buttons[new_index].select()

    def draw(self, milliseconds, surface):
        for button in self.buttons:
            button.draw(milliseconds, surface)
        super(Menu, self).draw(milliseconds, surface)


class Button(DrawableObj):
    def __init__(self, level, scale, position, image_deselect, image_select, image_selected=None):
        super(Button, self).__init__(level)

        self.scale = scale
        self.position = position
        if image_selected is None:
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

        self.scale_factor = copy.copy(level.scale_factor)

        self.npc_owner = npc_owner
        data_list = copy.copy(data_list)
        position = copy.copy(position)

        self.move_up_button = pygame.K_UP
        self.move_down_button = pygame.K_DOWN
        self.select_button = pygame.K_RETURN

        # print(data_list)

        self.parse_data_list(data_list)

        distance_between_choices = 10

        self.message_TextBox = TextBox(level, position, 50, self.message_text, True)
        choice_position = position + Vector2(0, self.message_TextBox.scale.y)

        for choice in self.choice_list:
            choice_position += Vector2(0, distance_between_choices)  # + Vector(0,self.choice_list.index(choice))
            choice_TextBox = TextBox(level, copy.copy(choice_position), 50, choice[0])
            choice_position += Vector2(0, choice_TextBox.scale.y)

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

        self.height = -(position.y - (button_position.Y + choice_TextBox.scale.Y))
        message_offset = Vector2(0, 0)
        message_offset.x = -self.message_TextBox.scale.X / 2 + self.npc_owner.scale.x / 2
        message_offset.y = -self.message_TextBox.scale.Y - (3.75 * self.scale_factor) + 0.2  # + 0.5 is against wobbling
        choices_offset = Vector2(0, 0)
        choices_offset.x = -self.message_TextBox.scale.X / 2 + self.npc_owner.scale.x / 2 + (
                self.message_TextBox.scale.X - (9.5 * self.scale_factor))
        choices_offset.y = -self.message_TextBox.scale.Y - (3.75 * self.scale_factor) + 0.2  # + 0.5 is against wobbling

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
        self.level = level
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




display_width = 800
display_height = 600
Game = Ragnarok(preferred_backbuffer_size=Vector2(display_width,display_height),
         window_name="Using Ranarok")

def normalizePosition(value):
    d = (display_width/2 - display_width) * value.X
    h = (display_height / 2 - display_height) * value.Y
    return Vector2(d,h)

black = (0,0,0)
white = (255,255,255)

world = Game.get_world()

world.clear_color = white


def createCard(pos_x, pos_y):
    card = Sprite()
    card.load_texture('data/core/card-template.png')
    card.set_scale(Vector2(0.2, 0.2))
    card.set_origin(Vector2(display_width * pos_x, display_height * pos_y))
    return card

for i in range(10):
    world.add_obj(createCard(i/4, 0.25))

text = Text()
text.load_font(font_path='data/fonts/elementary_gothic_bookhand/Elementary_Gothic_Bookhand.ttf',
                font_size=12)
text.text = "This is a text"
text.coords = normalizePosition(Vector2(-0.8, -0.0))
# text.color=white
world.add_obj(text)

Game.run()
