class GameState:
    IDLE = -1
    STARTING = 3
    RUNNING = 2
    TIMEOUT = 1
    ENDED = 0

    STARTUP_TIME = 5
    PLAY_TIME = 300
    ENDED_TIME = 60
    TIMEOUT_TIME = 30

    def __init__(self):
        self.player_best        = [-1, -1] #-1 means no score, positive number means best number of steps
        self.player_timeout     = [1, 1] #number of timouts left
        self.player_joker       = [1, 1] #0 means joker not active, 1 means joker active, -1 means no joker left
        
        self.state              = self.IDLE
        self.time_in_state      = 0
        self.state_start_time   = 0
        self.remaining_play_time = 0
        self.save_remaining_play_time = 0
