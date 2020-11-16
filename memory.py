#!/usr/bin/python3
"""Memory puzzle game.

Based on the Pygame book by Al Sweigart.
The game board is a grid of boxes, each hiding a random icon,
defined by a shape and a color.
Click a box to reveal an icon, and try to find the matching icon.
If succcessful, the icons stay revealed, otherwise they are hidden
again. Reveal all icons to win.

"""

import sys
import random
import logging
import pygame
from pygame.locals import *

FPS = 30
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
REVEALSPEED = 5
BOXSIZE = 40
ICONSIZE = 30
GAPSIZE = 10
BOARDWIDTH = 10
BOARDHEIGHT = 7
assert (BOARDWIDTH * BOARDHEIGHT) % 2 == 0

XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * (BOXSIZE + GAPSIZE))) / 2)
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * (BOXSIZE + GAPSIZE))) / 2)

BGCOLOR = pygame.Color('navy')
LIGHTBGCOLOR = pygame.Color('grey')
BOXCOLOR = pygame.Color('white')
HIGHLIGHTCOLOR = pygame.Color('blue')

ALLCOLORS = (pygame.Color('red'),
             pygame.Color('green'),
             pygame.Color('blue'),
             pygame.Color('yellow'),
             pygame.Color('orange'),
             pygame.Color('purple'),
             pygame.Color('cyan'))
ALLSHAPES = ('donut',
             'square',
             'diamond',
             'triangle',
             'circle')
assert len(ALLCOLORS) * len(ALLSHAPES) * 2 >= BOARDWIDTH * BOARDHEIGHT


def createBoard() -> tuple:
    board = getRandomizedBoard(BOARDWIDTH, BOARDHEIGHT)
    revealed = generateRevealedBoxesData(False, BOARDWIDTH, BOARDHEIGHT)
    pygame.time.wait(500)
    startGameAnimation(board)
    return (board, revealed)


def main() -> None:
    """Main game loop"""
    global FPSCLOCK
    global DISPLAYSURF

    pygame.init()
    pygame.display.set_caption('Memory Puzzle!')

    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

    mousePos = (0, 0)
    selection = []
    mainBoard, revealedBoxes = createBoard()

    while True:
        mouseClicked = False
        drawBoard(mainBoard, revealedBoxes)

        for event in pygame.event.get():
            if event.type == MOUSEMOTION:
                mousePos = event.pos
            elif event.type == MOUSEBUTTONUP:
                mousePos = event.pos
                mouseClicked = True
            elif event.type == QUIT:
                pygame.quit()
                sys.exit()

        doBoxHighlight(revealedBoxes, mousePos)
        if mouseClicked:
            handleClick(mainBoard, revealedBoxes, mousePos, selection)

        if hasWon(revealedBoxes):
            gameWonAnimation(mainBoard)
            pygame.time.wait(2000)
            mainBoard, revealedBoxes = createBoard()

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def doBoxHighlight(revealed: list, mousePos: tuple) -> None:
    box = getBoxCell(mousePos)
    if box and not iconVisible(revealed, box):
        drawHighlightBox(box)


def handleClick(board: list, revealed: list,
                mousePos: tuple, selection: list) -> None:
    box = getBoxCell(mousePos)
    if box and box not in selection:
        selection.append(box)
        setIconVisible(revealed, box, True)
        revealBoxesAnimation(board, [box])
        logging.debug('Selection:' + str(selection))
        if len(selection) > 1:
            icon1 = getShapeAndColor(board, selection[0])
            icon2 = getShapeAndColor(board, selection[1])
            if icon1 == icon2:
                logging.debug('Match')
            else:
                logging.debug('Mismatch')
                pygame.time.wait(1000)
                coverBoxesAnimation(board, selection)
                for s in selection:
                    setIconVisible(revealed, s, False)
            selection.clear()


def getRandomizedBoard(width: int, height: int) -> list:
    """Generate a randomized game board with the given dimensions.
    Each entry in the board is an icon (shape, color)"""
    allIcons = [(shape, color) for shape in ALLSHAPES for color in ALLCOLORS]
    random.shuffle(allIcons)

    numIcons = int(width * height / 2)
    icons = allIcons[:numIcons] * 2  # 2 of each icon
    random.shuffle(icons)

    return [[icons.pop() for y in range(height)]
            for x in range(width)]


def splitIntoGroupsOf(size: int, items: list) -> list:
    """Split a list into sublists of the given sizen"""
    return [[item for item in items[start:start+size]]
            for start in range(0, len(items), size)]


def startGameAnimation(board: list) -> None:
    """Reveal all boxes briefly, in groups, as a hint"""
    coveredBoxes = generateRevealedBoxesData(False,
                                             BOARDWIDTH,
                                             BOARDHEIGHT)
    boxes = [(i, j) for i in range(BOARDWIDTH)
             for j in range(BOARDHEIGHT)]
    random.shuffle(boxes)
    boxGroups = splitIntoGroupsOf(8, boxes)
    drawBoard(board, coveredBoxes)
    for group in boxGroups:
        revealBoxesAnimation(board, group)
        coverBoxesAnimation(board, group)


def gameWonAnimation(board: list) -> None:
    """Show game won animation"""
    coveredBoxes = generateRevealedBoxesData(True,
                                             BOARDWIDTH,
                                             BOARDHEIGHT)
    colors = [LIGHTBGCOLOR, BGCOLOR] * 6
    logging.debug(colors)
    for color in colors:
        drawBoard(board, coveredBoxes, color)
        pygame.display.update()
        pygame.time.wait(300)


def drawBoxCovers(board: list, boxes: list, coverage: int) -> None:
    """Draw boxes partially covered by a rectangle of width 'coverage'"""
    for box in boxes:
        pygame.draw.rect(DISPLAYSURF, BGCOLOR, getBoxRect(box))
        drawIcon(board, box)
        if coverage > 0:
            cover = pygame.Rect((0, 0), (coverage, BOXSIZE))
            cover.center = getBoxRect(box).center
            pygame.draw.rect(DISPLAYSURF, BOXCOLOR, cover)
    pygame.display.update()
    FPSCLOCK.tick(FPS)


def revealBoxesAnimation(board: list, group: list) -> None:
    """Show the reveal animation for the given group of boxes"""
    for coverage in range(BOXSIZE, -REVEALSPEED - 1, -REVEALSPEED):
        drawBoxCovers(board, group, coverage)


def coverBoxesAnimation(board: list, group: list) -> None:
    """Show the cover animation for the given group of boxes"""
    for coverage in range(0, BOXSIZE + REVEALSPEED, REVEALSPEED):
        drawBoxCovers(board, group, coverage)


def drawHighlightBox(box: tuple) -> None:
    rect = pygame.Rect((0, 0), (BOXSIZE + 10, BOXSIZE + 10))
    rect.center = getBoxRect(box).center
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, rect, width=4)


def generateRevealedBoxesData(revealed: bool,
                              width: int, height: int) -> list:
    """Generate a list with the given dimensions, initialized to 'revealed'"""
    return [[revealed] * height for x in range(width)]


def getBoxPos(box: tuple) -> tuple:
    """For a box (i, j) returns the position in pixels"""
    return (box[0] * (BOXSIZE + GAPSIZE) + XMARGIN,
            box[1] * (BOXSIZE + GAPSIZE) + YMARGIN)


def getBoxRect(box: tuple) -> Rect:
    """For a box (i, j) returns a Rect"""
    return pygame.Rect(getBoxPos(box), (BOXSIZE, BOXSIZE))


def getBoxCell(pos: tuple) -> tuple:
    """For a position (x, y) in pixels, returns a box (i, j)"""
    for box in ((i, j) for i in range(BOARDWIDTH) for j in range(BOARDHEIGHT)):
        if getBoxRect(box).collidepoint(pos):
            return box
    return None


def getShapeAndColor(board: list, box: tuple) -> tuple:
    """Returns the icon (shape, color) corresponding to box (i, j)
    from the provided board"""
    return board[box[0]][box[1]]


def drawDonut(color: tuple, box: tuple) -> None:
    """Draw the donut icon with the given color at box (i, j)"""
    pygame.draw.circle(DISPLAYSURF,
                       color,
                       getBoxRect(box).center,
                       ICONSIZE / 2,
                       width=5)


def drawSquare(color: tuple, box: tuple) -> None:
    """Draw the square icon with the given color at box (i, j)"""
    rect = pygame.Rect((0, 0), (ICONSIZE, ICONSIZE))
    rect.center = getBoxRect(box).center
    pygame.draw.rect(DISPLAYSURF, color, rect)


def drawDiamond(color: tuple, box: tuple) -> None:
    """Draw the diamond icon with the given color at box (i, j)"""
    rect = pygame.Rect((0, 0), (ICONSIZE, ICONSIZE))
    rect.center = getBoxRect(box).center
    pygame.draw.polygon(DISPLAYSURF,
                        color,
                        ((rect.left, rect.center[1]),
                         (rect.center[0], rect.bottom),
                         (rect.right, rect.center[1]),
                         (rect.center[0], rect.top)))


def drawTriangle(color: tuple, box: tuple) -> None:
    """Draw the triangle icon with the given color at box (i, j)"""
    rect = pygame.Rect((0, 0), (ICONSIZE, ICONSIZE))
    rect.center = getBoxRect(box).center
    pygame.draw.polygon(DISPLAYSURF,
                        color,
                        ((rect.left, rect.bottom),
                         (rect.right, rect.bottom),
                         (rect.center[0], rect.top)))


def drawCircle(color: tuple, box: tuple) -> None:
    """Draw the circle icon with the given color at box (i, j)"""
    rect = pygame.Rect((0, 0), (ICONSIZE, ICONSIZE))
    rect.center = getBoxRect(box).center
    pygame.draw.ellipse(DISPLAYSURF, color, rect)


def drawIcon(board: list, box: tuple) -> None:
    """Draw the icon corresponding to box (i, j) from the provided board"""
    shape, color = getShapeAndColor(board, box)
    drawFunc = {'donut': drawDonut,
                'square': drawSquare,
                'diamond': drawDiamond,
                'triangle': drawTriangle,
                'circle': drawCircle}
    drawFunc[shape](color, box)


def setIconVisible(revealed: list, box: tuple, visible: bool) -> None:
    revealed[box[0]][box[1]] = visible


def iconVisible(revealed: list, box: tuple) -> bool:
    return revealed[box[0]][box[1]]


def drawBoard(board: list, revealed: list, color=BGCOLOR) -> None:
    """Draw the game board, using the revealed mask to show/hide icons"""
    DISPLAYSURF.fill(color)
    for box in ((i, j) for i in range(BOARDWIDTH) for j in range(BOARDHEIGHT)):
        if iconVisible(revealed, box):
            drawIcon(board, box)
        else:
            pygame.draw.rect(DISPLAYSURF, BOXCOLOR, getBoxRect(box))


def hasWon(revealed: list) -> bool:
    """Returns True if all boxes are revealed"""
    for col in revealed:
        if False in col:
            return False
    return True


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    main()
