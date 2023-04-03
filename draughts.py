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
        ctx.fill()

class Board:
    def __init__(self, size):
        self.size = size
        self.pieces = []
        self.rectangleSize = (640/size[0], 480/size[1])
        self.selection = [0, 0, 0]

        for i in range(1, (self.size[0] * self.size[1] // 2) + 1): # i starts at 1
            offset = ((i-1) // (self.size[0]//2) + 1) % 2 + 1 # this is 2 if the row is odd or 1 if it is even
            position = [2*((i-1) % (self.size[0]//2)) + offset, (i-1) // (self.size[0]//2) + 1] # starts at [1,1]
            if i <= (self.size[0] / 2) * (self.size[1] / 2 - 1): # black is at the top
                self.pieces.append(Piece(position, i, -1))
            elif i > (self.size[0] / 2) * (self.size[1] / 2 + 1): # white is at the bottom
                self.pieces.append(Piece(position, i, 1))
            else: # everywhere else there is nothing
                self.pieces.append(Piece(position, i))
    def draw(self, ctx, w, h):
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
            radius = 0.45 * min(rectangleSize[0], rectangleSize[1])

            ctx.set_source_rgb(1, 0, 1)
            ctx.arc(xc, yc, radius, 0, 2 * math.pi)
            ctx.fill()

        # Now we have a board, we render the checkers on top of it
        for piece in self.pieces:
            if piece:
                piece.draw(ctx, rectangleSize)

        # update the rectangleSize so we can use it when clicked
        self.rectangleSize = rectangleSize
    def clicked(self, x, y):
        position = int(x // self.rectangleSize[0]) + 1, int(y // self.rectangleSize[1]) + 1
        # print(f"Click in position {position}")
        if (position[0] + position[1]) % 2 == 1: # this checks if we are in a black square
            i = (position[0]+1)//2 + (position[1]-1)*(self.size[0]//2)
            if self.pieces[i-1].team != 0:
                self.selection = [position[0], position[1], i] # select the piece
                return # and we're done here
            movetext = self.toMovetext(self.selection[2], i)
            self.move(movetext) # try to move the previous selected piece to where we just clicked

            # print(f"Click placed at {i}")

        self.selection = [0, 0, 0] # reset the selection
    def move(self, move):
        if move.find("-") == -1: # can't deal with jumps yet
            return False

        placeStrings = move.split("-")
        start = int(placeStrings[0])
        end = int(placeStrings[1])

        if not (start and end): # if start and end aren't both nonzero then we give up
            return False

        width = self.size[0]//2
        evenRow = ((start-1)//width)%2 # 0 on odd rows and 1 on even rows
        offset = 1 - 2*evenRow # swaps between 1 on the odd rows and -1 on the even ones
        validEnds = [start + width, start - width]
        # If the place is at the edge of the board then it loses a few options
        if start%width != evenRow: # somewhat surprisingly, this works as places begin at 1
            validEnds.append(start + width + offset)
            validEnds.append(start - width + offset)

        if end not in validEnds:
            return False

        self.pieces[end - 1].team = self.pieces[start - 1].team
        self.pieces[start - 1].team = 0
        return True # if we've gotten this far, the move was probably valid
    def toMovetext(self, start, end): # this function won't check whether the move actually makes sense, as that's someone else's job
        # we need some logic to figure out whether this is a short move, otherwise a jump is assumed
        width = self.size[0]//2
        evenRow = ((start-1)//width)%2 # 0 on odd rows and 1 on even rows
        offset = 1 - 2*evenRow # swaps between 1 on the odd rows and -1 on the even ones
        shortEnds = [start + width, start - width]
        # If the place is at the edge of the board then it loses a few options
        if start%width != evenRow: # somewhat surprisingly, this works as places begin at 1
            shortEnds.append(start + width + offset)
            shortEnds.append(start - width + offset)

        if end in shortEnds:
            return f"{start}-{end}"
        else:
            return f"{start}x{end}" # the caller should do something to allow/force players to take more than one piece in a turn
    def validMoves(self):
        width = self.size[0]//2
        maxPlace = len(self.pieces)
        validMoves = []

        for i in range(maxPlace):
            place = i + 1
            team = self.pieces[i].team
            evenRow = ((place-1)//width)%2 # 0 on odd rows and 1 on even rows
            # First, we need to check a move down and to the left
            # This is place + width on an odd row and place + width - 1 on an even row
            target = place + width - evenRow
            if target <= maxPlace and not (target%width == 0 and evenRow == 1): # This checks that down and to the left is not off the left or bottom of the board
                if self.pieces[target - 1].team == 0: # this checks that the piece here is unowned
                    validMoves.append(f"{place}-{target}")
            # Next, we check down and to the right
            # This is place + width + 1 on an odd row and place + width on an even row
            target = place + width + 1 - evenRow
            if target <= maxPlace and not (target%width == 1 and evenrow == 0): # This checks that down and to the right is not off the right or bottom of the board
                if self.pieces[target - 1].team == 0: # this checks that the piece here is unowned
                    validMoves.append(f"{place}-{target}")
            # Now we check up and to the left
            # This is place - width on an odd row and place - width - 1 on an even row
            target = place - width - evenRow
            if target > 0 and not (target%width == 0 and evenRow == 1): # This checks that up and to the left is not off the left or top of the board
                if self.pieces[target - 1].team == 0: # this checks that the piece here is unowned
                    validMoves.append(f"{place}-{target}")
            # Finally, we need check up and to the right
            # This is place - width + 1 on an odd row and place - width on an even row
            target = place - width + 1 - evenRow
            if target > 0 and not (target%width == 1 and evenRow == 0): # This checks that up and to the right is not off the right or top of the board
                if self.pieces[target - 1].team == 0: # this checks that the piece here is unowned
                    validMoves.append(f"{place}-{target}")
    def checkStep(self, start, end, team):
        width = self.size[0]//2
        maxPlace = len(self.pieces)
        evenRow = ((place-1)//width)%2 # 0 on odd rows and 1 on even rows

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
            return 1 # we can land there
        else: # we don't need this else but it might improve readability?
            return 2 # This is an enemy piece, further investigation may be required

board = Board([10, 10])

def clicked(gesture, data, x, y):
    global win
    # print(f"Click recieved at x={x}, y={y}")
    board.clicked(x, y)
    win.da.queue_draw()

def activation(app):
    global win
    win = Gtk.ApplicationWindow(application=app)

    win.mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    win.set_child(win.mainBox)
    win.gameBox = Gtk.Box()
    win.mainBox.append(win.gameBox)

    win.button = Gtk.Button(label="Test")
    win.mainBox.append(win.button)

    win.da = Gtk.DrawingArea()
    win.da.set_hexpand(True)
    win.da.set_vexpand(True)
    win.da.set_draw_func(draw, None)
    # we need to pick up button presses
    click = Gtk.GestureClick.new()
    click.connect("pressed", clicked)
    win.da.add_controller(click)

    win.gameBox.append(win.da)

    win.set_default_size(640, 480)
    win.set_title("Draughts")
    win.present()

def draw(area, ctx, w, h, data):
    board.draw(ctx, w, h)

app = Adw.Application(application_id="org.duckdns.number251.draughts")
app.connect('activate', activation)

app.run(None)



# ================================ Working Out ================================
# note: these calculations only work for even board widths
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
