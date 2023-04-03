#!/usr/bin/env lua

local board = {width = 6/2, height = 6}

io.write("digraph draughts {\n")

for y=0, board.height-2 do -- first row is 0, stop 1 before the end as each row has nodes for the next
    for x=1, board.width do -- first column is 1
        local i = x + y*board.width
        local offset = 1 - 2*(y % 2) -- y mod 2 is 0 if y is even, 1 if it's odd
        if x + offset <= board.width and x + offset >= 1 then -- this makes sure the second point is on the board
            io.write(string.format("%d -> {%d %d}\n", i, i+board.width, i+board.width+offset))
        else
            io.write(string.format("%d -> %d\n", i, i+board.width))
        end
    end

    io.write("\n")
end
io.write("}\n")
