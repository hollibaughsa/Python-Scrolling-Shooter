# Stephen Hollibaugh
# April 28, 2010

import pygame
import random
from collections import deque

# Tiled background to be scrolled
Background = [
	[1, 1, 3, 5, 0, 8, 7, 8, 8, 7, 8, 0, 6, 4, 1, 1],
	[2, 1, 3, 5, 0, 0, 7, 8, 8, 7, 0, 0, 6, 4, 1, 2],
]

rlTimes = [30, 10, 45] # Reload times for each weapon type
enemyVals = [50, 250, 500] # Score values for enemy types
enemyHealth = [2, 6, 12] # Health for enemy types

sndShots = [] # Sound effects for weapons

# Projectile shot by the player or an enemy
class Projectile:
	def __init__(self, type, x, y, vx, vy, ax = 0, ay = 0, tvx = 0, tvy = 0):
		self.type = type # 0=gun, 1=laser, 2=missile
		self.x = x
		self.y = y
		self.vx = vx
		self.vy = vy
		self.ax = ax
		self.ay = ay
		self.tvx = tvx # Target x velocity. X Acceleration will stop when this is reached
		self.tvy = tvy # Target y velocity. Y Acceleration will stop when this is reached
		
	def tick(self):
		# Move
		self.x += self.vx
		self.y += self.vy
		# Accelerate
		if self.vx != self.tvx:
			self.vx += self.ax
		if self.vy != self.tvy:
			self.vy += self.ay

# An explosion special effect
class Explosion:
	def __init__(self, x, y):
		# Set fireball positions
		self.points = []
		i = 0
		while i < 8:
			self.points.append([x, y, i % 4])
			i += 1
		# Set velocity of each fireball
		self.velocity = [
			(-2, 0),
			(-1, -1),
			(0, -2),
			(1, -1),
			(2, 0),
			(1, 1),
			(0, 2),
			(-1, 1)
		]
		# Time until disappears
		self.life = 30
		
	def tick(self):
		# Update the position of each fireball
		i = 0
		while i < 8:
			self.points[i][0] += self.velocity[i][0]
			self.points[i][1] += self.velocity[i][1]
			self.points[i][2] = (self.points[i][2] + 1) % 4
			i += 1
		# Update timer
		self.life -= 1

# Floating powerup		
class Pickup:
	def __init__(self, type, x, y):
		self.type = type # 0-2=weapons, 3=health, 4=score
		self.x = x
		self.y = y
		# Randomize velocity
		self.vx = random.randrange(0, 2)
		self.vy = random.randrange(0, 2)
		if not self.vx:
			self.vx = -1
		if not self.vy:
			self.vy = -1
			
		self.vx *= 2
		self.vy *= 2
		# Time until disappears
		self.life = 360
		
	def tick(self):
		# Update timer
		self.life -= 1
		# Update position
		self.x += self.vx
		self.y += self.vy
		# Check screen boundaries and bounce
		if self.x + 4 < 0 or self.x - 4 > 256:
			self.vx *= -1
		if self.y + 4 < 0 or self.y - 4 > 256:
			self.vy *= -1

# Enemy ship that moves down the screen			
class Enemy:
	def __init__(self, type, x, vy = 2):
		self.type = type
		self.x = x
		self.y = -8 # Start off screen
		self.offY = 8
		self.offX = 8
		self.vy = vy
		self.health = enemyHealth[type]
		self.load = 0
		self.lTime = 10 # Delay before enemy starts shooting
		self.shots = []
		self.alive = 1
		
	def projCollide(self, projectile):
		# Check if collided with a projectile
		if self.x + self.offX > projectile.x and self.x - self.offX < projectile.x + 8 and self.y + self.offY > projectile.y and self.y - self.offY < projectile.y + 8:
			# Apply damage
			self.health -= projectile.type + 1
			# Check for death
			if self.health <= 0:
				self.alive = 0
				
			return 1
			
		return 0
	
	def tick(self):
		# Update projectiles from this ship
		for shot in self.shots:
			shot.tick()
			if shot.x + 4 < 0 or shot.x - 4 > 256 or shot.y + 4 < 0 or shot.y - 4 > 256:
				self.shots.remove(shot)
		
		# Update position
		if self.alive:
			self.y += self.vy
			if self.lTime:
				self.lTime -= 1
				if not self.lTime:
					self.load = 1
			
			# Fire weapons
			if self.load:
				self.shots.append(Projectile(self.type, self.x, self.y + self.offY, 0, 4))
				self.load = 0
				self.lTime = rlTimes[self.type] * 1.5
		
# Player controlled ship	
class Player:
	def __init__(self):
		self.x = 128
		self.y = 224
		self.offX = 8
		self.offY = 8
		self.width = 16
		self.height = 16
		self.vis = 1 # Visible or not
		self.vTime = 60 # Invincibility timer
		self.health = 16
		self.projectile = 0 # Current weapon
		self.pLevel = 0 # Level of current weapon
		self.load = 1
		self.lTime = 0
		self.speed = 3
		self.alive = 1
		self.keyStates = {"U":0, "D":0, "L":0, "R":0, "F":0}
		self.shots = []
		
	def keyPress(self, e):
		if e.key == pygame.K_UP:
			self.keyStates["U"] = 1
		elif e.key == pygame.K_DOWN:
			self.keyStates["D"] = 1
		elif e.key == pygame.K_LEFT:
			self.keyStates["L"] = 1
		elif e.key == pygame.K_RIGHT:
			self.keyStates["R"] = 1
		elif e.key == pygame.K_SPACE:
			self.keyStates["F"] = 1
		
	def keyRelease(self, e):
		if e.key == pygame.K_UP:
			self.keyStates["U"] = 0
		elif e.key == pygame.K_DOWN:
			self.keyStates["D"] = 0
		elif e.key == pygame.K_LEFT:
			self.keyStates["L"] = 0
		elif e.key == pygame.K_RIGHT:
			self.keyStates["R"] = 0
		elif e.key == pygame.K_SPACE:
			self.keyStates["F"] = 0
			
	def projCollide(self, projectile):
		# Check if collided with a projectile
		if not self.vTime and self.alive and self.x + self.offX > projectile.x and self.x - self.offX < projectile.x + 8 and self.y + self.offY > projectile.y and self.y - self.offY < projectile.y + 8:
			# Apply damage
			self.health -= projectile.type + 1
			# Give temporary invincibility
			self.vTime = 30
			return 1
			
		return 0
	
	def pickupCollide(self, pickup):
		# Check if collided with a pickup
		if self.alive and self.x + self.offX > pickup.x - 4 and self.x - self.offX < pickup.x + 4 and self.y + self.offY > pickup.y - 4 and self.y - self.offY < pickup.y + 4:
			# Weapon pickup
			if pickup.type < 3:
				if pickup.type == self.projectile:
					self.pLevel += 1
					if self.pLevel > 4:
						self.pLevel = 4
				else:
					self.projectile = pickup.type
					self.pLevel -= 1
					if self.pLevel < 0:
						self.pLevel = 0
			# Health pickup
			elif pickup.type == 3:
				self.health += 1
				if self.health > 16:
					self.health = 16
		
			return 1
		
		return 0
	
	def tick(self):
		# Update projectiles from player
		for shot in self.shots:
			shot.tick()
			if shot.x + 8 < 0 or shot.x > 256 or shot.y + 8 < 0 or shot.y > 256:
				self.shots.remove(shot)
		
		# Blink if invincible
		if self.vTime:
			self.vis = (self.vis + 1) % 2
			self.vTime -= 1
		elif self.alive:
			self.vis = 1
		else:
			self.vis = 0
		
		# Update reload time
		if self.lTime:
			self.lTime -= 1
			if not self.lTime:
				self.load = 1
		if self.alive:	
			# Move ship
			if self.keyStates["U"] and self.y - self.offY > 0:
				self.y -= self.speed
			if self.keyStates["D"] and self.y + self.offY < 256:
				self.y += self.speed
			if self.keyStates["L"] and self.x - self.offX > 0:
				self.x -= self.speed
			if self.keyStates["R"] and self.x + self.offX < 256:
				self.x += self.speed
			if self.keyStates["F"] and self.load:
				# Fire weapon of appropriate type and level
				sndShots[self.projectile].play()
				if self.pLevel == 0:
					self.shots.append(Projectile(self.projectile, self.x, self.y - self.offY, 0, -4))
				else:
					if self.projectile == 0:
						if self.pLevel == 1 or self.pLevel == 2:
							self.shots.append(Projectile(self.projectile, self.x, self.y - self.offY, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y - self.offY / 2, -3, -3))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y - self.offY / 2, 3, -3))
						else:
							self.shots.append(Projectile(self.projectile, self.x, self.y - self.offY, 0, -5))
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y - self.offY / 2, -3, -3))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y - self.offY / 2, 3, -3))
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 4, self.y - 3 * self.offY / 4, -2, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 4, self.y - 3 * self.offY / 4, 2, -4))
							
					elif self.projectile == 1:
						if self.pLevel == 1 or self.pLevel == 2:
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y, 0, -4))
						else:
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y - self.offY / 2, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y - self.offY / 2, 0, -4))
							
					else:
						if self.pLevel == 1 or self.pLevel == 2:
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y - self.offY / 2, -4.0, -6.0, 0.5, 0.5, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y - self.offY / 2, 4.0, -6.0, -0.5, 0.5, 0, -4))
						else:
							self.shots.append(Projectile(self.projectile, self.x - self.offX / 2, self.y - self.offY / 2, -4.0, -6.0, 0.5, 0.5, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x + self.offX / 2, self.y - self.offY / 2, 4.0, -6.0, -0.5, 0.5, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x, self.y, 2.0, -8.0, -0.25, 0.5, 0, -4))
							self.shots.append(Projectile(self.projectile, self.x, self.y, -2.0, -8.0, 0.25, 0.5, 0, -4))
							
				self.load = 0
				self.lTime = rlTimes[self.projectile] * (3 - self.pLevel / 2) / 3
		

def main():
	pygame.init() # Initialize pygame
	pygame.mixer.init(buffer=1024) # buffer set lower than default to decrease delay in audio playback
	pygame.mouse.set_visible(0) # Hide the mouse
	clock = pygame.time.Clock() # Timer to control framerate
	screen = pygame.display.set_mode((512, 512))
	pygame.display.set_caption("Vertical Shooter")
	disp = pygame.Surface((256, 256)) # Main surface
	hud = pygame.Surface((256, 16)) # Surface for health and score
	tiles = pygame.image.load("bgTiles.bmp") # Tiles for the background
	sprPlayer = pygame.image.load("player.bmp") # Player image
	sprPlayer.set_colorkey((0, 0, 0))
	sprShot = pygame.image.load("shot.bmp") # Projectiles
	sprShot.set_colorkey((0, 0, 0))
	sprEnemy = pygame.image.load("enemy.bmp") # Enemy images
	sprEnemy.set_colorkey((0, 0, 0))
	sprPickup = pygame.image.load("pickup.bmp") # Pickups
	sprPickup.set_colorkey((0, 0, 0))
	sprFlame = pygame.image.load("flame.bmp") # Fireball for explosions
	sprFlame.set_colorkey((0, 0, 0))
	sprHealth = pygame.image.load("health.bmp") # Health counters
	sprNums = pygame.image.load("numbers.bmp") # Numbers for displaying score
	sprScore = pygame.image.load("score.bmp") # The word 'Score:'
	
	sndShots.append(pygame.mixer.Sound("shot1.wav"))
	sndShots.append(pygame.mixer.Sound("shot2.wav"))
	sndShots.append(pygame.mixer.Sound("shot3.wav"))
	sndExplode = pygame.mixer.Sound("explode.wav")
	
	# Lower volume of sounds
	sndShots[0].set_volume(0.25)
	sndShots[1].set_volume(0.25)
	sndShots[2].set_volume(0.25)
	sndExplode.set_volume(0.25)
	
	nextE = 120 # Timer for next enemy spawn
	typeDelay = [940, 2560] # Time until each new enemy type is introduced
	typeRange = 1 # Types of enemies being used
	yOff = 16 # For vertical scroll
	nextRow = 1
	running = 1
	bgDeque = deque([]) # Background data
	i = 0
	score = 0
	player = Player()
	enemies = []
	pickups = []
	effects = []
	
	# Create background
	while i < 17:
		bgDeque.append(Background[i % 2])
		i += 1
	
	while running:
		for event in pygame.event.get():
			# Handle 'X'
			if event.type == pygame.QUIT:
				running = 0
			# Handle keyboard input
			elif event.type == pygame.KEYDOWN and event.key != pygame.K_RETURN:
				player.keyPress(event)
			elif event.type == pygame.KEYUP:
				player.keyRelease(event)
		
		# Clear the screen
		disp.fill((0, 0, 0))
		hud.fill((0, 0, 0))
		
		i = 0
		# Draw health status to hud
		while i < 16:
			if player.health - i > 0:
				hud.blit(sprHealth, (i % 8 * 8, i / 8 * 8), pygame.Rect(0, 0, 8, 8))
			else:
				hud.blit(sprHealth, (i % 8 * 8, i / 8 * 8), pygame.Rect(8, 0, 8, 8))
			i += 1
		
		# Draw score to hud
		hud.blit(sprScore, (256 - 48, 0))
		hud.blit(sprNums, (256 - 48, 8), pygame.Rect((score / 100000) * 8, 0, 8, 8))
		hud.blit(sprNums, (256 - 48 + 8, 8), pygame.Rect((score % 100000) / 10000  * 8, 0, 8, 8))
		hud.blit(sprNums, (256 - 48 + 16, 8), pygame.Rect((score % 10000) / 1000 * 8, 0, 8, 8))
		hud.blit(sprNums, (256 - 48 + 24, 8), pygame.Rect((score % 1000) / 100 * 8, 0, 8, 8))
		hud.blit(sprNums, (256 - 48 + 32, 8), pygame.Rect((score % 100) / 10 * 8, 0, 8, 8))
		hud.blit(sprNums, (256 - 48 + 40, 8), pygame.Rect((score % 10) * 8, 0, 8, 8))
		
		rNum = 0
		# Draw background to main surface
		for row in bgDeque:
			iNum = 0
			for elem in row:
				if elem != 0:
					elem -= 1
					disp.blit(tiles, (iNum * 16, rNum * 16 - yOff), pygame.Rect(elem % 8 * 16, elem / 8 * 16, 16, 16))
				
				iNum += 1
				
			rNum += 1
		# Scroll background	
		yOff -= 1
		if yOff <= 0:
			yOff = 16
			bgDeque.popleft()
			bgDeque.append(Background[nextRow])
			nextRow = (nextRow + 1) % 2
		# Draw pickups
		for pickup in pickups:
			disp.blit(sprPickup, (pickup.x - 4, pickup.y - 4), pygame.Rect(pickup.type * 8, 0, 8, 8))
		# Draw player projectiles
		for shot in player.shots:
			disp.blit(sprShot, (shot.x - 4, shot.y - 4), pygame.Rect(shot.type % 2 * 8, shot.type / 2 * 8, 8, 8))
			if shot.type == 2:
				disp.blit(sprShot, (shot.x - 4, shot.y + 4), pygame.Rect(8, 8, 8, 8))
		# Draw enemy projectiles		
		for enemy in enemies:
			for shot in enemy.shots:
				disp.blit(pygame.transform.flip(sprShot, 0, 1), (shot.x - 4, shot.y - 4), pygame.Rect(shot.type % 2 * 8, (3 - shot.type) / 2 * 8, 8, 8))
				if shot.type == 2:
					disp.blit(pygame.transform.flip(sprShot, 0, 1), (shot.x - 4, shot.y - 12), pygame.Rect(8, 0, 8, 8))
			if enemy.alive:	
				disp.blit(sprEnemy, (enemy.x - enemy.offX, enemy.y - enemy.offY), pygame.Rect(enemy.type * 16, 0, 16, 16))
		# Draw player
		if player.vis:
			disp.blit(sprPlayer, (player.x - player.offX, player.y - player.offY))
		# Draw explosions
		for effect in effects:
			for point in effect.points:
				disp.blit(pygame.transform.rotate(sprFlame, point[2] * 90), (point[0], point[1]))
		# Update player
		player.tick()
		# Update explosions
		for effect in effects:
			effect.tick()
			if effect.life <= 0:
				effects.remove(effect)
		# Update pickups
		for pickup in pickups:
			pickup.tick()
			if pickup.life <= 0:
				pickups.remove(pickup)
			# Handle score pickup
			if player.pickupCollide(pickup):
				if pickup.type == 4:
					score += 1000
				pickups.remove(pickup)
		# Update enemies	
		for enemy in enemies:
			enemy.tick()
			# Check collisions with player projectiles
			for shot in player.shots:
				if enemy.alive and enemy.projCollide(shot):
					player.shots.remove(shot)
					# Kill enemy
					if not enemy.alive:
						sndExplode.play()
						score += enemyVals[enemy.type]
						effects.append(Explosion(enemy.x, enemy.y))
						type = random.randrange(0, 10)
						if type < 5:
							pickups.append(Pickup(type, enemy.x, enemy.y))
			# Remove offscreen enemies
			if enemy.y - enemy.offY > 256:
				enemies.remove(enemy)
			else:
				# Check player collision with enemy projectiles
				for shot in enemy.shots:
					if player.projCollide(shot):
						enemy.shots.remove(shot)
						if player.health <= 0:
							player.alive = 0
							player.vTime = 0
							sndExplode.play()
							effects.append(Explosion(player.x, player.y))
			# Remove a dead enemy from the list when all of it's projectiles are gone			
			if not enemy.alive and len(enemy.shots) == 0:
				enemies.remove(enemy)
	
		nextE -= 1 # Update time until next enemy spawns
		typeDelay[0] -= 1
		typeDelay[1] -= 1
		# Introduce new enemy types
		if typeDelay[0] == 0:
			typeRange = 2
		if typeDelay[1] == 0:
			typeRange = 3
		# Spawn new enemy
		if nextE == 0:
			type = random.randrange(0, typeRange)
			rX = random.randrange(16, 240)
			enemies.append(Enemy(type, rX))
			nextE = 120 / typeRange
		# Keep score at 6 digits
		if score > 999999:
			score = 999999
		# Draw hud to main surface
		disp.blit(hud, (0, 0))
		# Draw scaled up version of main surface to screen
		screen.blit(pygame.transform.scale(disp, (512, 512)), (0, 0))
		# Flip display
		pygame.display.flip()
		# Control framerate
		clock.tick(60)
	
	pygame.mixer.quit()
	pygame.quit()

# Prevents main program from running if imported into another program	
if __name__ == "__main__":
	main()