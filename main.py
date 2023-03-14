import pygame
import sys
from objects import *
from outlook import WinSet
from pygame.locals import *
import random


class DoubleClickFunction:
    def __init__(self):
        self.double_click = pygame.time.Clock()
        self.time = 0  # checking second down click
        self.first_click = True  # check if this is the first click in the double click
        self.second_click = False  # check double click

    # limit the time between the two clicks
    def click_time(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            click_time = self.double_click.tick()  # Check how long since last click
            if not self.first_click:  # If it's the first click, exit function with False
                # check time gap between two clicks
                if click_time > WinSet.double_speed:
                    self.first_click = True
                else:
                    self.time = click_time

        if event.type == MOUSEBUTTONUP and event.button == 1:
            if not self.first_click:  # If it's the second click
                click_time = self.double_click.tick()  # Get time since last click (the second down click)
                self.first_click = True  # The next click will again be first
                if click_time + self.time < WinSet.double_speed:
                    self.second_click = True
                    return True
            else:
                self.first_click = False
        #  double click was detected
        self.second_click = False
        return False


class Main:
    def __init__(self):
        pygame.init()
        random.seed()

        self.screen = self.set_display()
        pygame.display.set_caption("CST8334-GROUP7 SOLITAIRE")
        self.double_click = DoubleClickFunction()  # Double click checker
        self.move_pile = PileMove('PileMove')  # For moving piles

        self.cards = self.loadCards()  # All the cards
        self.piles = self.populatePiles()  # All the piles

    # The display dimensions are calculated given the wanted margins and card dimensions
    @staticmethod
    def set_display():
        x_dim = (WinSet.margin_space * 2) + (WinSet.image_resolution[0] * 7) + (WinSet.start_space * 6)
        y_dim = WinSet.margin_space + (WinSet.image_resolution[1] * 2) + WinSet.row_space
        y_dim += (WinSet.tile_small_space * 6) + (WinSet.tile_large_space * 12)
        return pygame.display.set_mode((x_dim, y_dim))

    # Load the cards (the common card back and the card images)
    @staticmethod
    def loadCards():
        Card.back_loading(WinSet.image_back)
        cards = [Card(x, (0, 0)) for x in WinSet.image_names]
        random.shuffle(cards)
        return cards

    # Place the piles (are reset the FoundationPile win number down to 0)
    def populatePiles(self):
        piles = []
        suit_piles = []
        FoundationPile.total_cards = 0

        marker = 0  # Keeps track of the last card added
        x = WinSet.margin_space  # The x_position of the pile
        y = WinSet.margin_space + WinSet.image_resolution[1] + WinSet.row_space
        for i in range(1, 8):  # Need seven main piles
            pile_name = 'Main' + str(i)
            cards = self.cards[marker: i + marker]  # Each pile position also tells me how many cards it needs
            piles.append(
                TableauPile(pile_name, (x, y), WinSet.image_bottom, WinSet.tile_small_space, WinSet.tile_large_space,
                            cards))

            # The foundation piles are exactly above main piles (starting on the four one)
            if i > 3: suit_piles.append(FoundationPile('Suit' + str(i - 3), (x, WinSet.margin_space), WinSet.image_bottom))

            # tick along x and marker
            x += piles[-1].rect.w + WinSet.start_space
            marker = i + marker

        # Add the start pile
        cards = self.cards[marker: 52]  # The remaining cards
        piles.append(
            TalonPile('Start', (WinSet.margin_space, WinSet.margin_space), WinSet.start_space, WinSet.image_bottom,
                      cards))

        piles.extend(suit_piles)  # The last four piles always must be the suit piles
        return piles

    # simply gets the pile that was clicked (none if no pile was clicked)
    def clicked_pile(self, event):
        for pile in self.piles:
            if pile.has_position(event.pos):
                return pile

    # The basic idea of the game
    def game(self):
        font = pygame.font.SysFont(None, 32)
        start_time = pygame.time.get_ticks()
        prev_time = None

        while True:
            counting_time = pygame.time.get_ticks() - start_time

            # change milliseconds into minutes, seconds, milliseconds
            counting_minutes = str(round(counting_time/120000)).zfill(2)
            counting_seconds = str(round( (counting_time%60000)/1000 )).zfill(2)
            if counting_seconds == '60':
                counting_seconds = '00'

            counting_string = "%s:%s" % (counting_minutes, counting_seconds)

            counting_text = font.render(str(counting_string), True, (255, 255, 255))
            counting_rect = counting_text.get_rect(center = self.screen.get_rect().bottomleft)
            counting_rect.x = counting_rect.x + 50
            counting_rect.y = counting_rect.y - 20

            self.screen.blit(counting_text, counting_rect)
            pygame.display.update(counting_rect)


            if self.winCondition():
                self.move_motion(2)  # Move the piles around randomly if game has been won
                start_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                # Check and store if a double click
                if (event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN) and event.button == 1:
                    self.double_click.click_time(event)

                # Check if the program is quit
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                # Pressing r resets the program
                if event.type == KEYUP and event.key == K_r:
                    self.reset()

                # If the game has been won, reset it with a mouse click
                if self.winCondition():
                    if event.type == MOUSEBUTTONUP and event.button == 1:
                        self.reset()

                # Now for the main meat of the program
                else:
                    if event.type == MOUSEBUTTONUP and event.button == 1:
                        # check card dragging
                        move_pile_full = self.move_pile.hasCards()

                        if move_pile_full:  # If yes
                            # This finds the left most pile where the dropped cards are accepted
                            selected_pile = None
                            for pile in self.piles:
                                if pile.valid_move_cards(self.move_pile.cards):
                                    selected_pile = pile
                                    break

                            # If a valid pile is found, drop the cards there, otherwise return the cards
                            if selected_pile:
                                self.move_pile.add_to_pile(selected_pile)
                            else:
                                self.move_pile.returnCards()

                        # double click event
                        if self.double_click.second_click:
                            self.onDoubleClick(event)

                        # If the move_pile was empty and no double click, just run a simple on_click on the pile
                        if not move_pile_full and not self.double_click.second_click:
                            clicked_pile = self.clicked_pile(event)

                            if clicked_pile:
                                clicked_pile.on_click(event)

                    # If mouse is held down, move those cards to the self.move_pile
                    if event.type == MOUSEBUTTONDOWN and event.button == 1:
                        clicked_pile = self.clicked_pile(event)

                        if clicked_pile:
                            cards_taken = clicked_pile.on_click(event)
                            if cards_taken: self.move_pile.addCards(cards_taken)

                    # if the mouse is moved, move the mouse_pile (if it has cards)
                    if event.type == MOUSEMOTION:
                        if self.move_pile.hasCards(): self.move_pile.move_position(event.rel)

            self.screen.fill((0, 0, 0))
            self.draw()
            pygame.display.flip()

    #  Double click function
    def onDoubleClick(self, event):
        clicked_pile = self.clicked_pile(event)  # Get the clicked pile

        if clicked_pile:
            # double_click always returns only one card
            card_taken = clicked_pile.double_click(event)
            if card_taken:  # If a card is returned (double click was valid)
                no_home = True  # This card right now has no home in the Suit piles
                for pile in self.piles[-4:]:  # Go through the four suit piles
                    # The False ensures that the card_taken does not have to contact the Suit piles
                    if pile.valid_move_cards(card_taken, False):
                        pile.addCards(card_taken)
                        no_home = False
                        break;
                # If no suit pile has been found, return the card to the original pile
                if no_home:
                    card_taken[0].pile.addCards(card_taken)

    # Draw is simple, just draw all the piles
    def draw(self):
        for pile in self.piles:
            pile.draw(self.screen)

        self.move_pile.draw(self.screen)

    def start(self):
        self.game()

    # When all the cards are in the suit pile
    def winCondition(self):
        return FoundationPile.total_cards == len(self.cards)

    # Moves the piles randomly in all directions (the length arguement specifies how hard they move)
    def move_motion(self, length):
        for pile in self.piles:
            x_move = random.randint(-length, length)
            y_move = random.randint(-length, length)
            pile.movePosition((x_move, y_move))

    def reset(self):
        self.cards = self.loadCards()
        self.piles = self.populatePiles()


if __name__ == "__main__":
    g = Main()
    g.start()
