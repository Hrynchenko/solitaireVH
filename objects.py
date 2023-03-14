import describe
from pygame.locals import *


class Card(describe.DescribeImage):
    # Set up Constants
    # The two colors of the cards
    RED = 1
    BLACK = 2
    # Set up the back image for all the cards
    # Set if with self.loadBack()
    back_of_card = None

    # This static function can be called to load the back_of_card image after the pygame.init() has been called
    # and loading the image for the back of the cards
    @staticmethod
    def back_loading(name):
        Card.back_of_card = describe.image_loading(name)

    def __init__(self, name, pos):
        # The name of the card is 01-13[clubs,diamond,heart,spade]
        # Notice that the every card has a specific named image png file
        describe.DescribeImage.__init__(self, name, pos, name)

        # Sometimes it is necessary to keep track of what pile a card is in
        self.pile = None

        self.face_up = True

    def get_number(self):
        return int(self.name[:-1])

    def get_suit(self):
        return self.name[-1]

    def get_color(self):
        if self.get_suit() == 'h' or self.get_suit() == 'd':
            return Card.RED
        return Card.BLACK

    def color_match(self, card):
        return self.get_color() == card.get_color()

    def draw(self, screen):
        if self.visible:
            image = self.image if self.face_up else Card.back_of_card
            screen.blit(image, self.rect)


# Encodes the draw and discard rule for talon and stock
# The talon pile if face down and upon click moves the top card onto the stockpile face up
# If the talon pile is empty, it takes all the cards from the stockpile back
class TalonPile(describe.DescribeMultiPile):
    DRAW = 0
    DISCARD = 1

    def __init__(self, name, pos, space, bottom, cards=[]):
        describe.DescribeMultiPile.__init__(self, name, pos, space)
        self.setup_pile(self.setupDraw(cards, bottom))
        self.setup_pile(self.setupDiscard(bottom))

    # For the two setup functions, the position does not matter, as the setup_pile function will correctly
    # position the piles
    @staticmethod
    def setupDraw(cards, bottom):
        draw_pile = describe.DescribeSimplePile('Draw', (0, 0), bottom, cards)
        draw_pile.allFaceUp(False)
        return draw_pile

    @staticmethod
    def setupDiscard(bottom):
        discard_pile = describe.DescribeSimplePile('Discard', (0, 0), bottom)
        return discard_pile

    # If the draw pile is clicked
    def talon_click(self):
        if not self.piles[TalonPile.DRAW].pile_empty():
            take_cards = self.piles[TalonPile.DRAW].takeCards(1)  # If the pile is not empty, get the top card
            take_cards[0].face_up = True
            self.piles[TalonPile.DISCARD].addCards(take_cards)  # Add the card to stock

        else:  # when the talon is empty, click the stock and all the cards will back to talon
            self.piles[TalonPile.DISCARD].allFaceUp(False)
            all_cards = self.piles[TalonPile.DISCARD].takeAll()
            all_cards.reverse()
            self.piles[TalonPile.DRAW].addCards(all_cards)

    # The action set up to click the talon pile
    def on_click(self, event):
        clicked_pile = self.get_pile(event.pos)

        if not clicked_pile:
            return  # check if on_click was called accidentally
        if not clicked_pile.visible:
            return

        if event.type == MOUSEBUTTONUP and event.button == 1:
            if clicked_pile.name == 'Draw':
                self.talon_click()

        # Discard pile just returns the top card in a pile
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if clicked_pile.name == 'Discard' and not clicked_pile.pile_empty():
                return clicked_pile.takeCards(1)

    # The card which can be moved to the foundation piles by double click
    def double_click(self, event):
        clicked_pile = self.get_pile(event.pos)
        if not clicked_pile:
            return  # make sure on_click was called accidentally
        if not clicked_pile.visible:
            return

        if clicked_pile.name == 'Draw':
            self.talon_click()
        if clicked_pile.name == 'Discard' and not clicked_pile.pile_empty():
            return clicked_pile.takeCards(1)

    # permission for card to move another pile
    @staticmethod
    def valid_move_cards(cards):
        return False


# Tableau field set up
class TableauPile(describe.DescribeTilePile):
    def __init__(self, name, pos, image, init_space, add_space, cards=[]):
        self.pile_setup(cards)
        describe.DescribeTilePile.__init__(self, name, pos, image, init_space, add_space, cards)

    # All but the last card in the pile is face down
    @staticmethod
    def pile_setup(cards):
        for card in cards:
            card.face_up = False
        if cards:
            cards[-1].face_up = True

    # This function flip the top card from face down to face up when that was clicked
    # If no card was clicked, returns -1
    def top_card_clicked(self, pos):
        result = -1
        for i, card in enumerate(self.cards):
            if card.has_position(pos):
                result = i

        return result

    def on_click(self, event):
        if not self.visible:
            return

        # When clicked down, return all the cards including and after the card clicked
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            card_clicked = self.top_card_clicked(event.pos)
            if card_clicked != -1 and self.cards[card_clicked].face_up:
                cards_to_take = self.cardNum() - card_clicked
                return self.takeCards(cards_to_take)

        # If the last card in the pile if face down, an upclick will turn in around
        if event.type == MOUSEBUTTONUP and event.button == 1:
            if not self.pile_empty() and self.cards[-1].has_position(event.pos):
                self.cards[-1].face_up = True

    # Returns the last card in the pile if it is faced up and has been clicked
    def double_click(self, event):
        if not self.visible:
            return

        card_clicked = self.top_card_clicked(event.pos)
        if card_clicked != -1 and self.cards[card_clicked].face_up and card_clicked == self.cardNum() - 1:
            return self.takeCards(1)

    # set up the rule of the where the card can be moved to
    # implicit assumption is that the rest of the program makes sure the order of the cards remains valid
    def valid_move_cards(self, cards):
        # Only a king can be added to a spare tableau pile
        if self.pile_empty():
            if cards[0].get_number() == 13 and self.collision(cards[0]):
                return True
        else:
            ref_card = self.cards[-1]  # The top most card of the pile determines validity
            if not ref_card.face_up:  # Card must be face up for validation
                return False

            if not ref_card.color_match(cards[0]) and ref_card.get_number() == cards[0].get_number() + 1:
                if ref_card.collision(cards[0]):
                    return True

        return False


# Set up the foundation piles playing rules
# Only Aces can be moved to an empty foundation pile and add the track ascended
# The player win the game when all the cards can all move to foundation piles
class FoundationPile(describe.DescribeSimplePile):
    total_cards = 0

    def __init__(self, name, pos, image):
        describe.DescribeSimplePile.__init__(self, name, pos, image)

    # valid_move_cards has to be expended
    # If contact is true, the added card must be in touch with the suit pile
    # This matters because double-click a card can directly move it to a suit pile
    def valid_move_cards(self, cards, contact=True):
        if contact:
            if not self.collision(cards[0]): return False
        if len(cards) != 1: return False

        if self.pile_empty():
            if cards[0].get_number() == 1: return True
            return False

        ref_card = self.cards[-1]
        if ref_card.get_suit() == cards[0].get_suit() and ref_card.get_number() + 1 == cards[0].get_number():
            return True
        return False

    # On click
    def on_click(self, event):
        if not self.visible: return False

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if not self.pile_empty(): return self.takeCards(1)

    def double_click(self, event):
        pass

    # To keep track of the total number of cards in SuitPiles, add and take card function need to be expanded
    def takeCards(self, num):
        cards_taken = super(FoundationPile, self).takeCards(num)
        FoundationPile.total_cards -= num
        return cards_taken

    def addSingle(self, card):
        super(FoundationPile, self).addSingle(card)
        FoundationPile.total_cards += 1


# Move the whole pile which is already ranked in the right order
# It also keeps track of where the cards came from and can return it if necessary
class PileMove(object):
    def __init__(self, name):
        self.name = name
        self.cards = []
        self.source = None

    def addCards(self, cards):
        if self.source or self.cards: raise Exception
        if cards:
            self.cards = cards
            self.source = cards[0].pile

    def hasCards(self):
        if self.cards: return True
        return False

    def clear(self):
        self.cards = []
        self.source = None

    def returnCards(self):
        self.source.addCards(self.cards)
        self.clear()

    # Move the card to the pile (please check if the move if valid first)
    def add_to_pile(self, pile):
        pile.addCards(self.cards)
        self.clear()

    def draw(self, screen):
        for card in self.cards: card.draw(screen)

    def move_position(self, move):
        for card in self.cards: card.move_position(move)
