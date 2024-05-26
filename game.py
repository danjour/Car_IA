import pygame
import random
import numpy as np

pygame.init()

#Configuring the basic settings
screen_width = 400
screen_height = 600
FPS = 60

car_width = 75
car_height = 120
car_speed = 2

obstacle_width = 75
obstacle_height = 50
obstacle_speed = 5
obstacle_increment_speed = 0.01

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Don't damage another car")

clock = pygame.time.Clock()

class Jogo:
    def __init__(self) -> None:
        self.frame_iteration = 0
        self.obstacle_x1 = random.choice([0, 40])
        self.obstacle_x2 = random.choice([200, 300])
        self.background_y1 = 0
        self.background_y2 = -screen_height
        self.score = 0
        self.generation = 0
        self._restart()
        self.car_image = pygame.image.load(r"assets\car0.png").convert_alpha()
        self.car_image = pygame.transform.scale(self.car_image, (car_width, car_height))
        self.car_image1 = pygame.image.load(r"assets\car1.png").convert_alpha()
        self.car_image1 = pygame.transform.scale(self.car_image1, (car_width, car_height))
        self.car_image2 = pygame.image.load(r"assets\car2.png").convert_alpha()
        self.car_image2 = pygame.transform.scale(self.car_image2, (car_width, car_height))
        self.imagem_fundo = pygame.image.load(r"assets\background.png").convert()

    # Moves the car based on the received input action.
    # action is an array where [1, 0, 0] moves the car left, 
    # [0, 1, 0] moves the car right, and [0, 0, 1] keeps the car in place.
    def _move(self, action: np.ndarray) -> None:
        if np.array_equal(action, [1, 0, 0]):
            self.car_x -= car_speed
            if self.car_x < 0: 
                self.car_x = 0
        elif np.array_equal(action, [0, 1, 0]):
            self.car_x += car_speed
            if self.car_x > screen_width - car_width:
                self.car_x = screen_width - car_width
        elif np.array_equal(action, [0, 0, 1]):
            pass
    
    # If we have a collision, the game will restart.
    def _restart(self) -> None:
        self.car_x = screen_width // 2 - car_width // 2
        self.car_y = screen_height - car_height - 20
        self.obstacle_x = 0
        self.obstacle_y = -obstacle_height
        self.score = 0
        self.obstacle_speed = obstacle_speed
        # I used it to prevent the car from staying in the same position for too long.
        # Essentially, I try to place the obstacle directly in front of the car.
        if self.car_x < 40:
            self.obstacle_x1 = self.car_x
        else:  
            self.obstacle_x1 = random.choice([0, 40])
        if self.car_x > 210:
            self.obstacle_x2 = self.car_x
        else:  
            self.obstacle_x2 = random.choice([self.car_x, 300])
        self.obstacle_z1 = 75
        self.obstacle_z2 = 75
        self.car_x_anterior = self.car_x

    # Create the car.
    def create_car(self, x: int, y: int) -> None:
        screen.blit(self.car_image, (x, y))

    # Create the obstacle.
    def create_obstacle(self, x:int, y:int,z:int) ->None:
        # If the car is in the "other side" of the street, the image will flip.
        if x < 200: 
            screen.blit(pygame.transform.flip(self.car_image1, False, True), (x, y, z, obstacle_height))
        else:
            screen.blit(self.car_image2, (x, y, z, obstacle_height))

    # Only to show the score and the generation.
    def show_score(self) -> None:
        font = pygame.font.Font(None, 30)
        score_text = font.render(f"Score: {self.score} - Generation: {self.generation}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

    # A function to check if we have a collision.
    def collision(self, rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
        return rect1.colliderect(rect2)

    # To put more fun in the play, always that the car pass the obstacle, the speed of the obstacle will increase.
    def adjust_speed_obstacle(self)-> None:
        self.obstacle_speed += obstacle_increment_speed
    
    # Main game logic occurs here.
    def play_step(self, action: np.ndarray) -> tuple:
        
        # Move the car based on the action.
        self._move(action) 
        self.frame_iteration += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        car_rect = pygame.Rect(self.car_x, self.car_y, car_width, car_height)
        obstacle_rect1 = pygame.Rect(self.obstacle_x1, self.obstacle_y, car_width, obstacle_height)
        obstacle_rect2 = pygame.Rect(self.obstacle_x2, self.obstacle_y, car_width, obstacle_height)
        
        reward = 0
        game_over = False

        # Check if the car has collided with the first or second obstacle.
        if self.collision(car_rect, obstacle_rect1) or self.collision(car_rect, obstacle_rect2):
            # Increase the generation count.
            self.generation += 1
            # Restart the game.
            self._restart()
            # Assign a negative reward to the model.
            reward = -10
            self.frame_iteration = 0
            return reward, True, self.score

        # If there is no collision, the car successfully passed the obstacle, earning points.
        if self.obstacle_y > screen_height:
            self.generation += 1
            reward = 12
            # Prevent the car from staying in the same position for too long.
            # Place the obstacle directly in front of the car if needed.
            if self.car_x < 40:
                self.obstacle_x1 = self.car_x
            else:  
                self.obstacle_x1 = random.choice([0, 40])

            if self.car_x > 210:
                self.obstacle_x2 = self.car_x
            else:  
                self.obstacle_x2 = random.choice([210, 300])
            self.obstacle_y = -obstacle_height
            self.score += 1
            game_over = True
            self.adjust_speed_obstacle()

        return reward, game_over, self.score

    def run_game(self)  -> tuple:
        # This make the background "walk"
        self.background_y1 += self.obstacle_speed
        self.background_y2 += self.obstacle_speed

        # Reset the background position when it moves off the screen.
        if self.background_y1 >= screen_height:
            self.background_y1 = -screen_height
        if self.background_y2 >= screen_height:
            self.background_y2 = -screen_height

        # Create the background images.
        screen.blit(self.imagem_fundo, (0, self.background_y1))
        screen.blit(self.imagem_fundo, (0, self.background_y2))

        # Create and the car and obstacles.
        self.create_car(self.car_x, self.car_y)
        self.create_obstacle(self.obstacle_x1, self.obstacle_y,obstacle_width)
        self.create_obstacle(self.obstacle_x2, self.obstacle_y,obstacle_width)

        # Move the obstacles downwards.
        self.obstacle_y += self.obstacle_speed

        # Display the current score and generation.
        self.show_score()
        pygame.display.update()
        clock.tick(FPS)
        
        return self.obstacle_x, self.obstacle_y, self.car_x,self.car_y,self.obstacle_x2


