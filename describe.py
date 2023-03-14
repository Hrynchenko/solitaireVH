import pygame.image
import pygame.rect
import os.path

from pygame import image

from outlook import WinSet


def image_loading(name):
    set_image = pygame.image.load(os.path.join(WinSet.image_path, name + WinSet.image_type))
    return set_image.convert_alpha()


# Basic class on which all the other classes will depend
class DescribeObject(object):
    def __init__(self, name, pos):
        # Name of the object
        self.name = name
        # set up position and area (starts of as a 0 dimensional rect)
        self.rect = pygame.Rect(pos[0], pos[1], 0, 0)

    # check position availability
    def has_position(self, pos):
        if not self.visible:
            return False
        return self.rect.collidepoint(pos)

    def collision(self, obj):
        return self.rect.colliderect(obj.rect)

    # Just returns the x, y position of self.rect
    def get_position(self):
        return self.rect.x, self.rect.y

    # Moving objects might not be as easy as chaing rect.x, so use subclass this if necessary
    def set_position(self, pos):
        self.rect.x, self.rect.y = pos[0], pos[1]

    def move_position(self, move):
        self.rect.move_ip(move)


# An object that has an image associated with it
# Can be made invisible
class DescribeImage(DescribeObject):
    def __init__(self, name, pos, image):
        DescribeObject.__init__(self, name, pos)
        # All objects have an image (surface) associated with them.
        self.image = self.set_image(image)
        # objects can be set up be visible or invisible
        self.visible = True

    # Set up draw function
    def draw(self, screen):
        if self.visible:
            screen.blit(image, self.rect)

    # Each object is associated with an image.
    # As soon as the image is loaded, the self.rect attribute needs to be updated
    def set_image(self, image):
        loaded = image_loading(image)
        self.rect.w, self.rect.h = loaded.get_width(), loaded.get_height()
        return loaded


# The basic container for cards. Subsequent piles will subclass it
# The image represents the empty pile
class DescribePile(DescribeImage):

    def __init__(self, name, pos, image, cards=[]):
        DescribeImage.__init__(self, name, pos, image)
        self.cards = []
        self.addCards(cards)

    # Are there any cards in the pile?
    def pile_empty(self):
        if self.cards: return False
        return True

    # How many cards are in the pile
    def cardNum(self):
        return len(self.cards)

    # Turns all the cards in the pile faceup or facedown
    def allFaceUp(self, boolean):
        for card in self.cards:
            card.face_up = boolean

    # Draws the bottom symbol stored in self.image (generally used to show an empty pile)
    def drawBottom(self, screen):
        screen.blit(self.image, self.rect)

    # Remove cards from the top of the pile (end of the list)
    def takeCards(self, num):
        if num > self.cardNum() or num < 0: raise IndexError
        break_point = self.cardNum() - num
        to_take = self.cards[break_point:]  # Cards that are taken
        self.cards = self.cards[: break_point]  # Cards that remain
        return to_take

    def takeAll(self):
        return self.takeCards(self.cardNum())

    # The set_position function moves all the cards, rather than setting the position directly
    # This allows tiled piles to be set correctly, as using set_position directly would make the tiled pile into simple pile
    def set_position(self, pos):
        x_move = pos[0] - self.rect.x
        y_move = pos[1] - self.rect.y

        super(DescribePile, self).set_position(pos)
        for card in self.cards: card.move_position((x_move, y_move))

    def movePosition(self, move):
        super(DescribePile, self).movePosition(move)
        for card in self.cards: card.move_position(move)

    # Simple function that takes cards and puts them back
    def returnCards(self, cards):
        self.addCards(cards)

    # The rest of the functions need to be subclassed
    # Add a list of cards to the end of this pile. This is used to populate the pile originally
    def addCards(self, cards):
        raise NotImplementedError

    def draw(self, screen):
        raise NotImplementedError


# This is the abstract class for a pile where all the cards are exactly on top of each other
# It is fully functional if you want to just display this pile, but cannot be interacted with by user
class DescribeSimplePile(DescribePile):
    def __init__(self, name, pos, image, cards=[]):
        DescribePile.__init__(self, name, pos, image, cards)

    # The draw call does not draw all the cards in the pile
    # Only the top card is drawn, as it hides all the other cards
    def draw(self, screen):
        if not self.visible: return

        if self.pile_empty():
            self.drawBottom(screen)

        else:
            self.cards[-1].draw(screen)

    # Can a cards be added to this pile by the user (for this class, always no)
    def validAddCards(self, pile):
        return False

    # Add a single card (the card keeps track of where it was last added)
    def addSingle(self, card):
        card.set_position((self.rect.x, self.rect.y))
        card.pile = self
        self.cards.append(card)

    # Add cards to this pile
    # If you just want to know if cards could be added by user, run validAddPile
    def addCards(self, cards):
        for card in cards: self.addSingle(card)


# The cards are now spread out vertically (with the last card in the list at the top)
# The tile pile has two spacings between cards
# init_space for the spacing when the pile is just created and add_space for the spacing when new cards are added
class DescribeTilePile(DescribePile):
    def __init__(self, name, pos, image, init_space, add_space, cards=[]):
        self.init_space = init_space
        self.add_space = add_space
        DescribePile.__init__(self, name, pos, image, cards)

    def draw(self, screen):
        if not self.visible:
            return
        if self.pile_empty():
            self.drawBottom(screen)
        for card in self.cards:
            card.draw(screen)

    # card is not allowed to add
    def validAddCards(self, pile):
        return False

    # This function used to determine if a card is being added by the user
    # Or if cards are being returned to a pristine tiled pile
    def add_single(self, card):
        if self.pile_empty():
            card.set_position((self.rect.x, self.rect.y))
        else:
            last_card = self.cards[-1]
            # If the last card is face_up, add the card with add_space spacing
            if last_card.face_up:
                card.set_position((last_card.rect.x, last_card.rect.y + self.add_space))
            # If the last card is faceDown, it means the card should be added with the init_space
            else:
                card.set_position((last_card.rect.x, last_card.rect.y + self.init_space))

        card.pile = self
        self.cards.append(card)
        self.update_area()  # Don't forget to update the new area

    # Add cards to this pile
    def addCards(self, cards):
        for card in cards:
            self.add_single(card)

    # Update the pile area when cards been added
    def update_area(self):
        if self.pile_empty():
            ref = self.image.get_rect()
            self.rect.h = ref.h

        else:  # The pile area is simply between the top of the first and bottom of the last card
            bottom = self.cards[-1].rect.bottom
            top = self.cards[0].rect.top
            self.rect.h = bottom - top

    # When card is remove, the area should be updated to fit to the card number
    def takeCards(self, num):
        result = super(DescribeTilePile, self).takeCards(num)
        self.update_area()
        return result


# Set up the area for multi-piles
# It does not have an image by itself, so self.rect has no dimension
# Which means that has_position has to be subclassed to allow user interaction and define pile interactions
class DescribeMultiPile(DescribeObject):
    def __init__(self, name, pos, space):
        DescribeObject.__init__(self, name, pos)
        self.space = space
        self.piles = []

    # Each added pile is spaced by self.space from the previous pile
    def setup_pile(self, new_pile):
        displace = 0
        for pile in self.piles:
            displace += pile.rect.width + self.space
        new_pile.set_position((self.rect.x + displace, self.rect.y))
        self.piles.append(new_pile)

    # Is a pile located at that position (return None if there is nothing)
    def get_pile(self, pos):
        for pile in self.piles:
            if pile.has_position(pos): return pile

    def has_position(self, pos):
        if self.get_pile(pos): return True
        return False

    def movePosition(self, move):
        for pile in self.piles:
            pile.move_position(move)

    def draw(self, screen):
        for pile in self.piles:
            pile.draw(screen)
