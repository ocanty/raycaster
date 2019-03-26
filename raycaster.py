
import sdl2
import sdl2.ext
import random
import sys
import math
        
class Raycaster(sdl2.ext.Renderer):
    def __init__(self):
        sdl2.ext.init()

        self.proj_plane_size    = (640,480)
        self.camera_fov         = math.radians(90)
        self.camera_angle       = math.radians(30)
        self.camera_pos         = (2.5,2.5)

        super().__init__(
            sdl2.ext.Window(
            title   = "Raycaster",
            size    = self.proj_plane_size,
            flags   = sdl2.SDL_WINDOW_SHOWN
        ))

        self.running = False

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
                break
            
            if event.type == sdl2.SDL_KEYUP:
                self.keys[event.key.keysym.sym] = False
                break

    def handle_input(self):
        if sdl2.SDLK_LEFT in self.keys and self.keys[sdl2.SDLK_LEFT]:
            self.camera_angle = self.camera_angle + 0.01
        
        if sdl2.SDLK_RIGHT in self.keys and self.keys[sdl2.SDLK_RIGHT]:
            self.camera_angle = self.camera_angle - 0.01

        if sdl2.SDLK_UP in self.keys and self.keys[sdl2.SDLK_UP]:
            self.camera_pos = (
                self.camera_pos[0] + 0.05*math.cos(self.camera_angle),
                self.camera_pos[1] - 0.05*math.sin(self.camera_angle)
            )

        if sdl2.SDLK_DOWN in self.keys and self.keys[sdl2.SDLK_DOWN]:
            self.camera_pos = (
                self.camera_pos[0] - 0.05*math.cos(self.camera_angle),
                self.camera_pos[1] + 0.05*math.sin(self.camera_angle)
            )



    # Convert a world point to a screen point
    @staticmethod
    def world_to_minimap_point(point):
        return (int(point[0]*15 + 10), int(point[1]*15 + 10))

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
        # find the grid position that ray_pos is on
        ray_grid_pos = tuple(map(math.floor,ray_pos))

        ray_slope = math.tan(ray_angle) or 0.0000000001

        facing_north = ray_angle < math.radians(180) and ray_angle > math.radians(0)
        facing_south = not facing_north

        facing_east = ray_angle < math.radians(90) and ray_angle > math.radians(270)
        facing_west = not facing_east

        # find an equation of a line for the ray
        # y - y1 = m(x - x1)
        # where (x1,y1) = ray pos
        # y = m(x - x1) + y1
        # 
        # x = ((y - y1) / m) + x1

        # y = m(x - x1) + y1
        ray_y = lambda x: (ray_slope * (ray_pos[0] - x)) + ray_pos[1]

        # x = ((y - y1) / m) + x1
        #                       v-- note: this is reversed due to our different coordinate system
        #                                   i.e top left is 0,0 rather than bottom left
        ray_x = lambda y: ((ray_pos[1] - y) / ray_slope) + ray_pos[0]

        # find horizontal and vertical grid intersections until we find a wall
        # or we time out after 15 intersections
        i = 0
        while(i < 15):
            if facing_north:
                horiz_intersection = (ray_x(ray_grid_pos[1]), ray_grid_pos[1])
            else:
                horiz_intersection = (ray_x(ray_grid_pos[1]+1), ray_grid_pos[1]+1)

            if facing_east:
                vert_intersection = (ray_grid_pos[0], ray_y(ray_grid_pos[0]))
            else:
                vert_intersection = (ray_grid_pos[0]+1, ray_y(ray_grid_pos[0]+1))

            super().fill(
                Raycaster.world_to_minimap_point(horiz_intersection) + (3,3), 
                sdl2.ext.Color(127,64,255)
            )


            super().fill(
                Raycaster.world_to_minimap_point(vert_intersection) + (3,3), 
                sdl2.ext.Color(255,0,127)
            )

            i = i + 1
            
    
        # print(math.degrees(ray_angle))
 
        # x_offset_to_first_intersection = (ray_pos[1] - ray_grid_pos[1])/ray_slope
    
        # super().fill(
        #     Raycaster.world_to_minimap_point( (ray_pos[0] + x_offset_to_first_intersection, ray_grid_pos[1])) + (3,3), 
        #     sdl2.ext.Color(127,64,255)
        # )
            



    def draw_world(self):
        self.camera_angle = self.camera_angle % math.radians(360)
        ray_angle = self.camera_angle - (self.camera_fov/2)

        ray_angle_increment = self.camera_fov / self.proj_plane_size[0]

        debug_draw = 0
        # while(ray_angle < (self.camera_angle + (self.camera_fov/2))):
            
        #     #draw every 36th ray in minimap
        #     if(debug_draw % 36 == 0):
        #         self.draw_ray_on_minimap(self.camera_pos, ray_angle, 320, color=sdl2.ext.Color(255,0,0))
        #     debug_draw = debug_draw + 1
        self.trace_ray_on_world(self.camera_pos, self.camera_angle)

            # ray_angle = ray_angle + ray_angle_increment



    def draw(self):
        super().clear()

        # draw mini map
        for y, x_list in enumerate(self.world):
            for x, tile in enumerate(self.world[y]):
                super().fill(
                    Raycaster.world_to_minimap_point((x,y)) + (15,15), 
                    sdl2.ext.Color(255,255,255) if tile == True else sdl2.ext.Color(32,32,32)
                )
        
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


        return 0 

            


if __name__ == "__main__":
    raycaster = Raycaster()
    sys.exit(raycaster.run())