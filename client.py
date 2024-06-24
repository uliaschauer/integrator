import pygame
from pygame.math import Vector2
import pygame_gui
from pygame_gui import UIManager
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton, UIDropDownMenu, UITextEntryLine, UIImage, UILabel
import numpy as np
from network import Network
from player_update import PlayerUpdate

FLOOR_HEIGHT = 500
START_POS = [100, FLOOR_HEIGHT]
START_ANGLE = 65
TARGET_POS = [700, FLOOR_HEIGHT]
BALL_MASS = 1.00
BALL_CROSS_SECTION = 1.00
AIR_DENSITY = 1.00
GRAVITY = 9.81
DRAG = 0.008
BALL_RADIUS = 20
HOOP_RADIUS = 28
HOOP_PERSPECTIVE = 0.5
HOOP_THICKNESS = 2
ADMISSIBLE_DELTA = 2
FPS = 60
SERVER = "10.0.0.63"

#ALGORITHMS = ['Euler', 'Verlet', 'Velocity Verlet', 'Leap Frog']
ALGORITHMS = ['Verlet', 'Velocity Verlet', 'Leap Frog']

#set working directory
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#compute the perfect trajectory
#start_radians = np.deg2rad(START_ANGLE)
#start_speed = np.sqrt((TARGET_POS[0] - START_POS[0])*GRAVITY / np.sin(2*start_radians))
#print(np.rad2deg(start_radians), start_speed)
#trajectory_x = np.arange(START_POS[0], TARGET_POS[0]+1)
#trajectory_y = START_POS[1] -(np.tan(start_radians) * (trajectory_x - START_POS[0]) - GRAVITY * (trajectory_x - START_POS[0]) * (trajectory_x - START_POS[0]) / (2 * start_speed * start_speed * np.cos(start_radians) * np.cos(start_radians)))
#trajectory_points = list(zip(trajectory_x, trajectory_y))
trajectory_points = np.load('trajectory.npy')

start_speed = 370
start_radians = np.deg2rad(42.0)

#setup initial ball state
ball = {}
ball['pos'] = Vector2(START_POS)
ball['velocity'] = Vector2(start_speed * np.cos(start_radians), -start_speed * np.sin(start_radians))
ball['thrown'] = False
ball['trace'] = []

#set numerical integration parameters
step = 0.1
algo = ALGORITHMS[0]

#initialize pygame and display
pygame.init()
pygame.display.set_caption('Trajectories')
window_surface = pygame.display.set_mode((800, 600))

#initialize UI
ui = {}
ui['manager']          = UIManager((800, 600), 'theme.json')
ui['launch_button']    = UIButton(relative_rect=pygame.Rect((260, 500), (80, 80)), text='', object_id=ObjectID(object_id='#launch_button'))
ui['timeout_button']   = UIButton(relative_rect=pygame.Rect((360, 500), (80, 80)), text='', object_id=ObjectID(object_id='#timeout_button'))
ui['phone_button']     = UIButton(relative_rect=pygame.Rect((460, 500), (80, 80)), text='', object_id=ObjectID(object_id='#phone_button'))
ui['time_step_label']  = UILabel(relative_rect=pygame.Rect((10, 10), (120, 30)), text='Zeitschritt:')
ui['time_step']        = UITextEntryLine(relative_rect=pygame.Rect((130, 10), (150, 30)), initial_text = "{:.2f}".format(step))
ui['alrorithm_label']  = UILabel(relative_rect=pygame.Rect((10, 40), (120, 30)), text='Algorithmus:')
ui['algorithm_menu']   = UIDropDownMenu(options_list=ALGORITHMS, starting_option=algo, relative_rect=pygame.Rect((130, 40), (150, 30)))
ui['algorithm_code']   = UIButton(relative_rect=pygame.Rect((10, 80), (300, 80)), text='', object_id=ObjectID(object_id='#code_display_verlet'))
ui['fps']              = UILabel(relative_rect=pygame.Rect((10, 570), (50, 40)), text='FPS: 0', visible=False)

ui['time']             = UILabel(relative_rect=pygame.Rect((550, 10), (150, 30)), text='Zeit:')
ui['score']            = UILabel(relative_rect=pygame.Rect((550, 40), (150, 30)), text='Score:')
ui['opponent']         = UILabel(relative_rect=pygame.Rect((550, 70), (150, 30)), text='Opponent:')

ui['time_display']     = UILabel(relative_rect=pygame.Rect((650, 10), (150, 30)), text='')
ui['score_pts']        = UILabel(relative_rect=pygame.Rect((650, 40), (150, 30)), text='Kein Treffer')
ui['opponent_pts']     = UILabel(relative_rect=pygame.Rect((650, 70), (150, 30)), text='Kein Treffer')
ui['hit_miss_display'] = UILabel(relative_rect=pygame.Rect((TARGET_POS[0]-75, TARGET_POS[1]-35), (150, 20)), text='', object_id=ObjectID(object_id='#hit_miss'))
ui['get_ready']        = UILabel(relative_rect=pygame.Rect((200, 200), (400, 100)), text='Get ready!', object_id=ObjectID(object_id='#ready_text'), visible=False)
ui['game_over']        = UILabel(relative_rect=pygame.Rect((200, 200), (400, 100)), text='Game over!', object_id=ObjectID(object_id='#game_over_text'), visible=False)
ui['timeout']          = UILabel(relative_rect=pygame.Rect((200, 200), (400, 100)), text='Timeout', object_id=ObjectID(object_id='#game_over_text'), visible=False)

ui['launch_button'].disable()
ui['timeout_button'].disable()
ui['phone_button'].disable()
ui['algorithm_menu'].disable()
ui['time_step'].disable()
ui['algorithm_code'].disable()

#load images
ball_image = pygame.image.load('ball.png')
ball_image.convert()
hoop_image = pygame.image.load('hoop.png')
hoop_image.convert()

#initialize the game
clock = pygame.time.Clock()
is_running = True

#initialize network
n = Network(SERVER)
player_number = n.player_number
print("Connected as player {}".format(player_number))
player_update = PlayerUpdate()

def start_throw(ui, ball, start_radians, start_speed):
    ball['pos'] =Vector2(START_POS)
    ball['velocity'] = Vector2(start_speed * np.cos(start_radians), -start_speed * np.sin(start_radians))
    ball['thrown'] = True
    ball['trace'] = []
    ball['trace'].append((ball['pos'].x, ball['pos'].y))
    
    ui['launch_button'].disable()
    step = float(ui['time_step'].get_text())
    algo = ui['algorithm_menu'].selected_option[0]

    #initialize integrator quantities
    ball['prev_pos'] = Vector2(START_POS) - ball['velocity'] * step
    ball['prev_force'] = BALL_MASS * Vector2((0.0, GRAVITY)) - 0.5 * DRAG * BALL_CROSS_SECTION * AIR_DENSITY * ball['velocity'].length_squared() * ball['velocity'].normalize()
    ball['prev_velocity'] = ball['velocity'] - step * ball['prev_force'] / BALL_MASS

    return step, algo

def process_throw(ui, ball, step, algo):
    if ball['thrown']:

        force = BALL_MASS * Vector2((0.0, GRAVITY)) - 0.5 * DRAG * BALL_CROSS_SECTION * AIR_DENSITY * ball['velocity'].length_squared() * ball['velocity'].normalize()

        if algo == 'Euler':
            ball['velocity'] += step / BALL_MASS * force
            ball['pos'] += step * ball['velocity'] #+ 0.5 * step * step / BALL_MASS * force

        elif algo == 'Verlet':
            new_pos = 2 * ball['pos'] - ball['prev_pos'] + step * step / BALL_MASS * force
            ball['velocity'] = (new_pos - ball['prev_pos']) / (2*step)
            ball['prev_pos'] = ball['pos']
            ball['pos'] = new_pos

        elif algo == 'Velocity Verlet':
            ball['pos'] += step * ball['velocity'] + step * step / BALL_MASS * force
            ball['velocity'] += 0.5 * step / BALL_MASS * (force + ball['prev_force'])
            ball['prev_force'] = force

        elif algo == 'Leap Frog':
            ball['next_velocity'] = ball['prev_velocity'] + step / BALL_MASS * force
            ball['pos'] += step * ball['next_velocity']
            ball['velocity'] = 0.5 * (ball['prev_velocity'] + ball['next_velocity'])
            ball['prev_velocity'] = ball['next_velocity']
 
        else:
            print("Unknown algo: " + algo)

        #update trace display
        ball['trace'].append((ball['pos'].x, ball['pos'].y))
        if ball['pos'].y > FLOOR_HEIGHT:
            #np.save('trajectory', ball['trace'])
            ball['thrown'] = False
            ui['launch_button'].enable()
            if np.fabs(ball['pos'].x - TARGET_POS[0]) < ADMISSIBLE_DELTA:
                player_update.best_score = len(ball['trace'])
                ui['hit_miss_display'].set_text('Treffer!')
            else:
                ui['hit_miss_display'].set_text('Daneben!')
            ui['hit_miss_display'].set_active_effect(pygame_gui.TEXT_EFFECT_FADE_OUT, params={'time_per_alpha_change': 0.01})

def draw(ball, trajectory_points, window_surface):
    window_surface.fill(pygame.Color('whitesmoke'))
        
    window_surface.blit(hoop_image, pygame.Rect(Vector2(TARGET_POS) - Vector2(26, 40), (40, 40)))

    pygame.draw.aalines(window_surface, pygame.Color('grey'), False, trajectory_points)
    if len(ball['trace']) > 2:
        pygame.draw.aalines(window_surface, pygame.Color('lightgoldenrod'), False, ball['trace'])

    window_surface.blit(ball_image, pygame.Rect(ball['pos'] - Vector2(20, 20), (40, 40)))

    #pygame.draw.circle(window_surface, pygame.Color('orange'), ball['pos'], BALL_RADIUS)
    #pygame.draw.ellipse(window_surface, pygame.Color('black'), pygame.Rect((TARGET_POS[0]-HOOP_RADIUS, int(round(TARGET_POS[1]-HOOP_RADIUS*HOOP_PERSPECTIVE))), 
    #                                                                       (2*HOOP_RADIUS,             int(round(2*HOOP_RADIUS*HOOP_PERSPECTIVE)))), HOOP_THICKNESS)



while is_running:

    #throtle FPS and update clock
    time_delta = clock.tick(FPS) * 0.001

    #process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == ui['launch_button']:
                step, algo = start_throw(ui, ball, start_radians, start_speed)
            if event.ui_element == ui['timeout_button']:
                player_update.timeout = True
            if event.ui_element == ui['phone_button']:
                player_update.joker = True

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
           if event.ui_element == ui['algorithm_menu']:
                if ui['algorithm_menu'].selected_option[0] == 'Verlet':
                    ui['algorithm_code'].change_object_id(ObjectID(object_id='#code_display_verlet'))
                elif ui['algorithm_menu'].selected_option[0] == 'Velocity Verlet':
                    ui['algorithm_code'].change_object_id(ObjectID(object_id='#code_display_velocity_verlet'))
                elif ui['algorithm_menu'].selected_option[0] == 'Leap Frog':
                    ui['algorithm_code'].change_object_id(ObjectID(object_id='#code_display_leap_frog'))

        ui['manager'].process_events(event)

    #update game
    process_throw(ui, ball, step, algo)
        
    #draw game
    draw(ball, trajectory_points, window_surface)

    #handle networking
    game_state = n.send(player_update)

    #handle state switches
    #switch into ready mode
    if game_state and game_state.state == game_state.STARTING and ui['get_ready'].visible == False:
        ui['get_ready'].visible = True

    #switch into game mode
    if game_state and game_state.state == game_state.RUNNING and ui['get_ready'].visible == True:
        ui['get_ready'].visible = False
        ui['launch_button'].enable()
        ui['timeout_button'].enable()
        ui['phone_button'].enable()
        ui['algorithm_menu'].enable()
        ui['time_step'].enable()

    #switch into timeout mode
    if game_state and game_state.state == game_state.TIMEOUT and ui['timeout'].visible == False:
        ui['timeout'].visible = True
        ball['thrown'] = False

        ui['launch_button'].disable()
        ui['timeout_button'].disable()
        ui['phone_button'].disable()
        ui['algorithm_menu'].disable()
        ui['time_step'].disable()
        
    #switch out of timeout mode
    if game_state and game_state.state == game_state.RUNNING and ui['timeout'].visible == True:
        ui['timeout'].visible = False
        ball['thrown'] = True

        ui['launch_button'].enable()
        ui['phone_button'].enable()
        ui['algorithm_menu'].enable()
        ui['time_step'].enable()
        ui['timeout_button'].enable()            

    #switch out of play state
    if game_state and game_state.state == game_state.ENDED and ui['game_over'].visible == False:
        ui['game_over'].visible = True
        ball['thrown'] = False

        ui['launch_button'].disable()
        ui['timeout_button'].disable()
        ui['phone_button'].disable()
        ui['algorithm_menu'].disable()
        ui['time_step'].disable()

    #switch into idle state
    if game_state and game_state.state == game_state.IDLE and ui['game_over'].visible == True:
        ui['game_over'].visible = False
        ball['pos'] = Vector2(START_POS)

    #disable timeout and joker buttons if used up
    if game_state and game_state.player_joker[player_number] <= 0:
        ui['phone_button'].disable()
    if game_state and game_state.player_timeout[player_number] <= 0:
        ui['timeout_button'].disable()

    #update UI
    ui['manager'].update(time_delta)
    ui['fps'].set_text('FPS: {:2d}'.format(int(clock.get_fps())))
    if game_state:

        ui['time_display'].set_text("{:02d}:{:02d}".format(int(game_state.remaining_play_time / 60), int(game_state.remaining_play_time % 60)))

        if game_state.player_best[player_number] != -1:
            ui['score_pts'].set_text('{}'.format(game_state.player_best[player_number]))
        else:
            ui['score_pts'].set_text('{}'.format('Kein Treffer'))

        if game_state.player_best[(player_number+1)%2] != -1:
            ui['opponent_pts'].set_text('{}'.format(game_state.player_best[(player_number+1)%2]))
        else:
            ui['opponent_pts'].set_text('{}'.format('Kein Treffer'))

        if game_state.player_best[player_number] > 0 and game_state.player_best[(player_number+1)%2] == -1:
            ui['score_pts'].change_object_id(ObjectID(object_id='#winning'))
            ui['opponent_pts'].change_object_id(ObjectID(object_id='#loosing'))            
        elif game_state.player_best[player_number] == -1 and game_state.player_best[(player_number+1)%2] > 0:
            ui['score_pts'].change_object_id(ObjectID(object_id='#loosing'))
            ui['opponent_pts'].change_object_id(ObjectID(object_id='#winning'))            
        elif game_state.player_best[player_number] < game_state.player_best[(player_number+1)%2]:
            ui['score_pts'].change_object_id(ObjectID(object_id='#winning'))
            ui['opponent_pts'].change_object_id(ObjectID(object_id='#loosing'))
        elif game_state.player_best[(player_number+1)%2] > 0 and game_state.player_best[player_number] > game_state.player_best[(player_number+1)%2]:
            ui['score_pts'].change_object_id(ObjectID(object_id='#loosing'))
            ui['opponent_pts'].change_object_id(ObjectID(object_id='#winning'))
        else:
            ui['score_pts'].change_object_id(None)
            ui['opponent_pts'].change_object_id(None)

    ui['manager'].draw_ui(window_surface)

    #update display
    pygame.display.update()
