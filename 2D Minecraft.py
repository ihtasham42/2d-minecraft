import pygame, random, math, noise, copy, queue
random.seed()
pygame.init()
clock = pygame.time.Clock()

size = (640, 480)
screen = pygame.display.set_mode(size)

tileSize = 32
rows = 512
columns = 128

gravity = 1
groundLevel = 35
offset = random.randint(0, 100000)

tileTypes = {
    #Misc
    "empty" : {
        "sprite" : None,
        "hitpoints" : 0
    },

    #Terrain
    "dirt" : {
        "hitpoints" : 30
    },
    "grass" : {
        "hitpoints" : 30
    },

    "log" : {
        "hitpoints" : 60
    },
    "leaves" : {
        "hitpoints" : 30
    },     
    "stone" : {
        "hitpoints" : 120
    },

    #Ores
    "coalOre" : {
        "hitpoints" : 240
    },
    "ironOre" : {
        "hitpoints" : 240
    },
    "goldOre" : {
        "hitpoints" : 360
    },
    "diamondOre" : {
        "hitpoints" : 480
    },

    #ToSort
    "bricks" : {
        "hitpoints" : 120
    },
    "stoneBricks" : {
        "hitpoints" : 120
    },
    "bookshelf" : {
        "hitpoints" : 120
    },
    "cobblestone" : {
        "hitpoints" : 120
    },
    "mossyCobblestone" : {
        "hitpoints" : 120
    },
    "ironBlock" : {
        "hitpoints" : 120
    },
    "goldBlock" : {
        "hitpoints" : 120
    },
    "diamondBlock" : {
        "hitpoints" : 120
    },
    "plank" : {
        "hitpoints" : 120
    },
    "pumpkin" : {
        "hitpoints" : 120
    },
    "whiteWool" : {
        "hitpoints" : 120
    },
}

schematics = {
    "trees" : {
        "1" : {
            "tile" : {},
            "background" : {
                "log" : [
                    [0, -1],
                    [0, -2],
                ],
                "leaves" : [
                    [-1, -3],
                    [0, -3],
                    [1,-3],
                    [-1, -4],
                    [0, -4],
                    [1, -4],
                    [0, -5]
                ]
            }
        }
    }
}



playerTiles = []
restrictedTiles = ["empty", "coalOre", "ironOre", "goldOre", "diamondOre", "leaves"]
for tileType in tileTypes:
    if tileType in restrictedTiles: continue
    playerTiles.append(tileType)

for tileType in tileTypes:
    if tileType == "empty": continue
    directory = "tiles/" + tileType + ".png"
    sprite = pygame.transform.scale(pygame.image.load(directory), (tileSize, tileSize)).convert_alpha()
    tileTypes[tileType]["sprite"] = sprite

backgroundTiles = {}
for tileType in tileTypes:
    backgroundTile = copy.copy(tileTypes[tileType]["sprite"])
    if not backgroundTile: continue
    backgroundTile.fill((0, 0, 0, 100))
    backgroundTiles[tileType] = backgroundTile

cracks = []
for crack in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
    cracks.append(pygame.transform.scale(pygame.image.load("tiles/cracks/" + crack + ".png"), (tileSize, tileSize)))

directions = {
    "left" : pygame.math.Vector2(-1, 0),
    "right" : pygame.math.Vector2(1, 0)
}

class Tile:
    def __init__(self, x, y, tileType):
        self.x = x
        self.y = y
        self.tileType = tileType
        self.centre = pygame.math.Vector2(x * tileSize + tileSize / 2, y * tileSize + tileSize / 2)
        self.hitpoints = tileTypes[tileType]["hitpoints"]
        
    def takeDamage(self, entity):
        if self.tileType == "empty": return
        self.hitpoints -= 1
        if self.hitpoints <= 0:
            self.destroy()
        else:
            self.drawProgress()

    def setTile(self, tileType):
        self.tileType = tileType
        self.hitpoints = tileTypes[self.tileType]["hitpoints"]

    def reset(self):
        self.hitpoints = tileTypes[self.tileType]["hitpoints"]

    def destroy(self):
        self.tileType = "empty"

    def checkAdjacentNotEmpty(self, layer):
        directions = [[0, 1],
                      [0, -1],
                      [1, 0],
                      [-1, 0]]
        layers = [0]
        if layer == 1: layers.append(1)
        for layer in layers:     
            for direction in directions:
                xNew = self.x + direction[0]
                yNew = self.y + direction[1]
                
                xInBounds = 0 <= xNew < rows
                yInBounds = 0 <= yNew < columns
                if not (xInBounds and yInBounds): continue
                
                adjacentTile = grid[layer][yNew][xNew]
                if adjacentTile.tileType != "empty":
                    return True

    def draw(self, layer):
        if self.tileType == "empty": return
        if player.focusedTile != self: self.hitpoints = tileTypes[self.tileType]["hitpoints"]
        sprite = tileTypes[self.tileType]["sprite"]
        if layer == 0:
            screen.blit(sprite, (tileSize * self.x + player.offset.x, tileSize * self.y + player.offset.y))
        elif layer == 1:
            spriteOver = backgroundTiles[self.tileType]
            screen.blit(sprite, (tileSize * self.x + player.offset.x, tileSize * self.y + player.offset.y))
            screen.blit(spriteOver, (tileSize * self.x + player.offset.x, tileSize * self.y + player.offset.y))
            
    def drawProgress(self):
        if self.tileType == "empty": return
        maxHitpoints = tileTypes[self.tileType]["hitpoints"]
        
        progress = math.floor((len(cracks)) * (1 - self.hitpoints / maxHitpoints))
        crack = cracks[progress]
        screen.blit(crack, (self.x * tileSize + player.offset.x, self.y * tileSize + player.offset.y))

class Entity:
    def __init__(self, position):
        self.position = position
        self.size = pygame.math.Vector2(20, 60)
        
        self.grounded = False
        self.verticalVelocity = 0
        
        self.corners = {
            "top" : pygame.math.Vector2(self.size.x / 2, 0),
            "bottom" : pygame.math.Vector2(self.size.x / 2, self.size.y - 1),
            "left" : pygame.math.Vector2(0, self.size.y) / 2,
            "right" : pygame.math.Vector2(self.size.x - 1, 0) + pygame.math.Vector2(0, self.size.y) / 2,
            
            "topLeft" : pygame.math.Vector2(0, 0),
            "topRight" : pygame.math.Vector2(self.size.x - 1, 0),
            "bottomLeft" : pygame.math.Vector2(0, self.size.y - 1),
            "bottomRight" : self.size + pygame.math.Vector2(-1, -1)
        }
        
        self.base = [
           self.corners["bottomLeft"],
           self.corners["bottomRight"]
        ]

        self.roof = [
            self.corners["topLeft"],
            self.corners["topRight"]
        ]

        self.leftSide = [
            self.corners["topLeft"],
            self.corners["left"],
            self.corners["bottomLeft"]
        ]

        self.rightSide = [
            self.corners["topRight"],
            self.corners["right"],
            self.corners["bottomRight"]
        ]

        self.colour = (200, 0, 0)
        self.walkSpeed = 2
        self.jumpHeight = 7
        self.jumpCooldown = 15
        self.jumpTimer = self.jumpCooldown
        self.interactRange = 150

    def jump(self):
        if self.grounded == True and self.jumpTimer <= 0:
            self.grounded = False
            self.jumpTimer = self.jumpCooldown
            self.verticalVelocity = -self.jumpHeight

    def walk(self, direction):
        self.position += direction * self.walkSpeed
        
        while self.areCornersColliding(self.leftSide):
            self.position.x += 1

        while self.areCornersColliding(self.rightSide):
            self.position.x -= 1

    def fall(self):
        self.jumpTimer -= 1
        
        self.verticalVelocity += 0.3
        if self.verticalVelocity > 16:
            self.verticalVelocity = 16
        self.position.y += self.verticalVelocity

        self.grounded = False
        
        while self.areCornersColliding(self.base):
            self.position.y -= 1
            self.verticalVelocity = 0
            self.grounded = True
            
        while self.areCornersColliding(self.roof):
            self.position.y += 1
            self.verticalVelocity = 0
                
    def areCornersColliding(self, corners):
        for corner in corners:
            cornerPosition = self.position + corner
            
            xInBound = 0 <= cornerPosition.x < tileSize * rows
            yInBound = 0 <= cornerPosition.y < tileSize * columns 
            if not (xInBound and yInBound): return True
            
            tileType = getTileFromPosition(cornerPosition, 0).tileType
            if tileType != "empty":
                return True

    def update(self):
        self.fall()
            
    def draw(self):
        pygame.draw.rect(screen, self.colour, (self.position + player.offset, self.size))

class Player(Entity):
    def __init__(self, position):
        super().__init__(position)

        self.focusedTile = None
        self.outline = pygame.transform.scale(pygame.image.load("tiles/outline.png"), (tileSize, tileSize))
        self.offset = pygame.math.Vector2(0, 0)
        self.tileTypeInHandIndex = 1

    def isInInteractRange(self, tile):
        centre = self.position + self.size / 2
        distance = centre.distance_to(tile.centre)
        if distance <= self.interactRange: return True

    def isEntityInTile(self, tile):
        for entity in entities:
            entityRect = pygame.Rect(entity.position, entity.size)
            tileRect = pygame.Rect(tile.x * tileSize, tile.y * tileSize, tileSize, tileSize)
            if entityRect.colliderect(tileRect):
                return True

    def canPlaceTile(self, tile, layer):
        if layer == 0:
            if self.isInInteractRange(tile) and not self.isEntityInTile(tile) and tile.checkAdjacentNotEmpty(layer) and tile.tileType == "empty":
                return True
        elif layer == 1:
            if self.isInInteractRange(tile) and tile.checkAdjacentNotEmpty(layer) and tile.tileType == "empty":
                return True

    def getTileFromMousePosition(self, layer):
        mousePosition = self.getMousePosition() - player.offset
        tile = getTileFromPosition(mousePosition, layer)
        return tile

    def getMousePosition(self):
        position = pygame.mouse.get_pos()
        mousePosition = pygame.math.Vector2(position[0], position[1])
        return mousePosition

    def breakTile(self, layer):
        tile = self.getTileFromMousePosition(layer)
        if not self.isInInteractRange(tile): return
        tile.takeDamage(self)
        self.focusedTile = tile

    def placeTile(self, layer):
        tile = self.getTileFromMousePosition(layer)
        if not self.canPlaceTile(tile, layer): return
        tileType = playerTiles[self.tileTypeInHandIndex]
        tile.setTile(tileType)

    def getPlayerInputs(self):
        keysPressed = pygame.key.get_pressed()
        if keysPressed[pygame.K_a]:
            player.walk(directions["left"])
            
        if keysPressed[pygame.K_d]:
            player.walk(directions["right"])
            
        if keysPressed[pygame.K_w]:
            player.jump()

        mousePressed = pygame.mouse.get_pressed()
            
        if mousePressed[0]:
            if keysPressed[pygame.K_LSHIFT]:
                self.breakTile(1)
            else:
                self.breakTile(0)
        else:
            if self.focusedTile:
                self.focusedTile.reset()

        if mousePressed[2]:
            if keysPressed[pygame.K_LSHIFT]:
                self.placeTile(1)
            else:
                self.placeTile(0)

    def setOffset(self):
        self.offset = -self.position + pygame.math.Vector2(320, 240) - self.size / 2
        
    def update(self):
        self.getPlayerInputs()
        self.fall()
        self.setOffset()

    def drawOutline(self):
        tile = self.getTileFromMousePosition(0)
        colour = (0, 255, 255)
        if not self.canPlaceTile(tile, 0): colour = (255, 255, 255)
        screen.blit(self.outline, (tile.x * tileSize +  + player.offset.x, tile.y * tileSize +  + player.offset.y))

def getTileFromPosition(position, layer):
    global grid
    
    x, y = int(position.x) // tileSize, int(position.y) // tileSize
    if x > rows - 1: x = rows - 1
    if y > columns - 1: y = columns - 1
    tile = grid[layer][y][x]
    
    return tile

def drawGrid(layer):
    tile = getTileFromPosition(player.position, 0)
    for col in range(20):
        for row in range(22):                  
            y = col + tile.y - 8
            x = row + tile.x - 10
            if y < 0 or y >= columns or x < 0 or x >= rows : continue
            if layer == 1 and grid[0][y][x].tileType != "empty": continue
            tileToBeDrawn = grid[layer][y][x]
            tileToBeDrawn.draw(layer)

def drawHUD():
    index = player.tileTypeInHandIndex % len(playerTiles)   
    tileType = playerTiles[player.tileTypeInHandIndex]
    sprite = tileTypes[tileType]["sprite"]
    screen.blit(pygame.transform.scale(sprite, (64, 64)), (25, 25))
       
def draw():
    screen.fill((204, 229, 255))
    drawGrid(1)
    drawGrid(0)
    for entity in entities:
        entity.update()
        entity.draw()
    player.drawOutline()
    drawHUD()
    pygame.display.update()

def growGrass(potentialGrass):
    for dirt in potentialGrass:
        tileAbovePosition = pygame.Vector2(dirt.x * tileSize, dirt.y * tileSize) + pygame.Vector2(0, -tileSize)
        tileAbove = getTileFromPosition(tileAbovePosition, 0)
        if tileAbove.tileType == "empty":
            tileAbove.setTile("grass")

def decideTerrainTile(row, col):
    tileType = None
    dirtHeight = int(noise.pnoise1(row * 0.03 + offset, 3, repeat = 9999999) * 15)
    stoneHeight = int(noise.pnoise1(row * 0.3 + offset, repeat = 9999999) * 5) + random.randint(-1, 1)
    
    if col < groundLevel + dirtHeight:
        tileType = "empty"
    elif col < groundLevel + 8 + stoneHeight:
        tileType = "dirt"
    else:
        tileType = "stone"

    return tileType

def decideTerrainBackground(row, col, tile):
    tileType = None
    
    if tile.tileType != "empty":

        if tile.tileType == "dirt":
            tileType = "dirt"
        else:
            tileType = "stone"
    else:
        tileType = "empty"

    return tileType

def getLayerNumber(layer):
    if layer == "tile":
        return 0
    elif layer == "background":
        return 1

def generateCaves():
    perlinFactor = 0.1
    chanceGoal = 0.2
    for col in range(columns):
        heightFactor = (groundLevel + 5  - col) / 20
        if heightFactor < 0: heightFactor = 0
        for row in range(rows):
            
            tile = grid[0][col][row]

            chance = noise.pnoise2(row * perlinFactor + offset, col * perlinFactor + offset)
            
            if chance > chanceGoal + heightFactor:
                tile.destroy()

def checkSchematicSpacing(margin):
    pass

def generateSchematic(schematic, x, y):
    for layer in schematic.keys():
        layerNumber = getLayerNumber(layer)
        for tileType in schematic[layer]:
            for tilePosition in schematic[layer][tileType]:
                fx = x + tilePosition[0]
                fy = y + tilePosition[1]
                if fx < rows and fx >= 0 and fy < rows and fy >= 0:
                    tile = grid[layerNumber][fy][fx]
                    tile.setTile(tileType)

def generateTrees():
    treeTiles = []

    for col in range(columns):
        for row in range(rows):
            tile = grid[0][col][row]
            if tile.tileType == "grass" and random.randint(1, 5) == 1:
                treeTiles.append(tile)

    for treeTile in treeTiles:
        schematic = schematics["trees"]["1"]
        generateSchematic(schematic, treeTile.x, treeTile.y) 

def generateWorld():
    global grid
    potentialGrass = []
    for layer in range(2):
        for col in range(columns):
            grid[layer].append([])
            for row in range(rows):
                if layer == 0:    
                    tileType = decideTerrainTile(row, col)
                    tile = Tile(row, col, tileType)
                    
                    if tileType == "dirt": potentialGrass.append(tile)
                    
                elif layer == 1:
                    tile = grid[0][col][row]
                    tileType = decideTerrainBackground(row, col, tile)
                    tile = Tile(row, col, tileType)
                    
                grid[layer][col].append(tile)

    growGrass(potentialGrass)
    generateCaves()
    generateTrees()


grid = [[], []]
generateWorld()

entities = []
player = Player(pygame.math.Vector2(rows / 2 * tileSize, 300))
entities.append(player)
        
run = True
while run:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                player.tileTypeInHandIndex += 1
                if player.tileTypeInHandIndex == len(playerTiles):
                    player.tileTypeInHandIndex = 0
            if event.button == 5:
                player.tileTypeInHandIndex -= 1
                if player.tileTypeInHandIndex < 0:
                    player.tileTypeInHandIndex = len(playerTiles) - 1

    draw()

pygame.quit()
