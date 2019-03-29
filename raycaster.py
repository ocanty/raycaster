
import sdl2
import sdl2.ext
import random
import sys
import math
import time
        
class Raycaster(sdl2.ext.Renderer):
    def __init__(self):
        sdl2.ext.init()
        self.camera_fov         = math.radians(90)
        self.camera_angle       = math.radians(30)
        self.camera_pos         = (2.5,2.5)

        self.proj_plane_size    = (768,512)
        self.proj_plane_dist    = self.proj_plane_size[0]/math.tan(self.camera_fov/2)

        
        self.window = sdl2.ext.Window(
            title   = "Raycaster",
            size    = self.proj_plane_size,
            flags   = sdl2.SDL_WINDOW_SHOWN
        )

        super().__init__(self.window)

        self.factory            = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE, renderer=self)
        self.sprite_renderer    = self.factory.create_sprite_render_system(self.window)
        self.render_sprite      = self.factory.create_software_sprite((self.proj_plane_size))
        self.render_buffer      = sdl2.ext.pixels2d(self.render_sprite)

        self.render_buffer[202] = 7777777
        self.running = False

        # build a randomized world
        self.world = [
            sorted([False,False,False,False,False,False,True]*2,key= lambda r : random.randint(0,23)) for x in range(14)
        ]

        self.keys = { }

    def handle_events(self):
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                break

            if event.type == sdl2.SDL_KEYDOWN:
                self.keys[event.key.keysym.sym] = True
                continue

            if event.type == sdl2.SDL_KEYUP:
                self.keys[event.key.keysym.sym] = False
                continue

    def is_key_down(self, key):
        return key in self.keys and self.keys[key]

    def handle_input(self):
        if self.is_key_down(sdl2.SDLK_RIGHT):
            self.camera_angle = self.camera_angle + 0.04

        if self.is_key_down(sdl2.SDLK_LEFT):
            self.camera_angle = self.camera_angle - 0.04

        if self.is_key_down(sdl2.SDLK_UP):
            self.camera_pos = (
                self.camera_pos[0] + 0.1*math.cos(self.camera_angle),
                self.camera_pos[1] - 0.1*math.sin(self.camera_angle)
            )

        if self.is_key_down(sdl2.SDLK_DOWN):
            self.camera_pos = (
                self.camera_pos[0] - 0.1*math.cos(self.camera_angle),
                self.camera_pos[1] + 0.1*math.sin(self.camera_angle)
            )

    # Test if an x,y (as ints, not floats!) is a wall
    # Returns the grid element if true
    def test_world(self, point):
        if len(self.world) > point[1] and point[1] >= 0:
            if len(self.world[point[1]]) > point[0] and point[0] >= 0:
                return self.world[point[1]][point[0]]

        return False

    # Convert a world point to a minimap point
    @staticmethod
    def world_to_minimap_point(point):
        return (int(point[0]*30 + 10), int(point[1]*30 + 10))

    @staticmethod
    def distance(point1, point2):
        return math.sqrt(math.pow(point1[0] - point2[0],2) + math.pow(point1[1] - point2[1],2))

    def draw_ray_on_minimap(self, ray_pos, ray_angle, scale, color):
        minimap_pos = Raycaster.world_to_minimap_point(ray_pos)
        
        # get a direction vector, scale it and convert from local to global by adding origin
        super().draw_line(
            minimap_pos + 
            (minimap_pos[0] + int(scale*math.cos(ray_angle)), 
             minimap_pos[1] - int(scale*math.sin(ray_angle))), 
            color
        )

    def trace_ray_on_world(self, ray_pos, ray_angle):
        hit_x = False
        hit_y = False
        distance_hit_x = 99999
        distance_hit_y = 99999

        # find the grid position that ray_pos is on
        ray_grid_pos = list(map(math.floor,ray_pos))

        ray_slope = math.tan(ray_angle)

        # 180 to 0
        facing_north = ray_angle < math.pi and ray_angle > 0
        facing_south = not facing_north

        # we face east if we're our angle is 90 > a > 270 (assuming wrap around)
        facing_east = (ray_angle < (math.pi/2) and ray_angle > 0) or (ray_angle < (math.pi*2) and ray_angle > (math.pi*1.5) ) 
        facing_west = not facing_east

        # find an equation of a line for the ray
        # y - y1 = m(x - x1)
        # where (x1,y1) = ray pos
        # y = m(x - x1) + y1
        # 
        # x = ((y - y1) / m) + x1
        # y = m(x - x1) + y1
        #                       v-- note: this is reversed due to our different coordinate system
        #                                   i.e top left is 0,0 rather than bottom left
        ray_y = lambda x: (ray_slope * (ray_pos[0] - x)) + ray_pos[1]

        # x = ((y - y1) / m) + x1
        #                       v-- note: again different coordinate system
        ray_x = lambda y: ((ray_pos[1] - y) / ray_slope) + ray_pos[0]

        # draw ray
        # if abs(self.camera_angle - ray_angle) < 0.05:
        #     self.draw_ray_on_minimap(self.camera_pos, ray_angle, 320, color=sdl2.ext.Color(255,0,0))

        # find horizontal and vertical grid intersections until we find a wall
        # or we time out after 15 intersections
        i = 0
        while(i < 15):
            # add the offset for the intersection we're testing against
            # i.e if we're facing north, we're staying in our current grid position
            # but if we're facing south the next grid is our current grid y + 1
            # we also need to do a grid offset for the current intersection
            x = ray_grid_pos[0] + i + 1 if facing_east else ray_grid_pos[0] - i 
            y = ray_grid_pos[1] + i + 1 if facing_south else ray_grid_pos[1] - i

            #print(facing_north, facing_east)
            horiz_intersection = [ray_x(y), y]
            vert_intersection  = [x, ray_y(x)]

            # #draw intersections on minimap
            # if abs(self.camera_angle - ray_angle) < 0.05:
            #     super().fill(
            #         Raycaster.world_to_minimap_point(horiz_intersection) + (3,3), 
            #         sdl2.ext.Color(127,64,255)
            #     )

            #     super().fill(
            #         Raycaster.world_to_minimap_point(vert_intersection) + (3,3), 
            #         sdl2.ext.Color(255,0,127)
            #     )

            # what grid location do we pick, i.e 
            # we can have grid intersections on a grid line
            # but we need to decide which actual world element to choose
            # i.e NSEW of that boundary
            horiz_grid = list(map(math.floor, [horiz_intersection[0], horiz_intersection[1] - 1 if facing_north else horiz_intersection[1]]))
            vert_grid = list(map(math.floor, [vert_intersection[0] - 1 if facing_west else vert_intersection[0], vert_intersection[1]]))

            if self.test_world(horiz_grid) and not hit_x:
                # if abs(self.camera_angle - ray_angle) < 0.05:   
                #     super().fill(
                #         Raycaster.world_to_minimap_point(horiz_grid) + (30,30), 
                #         sdl2.ext.Color(255,64,255,12)
                #     )
                hit_x = True
                distance_hit_x = Raycaster.distance(self.camera_pos, horiz_intersection)
                # if abs(self.camera_angle - ray_angle) < 0.05:
                #     super().fill(
                #         Raycaster.world_to_minimap_point(horiz_intersection) + (3,3), 
                #         sdl2.ext.Color(0,255,0)
                #     )

            if self.test_world(vert_grid) and not hit_y:
                # if abs(self.camera_angle - ray_angle) < 0.05:   
                #     super().fill(
                #         Raycaster.world_to_minimap_point(vert_grid) + (30,30), 
                #         sdl2.ext.Color(255,64,255,64)
                #     )
                hit_y = True
                distance_hit_y = Raycaster.distance(self.camera_pos, vert_intersection)
                # if abs(self.camera_angle - ray_angle) < 0.05:
                #     super().fill(
                #         Raycaster.world_to_minimap_point(vert_intersection) + (3,3), 
                #         sdl2.ext.Color(127,127,127)
                #     )

            if hit_x and hit_y:
                # return distance and correct fish eye lens
                return True, min(distance_hit_x, distance_hit_y) * math.cos(self.camera_fov/2)

            i = i + 1

        return (hit_x or hit_y), min(distance_hit_x,distance_hit_y) * math.cos(self.camera_fov/2)
            
    def draw_world(self):
        # start at furthest end of fov
        ray_angle = self.camera_angle - (self.camera_fov/2)

        # increment equal angles for each pixel on screen
        ray_angle_increment = self.camera_fov / self.proj_plane_size[0]

        # each vertical line on screen
        for x in range(self.proj_plane_size[0]):
            # prevent angle overflow
            ray_angle = ray_angle % (math.pi*2)

            if(x%3 == 0):
                hit, distance = self.trace_ray_on_world(self.camera_pos, ray_angle)

                if hit:
                    height = int(((1/distance)*self.proj_plane_dist)*0.5)
                    #print(distance)
                    super().fill((x-2, int((self.proj_plane_size[1]/2)-(height/2)), 3, height), color=sdl2.ext.Color(min(int((distance/6)*255),255),119,131))

            ray_angle = ray_angle + ray_angle_increment


        self.sprite_renderer.render(self.render_sprite, x=0, y=0)
    def draw(self):
        super().clear()
        # keep in 360 range
        self.camera_angle = self.camera_angle % (math.pi*2)

        # draw mini map
        # for y, x_list in enumerate(self.world):
        #     for x, tile in enumerate(self.world[y]):
        #         super().fill(
        #             Raycaster.world_to_minimap_point((x,y)) + (30,30), 
        #             sdl2.ext.Color(255,255,255) if tile == True else sdl2.ext.Color(32,32,32)
        #         )
        
        minimap_camera_pos = Raycaster.world_to_minimap_point(self.camera_pos)

        # draw camera pos on minimap
        super().fill(
            minimap_camera_pos + (5,5), 
            sdl2.ext.Color(255,215,0)
        )

        self.draw_ray_on_minimap(self.camera_pos, self.camera_angle, 128, sdl2.ext.Color(255,215,0))
        self.draw_world()

        super().present()
        
    def run(self) -> int:
        self.running = True

        while self.running:
            self.handle_events()
            self.handle_input()
            self.draw()
        
        sdl2.ext.quit()
        return 0 

if __name__ == "__main__":
    raycaster = Raycaster()
    sys.exit(raycaster.run())