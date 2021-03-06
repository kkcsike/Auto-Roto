from tkinter import *
import os
import ctypes
import edge_detection
from PIL import Image
from PIL import ImageTk
from PIL import ImageOps
from PIL import ImageDraw
from tkinter import filedialog
from tkinter import messagebox
import imghdr
from collections import *

################ DRAW ################

def showEdges(canvas):
    draw = ImageDraw.Draw(canvas.data.image)

    edges = canvas.data.edges
    for i in range(len(edges)):
        for j in range(len(edges[0])):
            if edges[i, j] == True:
                draw.point((j, i))

    canvas.data.undoQueue.append(canvas.data.image.copy())
    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)

def selectEdge(canvas):
    if canvas.data.image != None:
        canvas.unbind("<ButtonPress-1>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.unbind("<Button-1>")
        canvas.bind("<Button-1>", \
                                    lambda event: select(event, canvas))

def deselectEdge(canvas):
    if canvas.data.image != None:
        canvas.unbind("<ButtonPress-1>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.unbind("<Button-1>")
        canvas.bind("<ButtonPress-1>", lambda event: onDeselectStart(event, canvas))
        canvas.bind("<ButtonRelease-1>", lambda event: onDeselectEnd(event, canvas))

def isolateAction(canvas):
    global selectedPoints
    sortedPoints = sorted(selectedPoints, key = point_compare)
    unquie_points = remove_duplicated(sortedPoints)
    points_in_map = to_dictionaries(unquie_points)

    draw = ImageDraw.Draw(canvas.data.image)
    w = canvas.data.image.size[0]
    h = canvas.data.image.size[1]
    for i in range(0, w):
        for j in range(0, h):
            if not inside_selection((i, j), points_in_map):
                draw.point((i, j), fill = (128, 128, 128, 0))

    #canvas.data.undoQueue.append(canvas.data.image.copy())
    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)

def to_dictionaries(sortedPoints):
    y_to_points = {}
    points = list()
    points.append(sortedPoints[0])
    y_to_points[sortedPoints[0][1]]=points
    for i in range(1, len(sortedPoints)):
        if sortedPoints[i][1] == sortedPoints[i-1][1]:
            #if sortedPoints[i][0] - y_to_points[sortedPoints[i-1][1]][-1][0] > 3:
            y_to_points[sortedPoints[i-1][1]].append(sortedPoints[i])
        else:
            points = list()
            points.append(sortedPoints[i])
            y_to_points[sortedPoints[i][1]] = points
    return y_to_points

def inside_selection(point, boundary_points):
    x = point[0]
    y = point[1]
    if y in boundary_points:
        y_points = boundary_points[y]
        if x < y_points[0][0] or x > y_points[-1][0]:
            return False

        for i in range(0, len(y_points)):
            if x == y_points[i][0]:
                return True

        grp_numbers = 0
        grp_position = 0
        for i in range(0, len(y_points)):
            grp_numbers = grp_numbers + 1
            while ((i + 1) < len(y_points)) and ((y_points[i + 1][0] - y_points[i][0]) <= 3):
                i = i + 1

            if y_points[i][0] > x and grp_numbers == 0:
                grp_position = grp_numbers

        if grp_numbers == 1:
            return False
        elif grp_numbers == 2:
            return True
        elif grp_numbers == 3:
            return grp_position != 2
        else:
            return grp_position % 2 == 0
        # /*for i in range(0, len(y_points)):
        #     if x < y_points[i][0]:
        #         break
        #
        # if i >= len(y_points):
        #     return False
        # else:
        #     return (len(y_points) - 1 - i) % 2 == 0*/
    else:
        return False

def inside_selection1(point, circle):
    x = point[0]
    y = point[1]
    if y < circle[0][1]:
        return False
    elif y > circle[-1][1]:
        return False
    else:
        for i in range(0, len(circle)):
            if circle[i][1] == y:
                if x < circle[i][0]:
                    return False
                else:
                    while len(circle) > i + 1 and circle[i][1] == circle[i+1][1]:
                        i = i + 1
                    return circle[i][0] >= x
    return False

def remove_duplicated(sortedPoints):
    unqiue_points = list()
    unqiue_points.append(sortedPoints[0])
    for i in range(1, len(sortedPoints)):
        if sortedPoints[i] != sortedPoints[i-1]:
            unqiue_points.append(sortedPoints[i])

    return unqiue_points

def point_compare(xy):
    return xy[1] * 1000 + xy[0]
    # y_direction = x[1] - y[1]
    # if y_direction > 0:
    #     return y_direction
    # else:
    #     return x[0] - y[0]

def drawOnImage(canvas):
    canvas.data.colourPopToHappen = False
    canvas.data.cropPopToHappen = False
    canvas.data.drawOn = True
    colourChosen(canvas)

def colourChosen(canvas):
    if canvas.data.image != None:
        canvas.data.mainWindow.bind("<Button-1>", \
                                    lambda event: drawDraw(event, canvas))
    clickedPositions.clear()

clickedPositions = list()

selectedPoints = list()

def select(event, canvas):
    x = int(round((event.x - canvas.data.imageTopX) * canvas.data.imageScale))
    y = int(round((event.y - canvas.data.imageTopY) * canvas.data.imageScale))
    clickedPositions.append((x, y))
    draw = ImageDraw.Draw(canvas.data.image)

    edges = canvas.data.edges
    startPoint = findClosestPoint((x,y), edges)
    #for i in range(len(edges)):
    #    for j in range(len(edges[0])):
    #        if edges[i, j] == True and abs(i - startPoint[1]) < 20 and abs(j - startPoint[0]) < 20:
    #            draw.point((j, i))

    x = startPoint[0]
    y = startPoint[1]
    dist = 50
    w = canvas.data.width
    h = canvas.data.height
    range = ((x - dist if x >= dist else 0, y - dist if y >= dist else 0),
             (x + dist if x + dist < w else w, y + dist if y + dist < h else h))
    connectedPoints = findPoints((x, y), edges, range)
    for p in connectedPoints:
        selectedPoints.append(p)
        draw.point(p)

    canvas.data.undoQueue.append(canvas.data.image.copy())
    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)

deselect_startPoint = (-100, -100);
def onDeselectStart(event, canvas):
    x = int(round((event.x - canvas.data.imageTopX) * canvas.data.imageScale))
    y = int(round((event.y - canvas.data.imageTopY) * canvas.data.imageScale))
    global deselect_startPoint
    deselect_startPoint = (x, y)

def onDeselectEnd(event, canvas):
    x = int(round((event.x - canvas.data.imageTopX) * canvas.data.imageScale))
    y = int(round((event.y - canvas.data.imageTopY) * canvas.data.imageScale))
    endPoint = (x, y)
    global deselect_startPoint
    removeSelectedPoints(deselect_startPoint, endPoint, canvas)
    deselect_startPoint = (-100, -100)

def removeSelectedPoints(x0y0, x1y1, canvas):
    global selectedPoints
    filteredPoints = list()
    for (x, y) in selectedPoints:
        if not(x >= x0y0[0] and x <= x1y1[0] and y >= x0y0[1] and y <= x1y1[1]):
            filteredPoints.append((x, y))
    selectedPoints = filteredPoints

    canvas.data.colourPopToHappen = False
    canvas.data.cropPopToHappen = False
    canvas.data.drawOn = False
    ### change back to original image
    if canvas.data.image != None:
        canvas.data.image = canvas.data.originalImage.copy()
        #canvas.data.imageForTk = makeImageForTk(canvas)
        #drawImage(canvas)

    draw = ImageDraw.Draw(canvas.data.image)
    for (x, y) in selectedPoints:
        draw.point((x, y))

    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)

def findPoints(xy, edges, range):
    visited = set()
    points = set()
    findConnectedPoints(xy, edges, points, visited, range)
    return points

def findConnectedPoints(xy, edges, points, visited, range):
    visited.add(xy)
    if edges[xy[1], xy[0]] == True:
        points.add(xy)

        print("add point: ", xy)

        adjacent = (xy[0]-1, xy[1]-1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0], xy[1] - 1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0] + 1, xy[1] - 1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0] - 1, xy[1])
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0] + 1, xy[1])
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0] - 1, xy[1] + 1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0], xy[1] + 1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

        adjacent = (xy[0] + 1, xy[1] + 1)
        if withinRange(adjacent, range) and adjacent not in visited:
            findConnectedPoints(adjacent, edges, points, visited, range)

def withinRange(xy, range):
    return xy[0] >= range[0][0] and xy[0] <= range[1][0] and xy[1] >= range[0][1] and xy[1] <= range[1][1]


def findClosestPoint(xy, edges):

    for i in range (0, 10):
        foundPoint = findClosestPointByDistance(xy, edges, i)
        if edges[foundPoint[1], foundPoint[0]] == True:
            return foundPoint

    return xy


def findClosestPointByDistance(xy, edges, distance):
    for i in range(-distance, distance):
        if isPixelHighlightable((xy[0]-distance, xy[1]+i), edges):
            return (xy[0]-distance, xy[1]+i)

        if isPixelHighlightable((xy[0]+distance, xy[1]+i), edges):
            return (xy[0]+distance, xy[1]+i)

        if isPixelHighlightable((xy[0]+i, xy[1]-distance), edges):
            return (xy[0]+i, xy[1]-distance)

        if isPixelHighlightable((xy[0]+i, xy[1]+distance), edges):
            return (xy[0]+i, xy[1]+distance)

    return xy

def isPixelHighlightable(xy, edges):
    dim = edges.shape
    return xy[0] >= 0 and xy[0] <= dim[1] and xy[1] >= 0 and xy[1] <= dim[0] and edges[xy[1], xy[0]] == True

def drawDraw(event, canvas):
    if canvas.data.drawOn == True:
        #clickedPositions.append((event.x, event.y))

        x = int(round((event.x - canvas.data.imageTopX) * canvas.data.imageScale))
        y = int(round((event.y - canvas.data.imageTopY) * canvas.data.imageScale))
        clickedPositions.append((x, y))
        draw = ImageDraw.Draw(canvas.data.image)

        edges = canvas.data.edges
        for i in range(len(edges)):
            for j in range(len(edges[0])):
                if edges[i,j] == True:
                    draw.point((j, i))
        draw.line(clickedPositions, fill=(255, 255, 255), width=1)
        #draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=canvas.data.drawColour, \
        #             outline=None)

        #save(canvas)
        canvas.data.undoQueue.append(canvas.data.image.copy())
        canvas.data.imageForTk = makeImageForTk(canvas)
        drawImage(canvas)


######################## FEATURES ###########################
def reset(canvas):
    canvas.data.colourPopToHappen = False
    canvas.data.cropPopToHappen = False
    canvas.data.drawOn = False
    ### change back to original image
    if canvas.data.image != None:
        canvas.data.image = canvas.data.originalImage.copy()
        save(canvas)
        canvas.data.undoQueue.append(canvas.data.image.copy())
        canvas.data.imageForTk = makeImageForTk(canvas)
        drawImage(canvas)


################ EDIT MENU FUNCTIONS ############################

def keyPressed(canvas, event):
    if event.keysym == "z":
        undo(canvas)
    elif event.keysym == "y":
        redo(canvas)

def undo(canvas):
    if len(canvas.data.undoQueue) > 0:
        # the last element of the Undo Deque is the
        # current version of the image
        lastImage = canvas.data.undoQueue.pop()
        # we would want the current version if wehit redo after undo
        canvas.data.redoQueue.appendleft(lastImage)
    if len(canvas.data.undoQueue) > 0:
        # the previous version of the image
        canvas.data.image = canvas.data.undoQueue[-1]
    save(canvas)
    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)


def redo(canvas):
    if len(canvas.data.redoQueue) > 0:
        canvas.data.image = canvas.data.redoQueue[0]
    save(canvas)
    if len(canvas.data.redoQueue) > 0:
        lastImage = canvas.data.redoQueue.popleft()
        canvas.data.undoQueue.append(lastImage)
    canvas.data.imageForTk = makeImageForTk(canvas)
    drawImage(canvas)


############# MENU COMMANDS ################

def saveAs(canvas):
    if canvas.data.image != None:
        filename = filedialog.asksaveasfilename(defaultextension=".jpg")
        im = canvas.data.image
        im.save(filename)


def save(canvas):
    if canvas.data.image != None:
        im = canvas.data.image
        im.save(canvas.data.imageLocation)


def importImage(canvas):
    imageName = filedialog.askopenfilename()
    filetype = ""
    try:
        filetype = imghdr.what(imageName)
    except:
        messagebox.showinfo(title="Image File", \
                              message="Choose an Image File!", parent=canvas.data.mainWindow)
        return
    if filetype in ['jpeg', 'bmp', 'png', 'tiff']:
        canvas.data.imageLocation = imageName
        im = Image.open(imageName)
        canvas.data.image = im
        canvas.data.originalImage = im.copy()
        canvas.data.undoQueue.append(im.copy())
        canvas.data.imageSize = im.size  # Original Image dimensions
        canvas.data.edges = edge_detection.get_edges(imageName)

        canvas.data.imageForTk = makeImageForTk(canvas)



        #print("edges length: ", len(edges))
        drawImage(canvas)
    else:
        messagebox.showinfo(title="Image File", \
                              message="Choose an Image File!", parent=canvas.data.mainWindow)


######## CREATE A VERSION OF IMAGE TO BE DISPLAYED ON THE CANVAS #########

def makeImageForTk(canvas):
    im = canvas.data.image
    if canvas.data.image != None:
        # Because after cropping the now 'image' might have different
        # dimensional ratios
        imageWidth = canvas.data.image.size[0]
        imageHeight = canvas.data.image.size[1]
        # To make biggest version of the image fit inside the canvas
        if imageWidth > imageHeight:
            resizedImage = im.resize((canvas.data.width, \
                                      int(round(float(imageHeight) * canvas.data.width / imageWidth))))
            # store the scale so as to use it later
            canvas.data.imageScale = float(imageWidth) / canvas.data.width
        else:
            resizedImage = im.resize((int(round(float(imageWidth) * canvas.data.height / imageHeight)), \
                                      canvas.data.height))
            canvas.data.imageScale = float(imageHeight) / canvas.data.height
        # we may need to refer to their resized image atttributes again
        canvas.data.resizedIm = resizedImage
        return ImageTk.PhotoImage(resizedImage)


def drawImage(canvas):
    if canvas.data.image != None:
        # make the canvas center and the image center the same
        canvas.create_image(canvas.data.width / 2.0 - canvas.data.resizedIm.size[0] / 2.0,
                            canvas.data.height / 2.0 - canvas.data.resizedIm.size[1] / 2.0,
                            anchor=NW, image=canvas.data.imageForTk)
        canvas.data.imageTopX = int(round(canvas.data.width / 2.0 - canvas.data.resizedIm.size[0] / 2.0))
        canvas.data.imageTopY = int(round(canvas.data.height / 2.0 - canvas.data.resizedIm.size[1] / 2.0))


############ INITIALIZE ##############

def init(root, canvas):
    buttonsInit(root, canvas)
    menuInit(root, canvas)
    canvas.data.image = None
    canvas.data.angleSelected = None
    canvas.data.rotateWindowClose = False
    canvas.data.brightnessWindowClose = False
    canvas.data.brightnessLevel = None
    canvas.data.histWindowClose = False
    canvas.data.solarizeWindowClose = False
    canvas.data.posterizeWindowClose = False
    canvas.data.colourPopToHappen = False
    canvas.data.cropPopToHappen = False
    canvas.data.endCrop = False
    canvas.data.drawOn = True

    canvas.data.undoQueue = deque([], 10)
    canvas.data.redoQueue = deque([], 10)
    canvas.pack()


def buttonsInit(root, canvas):

    backgroundColour = "gray"
    buttonWidth = 14
    buttonHeight = 2
    toolKitFrame = Frame(root)
    drawButton = Button(toolKitFrame, text="Show Edges", \
                        background=backgroundColour, width=buttonWidth, \
                        height=buttonHeight, command=lambda: showEdges(canvas))
    drawButton.grid(row=1, column=0)
    resetButton = Button(toolKitFrame, text="Clear Edges", \
                         background=backgroundColour, width=buttonWidth, \
                         height=buttonHeight, command=lambda: reset(canvas))
    resetButton.grid(row=2, column=0)
    selectButton = Button(toolKitFrame, text="Select Edge", \
                          background=backgroundColour, width=buttonWidth, \
                          height=buttonHeight, command=lambda: selectEdge(canvas))
    selectButton.grid(row=3, column=0)
    deSelectButton = Button(toolKitFrame, text="De-select Edge", \
                          background=backgroundColour, width=buttonWidth, \
                          height=buttonHeight, command=lambda: deselectEdge(canvas))
    deSelectButton.grid(row=4, column=0)
    isolateButton = Button(toolKitFrame, text="Isolate", \
                            background=backgroundColour, width=buttonWidth, \
                            height=buttonHeight, command=lambda: isolateAction(canvas))
    isolateButton.grid(row=5, column=0)
    toolKitFrame.pack(side=LEFT)


def menuInit(root, canvas):
    menubar = Menu(root)
    menubar.add_command(label="New", command=lambda: importImage(canvas))
    menubar.add_command(label="Save", command=lambda: save(canvas))
    menubar.add_command(label="Save As", command=lambda: saveAs(canvas))
    ## Edit pull-down Menu
    editmenu = Menu(menubar, tearoff=0)
    editmenu.add_command(label="Undo   Z", command=lambda: undo(canvas))
    editmenu.add_command(label="Redo   Y", command=lambda: redo(canvas))
    menubar.add_cascade(label="Edit", menu=editmenu)
    root.config(menu=menubar)

class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>',self.toggle_geom)
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

def run():
    # create the root and the canvas
    root = Tk()
    root.title("Rotoscope.AI")
    root.tk.call('wm', 'iconphoto', root._w, PhotoImage(file='../resouces/rotologo.png'))
    #root.iconbitmap('../resouces/test1.ico')
    canvasWidth = 1280
    canvasHeight = 720

    canvas = Canvas(root, width=canvasWidth, height=canvasHeight, \
                    background='#282828')

    # Set up canvas data and call init
    class Struct: pass

    canvas.data = Struct()
    canvas.data.width = canvasWidth
    canvas.data.height = canvasHeight
    canvas.data.mainWindow = root
    init(root, canvas)
    root.bind("<Key>", lambda event: keyPressed(canvas, event))
    # and launch the app

    app = FullScreenApp(root)
    root.mainloop()  # This call BLOCKS (so your program waits)


run()