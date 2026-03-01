import "CoreLibs/object"
import "CoreLibs/graphics"
import "CoreLibs/sprites"

local gfx = playdate.graphics

local GRID = 6
-- Make board fill vertical space more aggressively on 400x240 screen
local TILE = 34
local BOARD_PX = GRID * TILE
local OX = math.floor((400 - BOARD_PX) / 2)
local OY = 24
local TYPES = 5

local board = {}
local cx, cy = 1, 1
local selected = nil
local blink = 0

local function randTile()
  return math.random(1, TYPES)
end

local function colorFor(v)
  -- grayscale shades for prototype
  return gfx.kColorBlack, (v * 35)
end

local function initBoard()
  for y=1,GRID do
    board[y] = {}
    for x=1,GRID do
      board[y][x] = randTile()
    end
  end
end

local function swap(a,b,c,d)
  board[b][a], board[d][c] = board[d][c], board[b][a]
end

local function findMatches()
  local mark = {}
  for y=1,GRID do
    mark[y] = {}
    for x=1,GRID do mark[y][x] = false end
  end

  -- rows
  for y=1,GRID do
    local runVal, runStart, runLen = board[y][1], 1, 1
    for x=2,GRID+1 do
      local v = (x<=GRID) and board[y][x] or -1
      if v == runVal then
        runLen += 1
      else
        if runLen >= 3 then
          for k=runStart, runStart+runLen-1 do mark[y][k] = true end
        end
        runVal, runStart, runLen = v, x, 1
      end
    end
  end

  -- cols
  for x=1,GRID do
    local runVal, runStart, runLen = board[1][x], 1, 1
    for y=2,GRID+1 do
      local v = (y<=GRID) and board[y][x] or -1
      if v == runVal then
        runLen += 1
      else
        if runLen >= 3 then
          for k=runStart, runStart+runLen-1 do mark[k][x] = true end
        end
        runVal, runStart, runLen = v, y, 1
      end
    end
  end

  return mark
end

local function clearAndDrop(mark)
  local any = false
  for y=1,GRID do
    for x=1,GRID do
      if mark[y][x] then
        board[y][x] = 0
        any = true
      end
    end
  end
  if not any then return false end

  for x=1,GRID do
    local write = GRID
    for y=GRID,1,-1 do
      if board[y][x] ~= 0 then
        board[write][x] = board[y][x]
        write -= 1
      end
    end
    for y=write,1,-1 do
      board[y][x] = randTile()
    end
  end
  return true
end

local function tryResolve()
  while true do
    local mark = findMatches()
    if not clearAndDrop(mark) then break end
  end
end

local function drawBoard()
  gfx.clear(gfx.kColorWhite)
  gfx.drawText("Match-3 Proto", 12, 6)
  gfx.drawText("D-pad move  A select/swap", 12, 20)

  for y=1,GRID do
    for x=1,GRID do
      local _, shade = colorFor(board[y][x])
      gfx.setColor(gfx.kColorBlack)
      gfx.drawRect(OX + (x-1)*TILE, OY + (y-1)*TILE, TILE, TILE)
      gfx.setDitherPattern(math.min(1, shade/255), gfx.image.kDitherTypeBayer8x8)
      gfx.fillRect(OX + (x-1)*TILE + 2, OY + (y-1)*TILE + 2, TILE-4, TILE-4)
      gfx.setDitherPattern(1, gfx.image.kDitherTypeBayer8x8)
    end
  end

  local px = OX + (cx-1)*TILE
  local py = OY + (cy-1)*TILE

  -- Highly visible cursor: pulsing double-border + corner ticks
  local pulseOn = (blink % 30) < 15
  gfx.setLineWidth(3)
  gfx.setColor(gfx.kColorBlack)
  gfx.drawRect(px, py, TILE, TILE)
  if pulseOn then
    gfx.setLineWidth(1)
    gfx.drawRect(px+3, py+3, TILE-6, TILE-6)
  end

  -- corner ticks for visibility on any tile shade
  local t = 6
  gfx.drawLine(px, py, px+t, py)
  gfx.drawLine(px, py, px, py+t)
  gfx.drawLine(px+TILE, py, px+TILE-t, py)
  gfx.drawLine(px+TILE, py, px+TILE, py+t)
  gfx.drawLine(px, py+TILE, px+t, py+TILE)
  gfx.drawLine(px, py+TILE, px, py+TILE-t)
  gfx.drawLine(px+TILE, py+TILE, px+TILE-t, py+TILE)
  gfx.drawLine(px+TILE, py+TILE, px+TILE, py+TILE-t)

  if selected then
    local sx = OX + (selected.x-1)*TILE
    local sy = OY + (selected.y-1)*TILE
    gfx.setLineWidth(2)
    gfx.drawRect(sx+4, sy+4, TILE-8, TILE-8)
    gfx.drawText("SELECTED", 300, 8)
  end
end

local function adjacent(ax,ay,bx,by)
  return math.abs(ax-bx) + math.abs(ay-by) == 1
end

function playdate.update()
  blink += 1
  if playdate.buttonJustPressed(playdate.kButtonLeft) then cx = math.max(1, cx-1) end
  if playdate.buttonJustPressed(playdate.kButtonRight) then cx = math.min(GRID, cx+1) end
  if playdate.buttonJustPressed(playdate.kButtonUp) then cy = math.max(1, cy-1) end
  if playdate.buttonJustPressed(playdate.kButtonDown) then cy = math.min(GRID, cy+1) end

  if playdate.buttonJustPressed(playdate.kButtonA) then
    if not selected then
      selected = {x=cx, y=cy}
    else
      if adjacent(selected.x, selected.y, cx, cy) then
        swap(selected.x, selected.y, cx, cy)
        local mark = findMatches()
        if clearAndDrop(mark) then
          tryResolve()
        else
          -- invalid swap, revert
          swap(selected.x, selected.y, cx, cy)
        end
      end
      selected = nil
    end
  end

  drawBoard()
end

math.randomseed(playdate.getSecondsSinceEpoch())
initBoard()
tryResolve()
