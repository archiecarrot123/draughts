#!/usr/bin/env python3

import math

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class Piece:
    def __init__(self, position, place, team=0, majesty=False):
        self.team = team # A team of -1 means black, 0 means none, and 1 means white
        self.position = position # the position as co-ordinates (so the piece can be drawn correctly)
        self.place = place # the place as a number, for move-checking and array-access operations
        self.majesty = majesty # True if the piece is a king/dame, false if man/pawn

        # print(f"position ([x, y]): {self.position}, place (n): {self.place}")
    def draw(self, ctx, size):
        if self.team == 0:
            return

        xc = (self.position[0] - 0.5) * size[0]
        yc = (self.position[1] - 0.5) * size[1]
        radius = 0.4 * min(size[0], size[1])

        if self.team == -1:
            ctx.set_source_rgb(0.5, 0, 0)
        elif self.team == 1:
            ctx.set_source_rgb(1, 1, 0.5)
        ctx.arc(xc, yc, radius, 0, 2 * math.pi)
        ctx.fill() # fill in the circle
        # now we need to draw the circles around them
        ctx.set_source_rgb(0.5, 0.5, 0) # a sort of dark yellow
        ctx.set_line_width(0.004*radius**2 + 0.07*radius) # strange quadrilateral i made up to scale the radius
        ctx.arc(xc, yc, radius, 0, 2 * math.pi)
        ctx.stroke()
        if self.majesty:
            ctx.set_line_width(0.00256*radius**2 + 0.056*radius)
            ctx.arc(xc, yc, radius * 0.8 - 0.004*radius**2, 0, 2 * math.pi)
            ctx.stroke()

class Board:
    def __init__(self, size):
        self.size = size
        self.pieces = []
        self.rectangleSize = (640/size[0], 480/size[1])
        self.selection = [0, 0, 0]
        self.turnLabel = None # this is how we might tell the players whose turn it is
        self.moveList = None # this is how we can tell the player what moves they can make, and allow keyboard play
        self.currentTeam = 1

        for i in range(1, (self.size[0] * self.size[1] // 2) + 1): # i starts at 1
            offset = ((i-1) // (self.size[0]//2) + 1) % 2 + 1 # this is 2 if the row is odd or 1 if it is even
            position = [2*((i-1) % (self.size[0]//2)) + offset, (i-1) // (self.size[0]//2) + 1] # starts at [1,1]
            if i <= (self.size[0] / 2) * (self.size[1] / 2 - 1): # black is at the top
                self.pieces.append(Piece(position, i, -1))
            elif i > (self.size[0] / 2) * (self.size[1] / 2 + 1): # white is at the bottom
                self.pieces.append(Piece(position, i, 1))
            else: # everywhere else there is nothing
                self.pieces.append(Piece(position, i))

        self.validMoves = self.findValidMoves() # HOW did i not realise i needed to put this last?

    def draw(self, ctx, w, h): # this function draws the board and everything on it
        """draws the board and everything on it"""
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()

        tileCounter = 1
        rectangleSize = w/self.size[0], h/self.size[1]
        textSize = min(rectangleSize[0]/4, rectangleSize[1]*2/3)
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                if (x+y) % 2 == 0:
                    ctx.set_source_rgb(1, 1, 1)
                    ctx.rectangle(x*rectangleSize[0], y*rectangleSize[1], rectangleSize[0], rectangleSize[1])
                    ctx.fill()
                else:
                    ctx.set_source_rgb(0, 0.5, 0.5)
                    ctx.select_font_face('Sans')
                    ctx.set_font_size(textSize)
                    ctx.move_to(x*rectangleSize[0], (y+1)*rectangleSize[1])
                    ctx.show_text(str(tileCounter))
                    tileCounter += 1

        # We need to draw a circle around the selected piece before the piece is drawn
        if self.selection[2]:
            xc = (self.selection[0] - 0.5) * rectangleSize[0]
            yc = (self.selection[1] - 0.5) * rectangleSize[1]
            radius = 0.48 * min(rectangleSize[0], rectangleSize[1])

            ctx.set_source_rgb(1, 0, 1)
            ctx.arc(xc, yc, radius, 0, 2 * math.pi)
            ctx.fill()

        # Now we have a board, we render the checkers on top of it
        for piece in self.pieces:
            if piece:
                piece.draw(ctx, rectangleSize)

        # update the rectangleSize so we can use it when clicked
        self.rectangleSize = rectangleSize

    def clicked(self, x, y): # this function is responsible for handling clicks (obviously)
        """responsible for handling clicks"""
        position = int(x // self.rectangleSize[0]) + 1, int(y // self.rectangleSize[1]) + 1
        # print(f"Click in position {position}")
        if (position[0] + position[1]) % 2 == 1: # this checks if we are in a black square
            i = (position[0]+1)//2 + (position[1]-1)*(self.size[0]//2)
            if (team := self.pieces[i-1].team): # check that there is a piece there; NOTE the walrus operator (:=) returns the assigned value
                if team == self.currentTeam: # only allow selection of a piece on our team
                    self.selection = [position[0], position[1], i] # select the piece
                return # even if we couldn't select it we're done here
            movetext = self.toMovetext(self.selection[2], i)
            if movetext in self.validMoves:
                self.move(movetext) # try to move the previously selected piece to where we just clicked

            # print(f"Click placed at {i}")

        self.selection = [0, 0, 0] # reset the selection

    def move(self, move): # this function just moves the piece and performs any takes; it appears to be finished and should be able to deal with multiple jumps
        """moves the piece and does takes, the move must be in long notation; can't deal with flying jumps yet"""
        if move.find("-") != -1: # This is the code for steps
            placeStrings = move.split("-")
            if len(placeStrings) != 2: # just sanity check, make sure we're not getting something stupid
                return False

            start = int(placeStrings[0])
            end = int(placeStrings[1])
        elif move.find("x") != -1: # Here we deal with jumps
            placeStrings = move.split("x")
            if len(placeStrings) < 2: # make sure there is at least a beginning and an end
                return False

            for i in range(len(placeStrings) - 1): # the piece stops on the last place so we don't need to do anything at that point
                start = int(placeStrings[i])
                end = int(placeStrings[i+1])

                width = self.size[0]//2
                evenRow = ((start-1)//width)%2 # 0 on odd rows and 1 on even rows
                offset = 1 - 2*evenRow # swaps between 1 on the odd rows and -1 on the even ones

                middle = (start + end + offset)//2 # it's just the average of the start and end, plus half the offset (wacky magic panacea value)
                self.pieces[middle - 1].team = 0 # KILL IT!!!
                self.pieces[middle - 1].majesty = False # if it's dead it's no longer a king
            # we move the piece at the end, to save a little time
            start = int(placeStrings[0])
            end = int(placeStrings[len(placeStrings) - 1])
        else:
            return False

        # this code was the same so i moved it
        team = self.pieces[start - 1].team
        self.pieces[end - 1].team = team
        self.pieces[start - 1].team = 0
        # move majesty as well
        self.pieces[end - 1].majesty = self.pieces[start - 1].majesty
        self.pieces[start - 1].majesty = False

        self.currentTeam = -self.currentTeam # swap the team, as a move has been made
        self.validMoves = self.findValidMoves() # update the list of valid moves

        if self.currentTeam == 1: # this feels a bit extreme but whatever
            teamName = "white"
        else:
            teamName = "black"
        if self.turnLabel: # just make sure that it exists
            self.turnLabel.set_label(f"It is {teamName}'s turn") # we need to tell the player whose turn it is
        if self.moveList:
            length = self.moveList.get_n_items()
            self.moveList.splice(0, length, self.validMoves)

        if (end <= self.size[0]//2 and team > 0) or (end > (self.size[0]//2)*(self.size[1]-1) and team < 0): # if the piece is at the top and white or at the bottom and black
            self.pieces[end - 1].majesty = True # make the piece a king

        print(move)
        if len(self.validMoves) == 0: # if there are no moves left you lose
            if self.currentTeam == 1:
                self.turnLabel.set_label("Black wins!")
            else:
                self.turnLabel.set_label("White wins!")
        return True

    def toMovetext(self, start, end): # this function won't check whether the move actually makes sense, as that's someone else's job
        """converts a start and end point to movetext for the clicked function"""
        # we need some logic to figure out whether this is a short move, otherwise a jump is assumed
        width = self.size[0]//2
        evenRow = ((start-1)//width)%2 # 0 on odd rows and 1 on even rows
        offset = 1 - 2*evenRow # swaps between 1 on the odd rows and -1 on the even ones
        stepEnds = [start + width, start - width]
        # If the place is at the edge of the board then it loses a few options
        if start%width != evenRow: # somewhat surprisingly, this works as places begin at 1
            stepEnds.append(start + width + offset)
            stepEnds.append(start - width + offset)

        if end in stepEnds:
            return f"{start}-{end}"
        else:
            return f"{start}x{end}" # the caller should do something to allow/force players to take more than one piece in a turn

    def findValidMoves(self): # this function returns an array of the valid moves
        """returns an array of valid moves this turn in long notation"""
        width = self.size[0]//2
        maxPlace = len(self.pieces)
        threshold = 0
        validMoves = []

        for i in range(maxPlace):
            place = i + 1
            team = self.pieces[i].team

            if team != self.currentTeam:
                continue
            # there was a bunch of repetative code here before but the function fixes this
            for j in range(4): # check all four directions
                newThreshold = 0
                newMoves = []
                newThreshold, *newMoves = self.findStep(place, j, team, threshold, self.pieces[i].majesty, exclusion = []) # find the moves in the direction we're checking
                if newThreshold > threshold: # if we've found more important moves than any we have
                    threshold = newThreshold # require new moves to be at least as important
                    validMoves = [] # clear the old, unimportant moves
                validMoves.extend(newMoves) # add the new moves; NOTE we use extend here instead of append because we're adding the contents of the list

        return validMoves # I don't know how I forgot this the first time

    def checkStep(self, start, end, team, backwards = False): # this function returns 0 if the position is unreachable or contains a piece on team team, 1 if the position is free (a piece can land there), and 2 if it contains a piece on the opposite team
        """returns 0 if the position is unreachable or contains a piece on team team, 1 if the position is free (a piece can land there), and 2 if it contains a piece on the opposite team"""
        width = self.size[0]//2
        maxPlace = len(self.pieces)
        evenRow = ((start-1)//width)%2 # 0 on odd rows and 1 on even rows

        if end < 1 or end > maxPlace: # if there isn't a place there then we obviously can't go there
            return 0 # 0 means that we can't go there
        if self.pieces[end-1].team == team: # we can't move on top of or over our own piece
            return 0
        # here's some bizzare logic from an earlier function that works in a confusing manner to find the valid places
        offset = 1 - 2*evenRow # swaps between 1 on the odd rows and -1 on the even ones
        shortEnds = [start + width, start - width]
        # If the place is at the edge of the board then it loses a few options
        if start%width != evenRow: # somewhat surprisingly, this works as places begin at 1
            shortEnds.append(start + width + offset)
            shortEnds.append(start - width + offset)

        if end not in shortEnds:
            return 0 # we can't move there, as it's not adjacent to our piece

        if self.pieces[end-1].team == 0: # this checks if the spot is empty
            if not backwards and team*end > team*start: # white men can't step to a spot with a larger number, multiplying by a negative effectively inverts the >
                return 0
            else:
                return 1 # we can land there
        else: # we don't need this else but it might improve readability?
            return 2 # This is an enemy piece, further investigation may be required

    def findStep(self, place, direction, team, threshold = 0, majesty = False, landOnly = False, exclusion = []): # this function will return its threshold (how many times it jumps) and an array of the move(s) it has found, unless landOnly is True, in which case it will return 0 or the place it can land on; exclusion is so that pieces can't jump the same piece twice
        """returns an array of its threshold (how many times it jumps) and the move(s) it has found, unless landOnly is True, in which case it will return 0 or the place it can land on"""
        width = self.size[0]//2
        evenRow = ((place-1)//width)%2 # 0 on odd rows and 1 on even rows

        directions = [ # an array for where things go, purely because it's easer than a bunch of elifs
            place + width - evenRow,
            place + width + 1 - evenRow,
            place - width - evenRow,
            place - width + 1 - evenRow
        ]

        # First, we need to check a move down and to the left
        # This is place + width on an odd row and place + width - 1 on an even row
        target = directions[direction]
        stepability = self.checkStep(place, target, team, majesty or landOnly) # if we are jumping we can move backwards
        if stepability == 1: # check if we can land there
            if landOnly:
                return target
            elif threshold == 0: # only bother returning a step if we aren't jumping anywhere
                return [0, f"{place}-{target}"]
            else:
                return [0]
        elif stepability == 2 and not landOnly and target not in exclusion: # If this is true, there is an enemy piece there
            # We need to check if we can land behind and take it
            if (behind := self.findStep(target, direction, team, threshold - 1, majesty, True)): # we check if we can land in the place behind
                foundMoves = [max(threshold, 1)]
                if threshold <= 1:
                    threshold = 1 # we've found a move of depth 1
                    foundMoves.append(f"{place}x{behind}") # this is the move we've just found
                    exclusion.append(target) # we can't go to target from here

                # this is similar to what is done in findValidMoves
                for i in range(4): # check all four directions
                    if i == 3 - direction: # except where we came from
                        continue
                    newThreshold = 0
                    newMoves = []
                    newThreshold, *newMoves = self.findStep(behind, i, team, max(threshold - 1, 1), exclusion = exclusion.copy()) # threshold is reduced as we're checking deeper, actually that's really confusing but we need to make sure it's not less than 1, also this function should return the deepest it's found not the thing it got in i need to fix that; pass on exclusion so we don't go over the same piece
                    # oh my god how did i not realise that it needed to start from behind not place ;(
                    if newThreshold + 1 > threshold: # if we've found more important moves than any we have
                        threshold = newThreshold + 1 # require new moves to be at least as important
                        foundMoves = [threshold] # clear the old, unimportant moves
                    for i in range(len(newMoves)): # we need to add the start to the beginning of these
                        newMoves[i] = f"{place}x{newMoves[i]}"
                    foundMoves.extend(newMoves) # add the new moves; NOTE we use extend here instead of append because we're adding the contents of the list
                return foundMoves # we return the moves

        if landOnly: # if everything falls through then we return nothing
            return 0
        else:
            return [0] # we found nothing, that's completely unimportant so we return [0] NOT [threshold]


board = Board([10, 10])

def clicked(gesture, data, x, y): # this function gets the board to handle the click
    global win
    # print(f"Click recieved at x={x}, y={y}")
    board.clicked(x, y)
    win.da.queue_draw()

def chooseMove(button): # basically a simplified version of Board.clicked
    movetext = win.moveChooser.get_selected_item().get_string() # get the string from the selected StringObject
    if movetext in board.validMoves: # sanity check
        board.move(movetext) # make the move
        win.da.queue_draw() # we need to refresh the image

def activation(app): # this function gets called when the app is activated
    global win
    win = Gtk.ApplicationWindow(application=app)

    win.grid = Gtk.Grid() # create a grid
    win.set_child(win.grid) # add the grid to the window

    # win.button = Gtk.Button(label="Test")
    # win.grid.attach(win.button, 1, 0, 1, 1) # https://docs.gtk.org/gtk4/method.Grid.attach.html

    # create the drawing area to draw the game in
    win.da = Gtk.DrawingArea()
    win.da.set_hexpand(True)
    win.da.set_vexpand(True)
    win.da.set_draw_func(draw, None)
    # the area needs to pick up button presses
    click = Gtk.GestureClick.new()
    click.connect("pressed", clicked) # when the mouse button is pressed on the game window we need to call clicked
    win.da.add_controller(click)

    # instead of putting the drawing area directly in the box, we ensure it remains square
    win.aspectFrame = Gtk.AspectFrame()
    win.aspectFrame.set_child(win.da)
    win.grid.attach(win.aspectFrame, 0, 0, 1, 1) # column 0, row 0

    # We need some way of telling the player whose turn it is
    board.turnLabel = Gtk.Label(label="It is white's turn")
    win.grid.attach(board.turnLabel, 0, 1, 1, 1) # column 0, row 1
    # A way to see what moves we can make would be nice
    board.moveList = Gtk.StringList.new(board.validMoves) # create a GObject string list for the valid moves to be copied into
    win.moveChooser = Gtk.DropDown(model=board.moveList) # create a DropDown that uses the string list we just created
    win.grid.attach(win.moveChooser, 1, 1, 1, 1) # column 1, row 1
    # The player should be able to press a button to make the move
    win.moveButton = Gtk.Button(label="Move!")
    win.moveButton.connect('clicked', chooseMove) # when the button is clicked we need to call chooseMove
    win.grid.attach(win.moveButton, 2, 1, 1, 1) # column 2, row 1


    win.set_default_size(640, 480)
    win.set_title("Draughts")
    win.present()

def draw(area, ctx, w, h, data):
    board.draw(ctx, w, h)

app = Adw.Application(application_id="org.duckdns.number251.draughts")
app.connect('activate', activation) # call activation when the app is ready to activate

app.run(None)



# ================================ Working Out ================================
# NOTE: these calculations only work for even board widths
# i = x - 1 + (y-1)*(board.width/2)
# i - (y-1)*(board.width/2) = x - 1
# i % (board.width/2) = x - 1; as x - 1 < board.width/2 and y-1 is an integer
# (i % (board.width/2)) + 1 = x

# i - x + 1 = (y-1)*(board.width/2)
# i - (i % (board.width/2)) = (y-1)*board.width
# (i - (i % board.width/2))/(board.width/2) = y - 1
# i // (board.width/2) = y - 1
# i // (board.width/2) + 1 = y

# ---- some logic for checking if the place is at the edge of the board
# if 1 <= (start - 1)%width + 1 + offset <= width:
# if 0 - offset <= (start - 1)%width < width - offset: # if offset is positive then the <= is always true, if negative then the < is always true
# if (offset > 0 and (start - 1)%width < width - offset) or (offset < 0 and 0 - offset <= (start - 1)%width): # when offset is positive it is 1, when negative it is -1
# if (offset > 0 and (start - 1)%width < width - 1) or (offset < 0 and 1 <= (start - 1)%width): # (start - 1)%width can only have one value < 1 and only one >= width - 1
# if (offset > 0 and (start - 1)%width != width - 1) or (offset < 0 and (start - 1)%width != 0): # can do some weird maths here because != works the same as ==
# if (offset > 0 and start%width != 0) or (offset < 0 and start%width != 1): # use evenRow (which I just added)
# if (start%width != evenRow) or (start%width != evenRow): # oh look they're the same
# if start%width != evenRow: # somewhat surprisingly, this works as places begin at 1
