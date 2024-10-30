import pygame
import pygame.math as pgm
import sys
from falcon_serial import VCU

# Constants
WIDTH, HEIGHT = 1200, 800
DEADBAND = 0.05
FPS = 60

# Positions for left and right wheels relative to the race car
LW_POS = pgm.Vector2(0.309, -0.746)
RW_POS = pgm.Vector2(0.693, -0.746)

def initialize_pygame():
    pygame.init()
    

def load_images():
    try:
        images = {
            'steering_wheel': pygame.image.load('steering_wheel.png').convert_alpha(),
            'race_car': pygame.image.load('race_car.png').convert_alpha(),
            'wheel': pygame.image.load('wheel.png').convert_alpha(),      
            'odometer': pygame.image.load('odometer.png').convert_alpha(),   
            'odometer_dial': pygame.image.load('odometer_dial.png').convert_alpha()
            }
        return images
    except pygame.error as e:
        print(f"Error loading images: {e}")
        pygame.quit()
        sys.exit()

def setup_display():
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rotating Steering Wheel")
    return window

def initialize_joystick():
    pygame.joystick.quit()
    pygame.joystick.init()
    # if pygame.joystick.get_count() == 0:
    #     print("No joystick connected")
    #     pygame.quit()
    #     sys.exit()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return joystick

def image_transform(image, angle, scale):
    rotated_image = pygame.transform.rotozoom(image, angle, 1)
    rotated_image = pygame.transform.smoothscale_by(rotated_image, scale)
    return rotated_image

def move(image, angle, scale, rect):
    transformed_image = pygame.transform.rotozoom(image, angle, 1)
    transformed_image = pygame.transform.smoothscale_by(transformed_image, scale)
    transformed_rect = transformed_image.get_rect(center=rect.center)
    return transformed_rect, transformed_image

def calculate_wheel_centers(race_car_rect, race_car_size):

    left_wheel_center = pgm.Vector2(race_car_rect.bottomleft) + race_car_size.elementwise() * LW_POS
    right_wheel_center = pgm.Vector2(race_car_rect.bottomleft) + race_car_size.elementwise() * RW_POS
    return left_wheel_center, right_wheel_center

def handle_input(joystick: pygame.joystick.JoystickType) -> float:

    x_axis = joystick.get_axis(2)  # Adjust axis index if necessary
    y_axis = joystick.get_axis(1)  # Adjust axis index if necessary

    # Apply deadband
    if abs(x_axis) < DEADBAND:
        x_axis = 0
    if abs(y_axis) < DEADBAND:
        y_axis = 0
    

    # Map the axis value (-1.0 to 1.0) to angle (-140 to 140 degrees)
    angle = x_axis * 140.0
    throttle = y_axis * 80.0
    return angle , throttle



def main():
    # Initialization
    initialize_pygame()
    vcu = VCU(port_name="/dev/cu.usbmodem11203")
    vcu.debug()
    window = setup_display()
    images = load_images()
    joystick = None
    try:
        joystick = initialize_joystick()
    except pygame.error as e:
        print(f"Error initializing joystick: {e}")
        
    clock = pygame.time.Clock()

    # Prepare steering wheel
    steering_wheel_image = images['steering_wheel']
    steering_wheel_rect = steering_wheel_image.get_rect(center=(WIDTH // 4, HEIGHT // 4))

    # Prepare race car
    race_car_image = images['race_car']
    race_car_transformed = image_transform(race_car_image, 90, 0.3)
    race_car_rect = race_car_transformed.get_rect(center=(3 * WIDTH // 4, HEIGHT // 4))
    race_car_size = pgm.Vector2(race_car_rect.size)

    # Calculate wheel centers
    left_wheel_center, right_wheel_center = calculate_wheel_centers(race_car_rect, race_car_size)

    # Prepare wheels
    wheel_image = images['wheel']
    left_wheel = wheel_image.get_rect(center=left_wheel_center)
    right_wheel = wheel_image.get_rect(center=right_wheel_center)

    #odometer 
    odometer_image = images['odometer']
    odometer_dial_image = images['odometer_dial']
    scaled_odometer = pygame.transform.smoothscale_by(odometer_image, 0.2)
    scaled_odometer_dial = pygame.transform.smoothscale_by(odometer_dial_image, 0.2)
    odometer_rect = scaled_odometer.get_rect(center=(1.2*WIDTH // 4, 3 * HEIGHT // 4))
    odometer_dial_center = pygame.Vector2(odometer_rect.midbottom) + pygame.Vector2(0, -odometer_dial_image.get_height() // 2)
    odometer_dial_rect = scaled_odometer_dial.get_rect(center=odometer_dial_center)


    
    

    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                vcu.close()
                running = False
        try:
            joystick = initialize_joystick()
        except pygame.error as e:
            print(f"Error initializing joystick: {e}")
            continue

        # Input Handling
        angle, throttle = handle_input(joystick)
        get_position = -angle * 0.215  # TODO: Change to a function call if needed

        # Update Steering Wheel
        steering_rot_rect, steering_rot_image = move(steering_wheel_image, -angle, 0.4, steering_wheel_rect)
        vcu.set_angle(-angle)

        # Update Wheels
        left_wheel_rot_rect, left_wheel_rot_image = move(wheel_image, get_position + 90, 0.3, left_wheel)
        right_wheel_rot_rect, right_wheel_rot_image = move(wheel_image, get_position - 90, 0.3, right_wheel)

        # Update Odometer
        odometer_dial_rot_rect , odometer_dial_rot_image = move(odometer_dial_image, -throttle + 90, 0.2, odometer_dial_rect)
        vcu.set_torque(throttle)




        # Rendering
        window.fill((40, 44, 52))  # Background color

        # Draw all elements
        window.blit(steering_rot_image, steering_rot_rect)
        window.blit(race_car_transformed, race_car_rect)
        window.blit(left_wheel_rot_image, left_wheel_rot_rect)
        window.blit(right_wheel_rot_image, right_wheel_rot_rect)
        window.blit(scaled_odometer, odometer_rect)
        window.blit(odometer_dial_rot_image, odometer_dial_rot_rect)

        # Update the display
        pygame.display.flip()

        # Maintain frame rate
        clock.tick(FPS)

    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
