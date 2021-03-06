# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 08:21:40 2020

@author: coldhenry
"""
import math
import numpy as np
from pqdict import pqdict

class Dstarlite_Planner:
    
    def __init__(self, blocks, boundary, obsize=15, reso=0.1):       
        
        # resolution of the grid map
        self.reso = reso
        # observe cube size
        self.obsize = obsize
        # key modifier
        self.km = 0
        # record the true path
        self.final_path = []
        # record the optimal path at each iteration
        self.current_path = []
        # get the whole map (obstacle included)
        self.get_obstacle_map(blocks,boundary)
        # get the map from robot perspective
        self.currMap = np.array([[[False for i in range(self.zwidth)]for j in range(self.ywidth)]for k in range(self.xwidth)])
          
    def planning(self,start,goal):
        '''
        ==== D* algorithm ====
        1. Initialize all nodes
        2. Best-first search until n_start is consistent with neighbors and expanded
        3. move to the next best node
        4. If any edge costs change:
            a. track how heuristics have changed
            b. update sources nodes of changed edges
        5. repeat step 2.
        ----------------------------------
        ==== Implementation ====
        1. node representation: [type] tuple, [form] (x,y,z)
        2. node set: [type] dict, [form] {node: [g, rhs]}
        3. queue: [type] pqdict, [form] {node: <key>}
        '''
        # actual length
        sx, sy, sz = start[0], start[1], start[2]
        gx, gy, gz = goal[0], goal[1], goal[2]
        # grid index
        s_x, s_y, s_z = self.length2grid(sx, self.minx),self.length2grid(sy, self.miny),self.length2grid(sz, self.minz)
        g_x, g_y, g_z = self.length2grid(gx, self.minx),self.length2grid(gy, self.miny),self.length2grid(gz, self.minz)
        print("start: {s}, goal: {g}".format(s=start, g=goal))
        print("start point: {a},{b},{c}".format(a=s_x,b=s_y,c=s_z))        
        print("goal point: {a},{b},{c}".format(a=g_x,b=g_y,c=g_z)) 
        
        # start/goal coordinate
        self.n_start = tuple([s_x, s_y, s_z])
        self.n_goal = tuple([g_x, g_y, g_z]) 
        
        # collect nodes and info: key: node position / value; [g,rhs]
        self.nodeDict = {}
        self.nodeDict[self.n_start] = [np.inf, np.inf]
        self.nodeDict[self.n_goal] = [np.inf, 0] # rhs(goal)=0. always
        
        # record the last step where the agent was
        self.n_last = self.n_start
        # start the first observation
        self.updateObstacleMap(self.n_last)
        
        # add the first node into the final path
        self.final_path.append(tuple([sx, sy, sz]))
        
        # create a min queue and put in the goal node (backward search)
        self.queue = pqdict()
        self.queue.additem(self.n_goal, self.key(self.n_goal))
        
        while(1):
            
            topPair = self.queue.topitem()
            topKey = self.queue[topPair[0]]
            #print("topKey",topKey)
            #print("key of currnode: {k1}, key of start: {k2}".format(k1=self.key(currNode), k2=self.key(self.n_start)))
            # if the dequeud one is the start, path found!
            if(topKey>=self.key(self.n_start) and self.consistent(self.n_last)):
                print("the start node is consistent and the key of current value is larger than the start node one")
                # publish the optimal path
                current_path = self.get_path()
                
                # follow the path until new obstacles are observed
                self.n_last, obstacle = self.moveAgent()
                
                # the agent reached the goal
                if(self.n_last == self.n_goal):
                    print("Reached the goal!")
                    return np.array(self.final_path)
                
                # update the key modifier km
                self.km += self.heuristics(self.n_last, self.n_start)
                
                print("now obstacle",obstacle)
                # update the rhs of source nodes
                obs_pair = tuple([obstacle,self.nodeDict[obstacle]])
                self.update_RHS(obstacle,OBSTACLE = True)
                self.update_Neighbor(obs_pair)            

            # dequeue a node, update this node and its neighbor
            pair = self.queue.popitem()
            currNode = pair[0]
            if self.consistent(currNode):
                continue
            #print("\n====NEW iteration: dequeue node {s} with cost {c}".format(s=pair[0], c=self.nodeDict[pair[0]]))
            
            # update the g value of the dequeued node
            self.update_G(pair)
            # update the rhs value of its neighbors
            self.update_Neighbor(pair)
            #print(self.n_last in self.queue)
            
#%% Functions      
        
    def update_G(self, pair):
        # update the node / pair[0]: coordinate(tuple)
        g, rhs = self.nodeDict[pair[0]][0], self.nodeDict[pair[0]][1]
        if(g > rhs): # overconsistent
            #print("====Current node overconsistent!")
            self.nodeDict[pair[0]][0] = rhs
            return "overconsistent"
            
        elif(g < rhs): # underconsistent.
            #print("====Current node underconsistent!")    
            self.nodeDict[pair[0]][0] = np.inf
            return "underconsistent"
        else:
            #print("====Current node consistent!")
            return "consistent"
        
            
    def update_Neighbor(self, pair):
        '''
        update the RHS value of node's neighbor
        '''
        node = pair[0]
        #print("====Update the neighbor of node {idx}".format(idx=node))
               
        # looking for valid node j
        for motion in self.expand6():
            
            dx, dy, dz  = motion[0], motion[1], motion[2]
            tmp_idx = tuple([node[0]+dx, node[1]+dy, node[2]+dz])
            #print("neighbor:",tmp_idx)
            if(self.validNode(tmp_idx)):
                self.update_RHS(tmp_idx)
                
   
    def update_RHS(self, tmp_idx, OBSTACLE=False):
        
        # iterate through the neighbor of the neighbor of the dequeued node
        # to update minimal rhs value 
        if not OBSTACLE:
            _, tmp_rhs = self.findMin(tmp_idx)
        else:
            tmp_rhs = np.inf
        
        # if the node exists, check if it needs update
        if tmp_idx in self.nodeDict:
            if(tmp_idx == self.n_goal): # goal's rhs remains 0
                self.nodeDict[tmp_idx][1] = 0
            else:
                self.nodeDict[tmp_idx][1] = tmp_rhs
        # create a new node pair
        else:
            if(tmp_idx == self.n_goal): # goal's rhs remains 0
                self.nodeDict[tmp_idx] = [np.inf, 0]
            else:
                #print("find new node: {n}, value <{g},{rhs}>".format(n=tmp_idx, g=np.inf, rhs=tmp_rhs))
                self.nodeDict[tmp_idx] = [np.inf, tmp_rhs]
        # if g value and rhs value not equal (inconsistent), queue it
        if not self.consistent(tmp_idx):
            if tmp_idx in self.queue:
                #print("update node {s} in queue with key {k}".format(s=tmp_idx,k=self.key(tmp_idx)))
                self.queue[tmp_idx] = self.key(tmp_idx)
            else:
                #print("add node {s} to queue".format(s=tmp_idx))
                self.queue.additem(tmp_idx, self.key(tmp_idx))
   
    
    def key(self, node):
        g, rhs = self.nodeDict[node][0], self.nodeDict[node][1]
        cost1 = min(g,rhs) + self.heuristics(node,self.n_last)+ self.km
        cost2 = min(g,rhs)
        #print("key: <{c1}, {c2}>".format(c1=cost1,c2=cost2))
        return [cost1,cost2] 
        
    def heuristics(self,node,n_last):
        dx,dy,dz = abs(node[0]-n_last[0]), abs(node[1]-n_last[1]), abs(node[2]-n_last[2])
        return dx+dy+dz
    
    def validNode(self, node):
        
        x,y,z = node[0], node[1], node[2]
        
        px = self.grid2length(x, self.minx)
        py = self.grid2length(y, self.miny)
        pz = self.grid2length(z, self.minz)
        
        # possible node check
        if px < self.minx or px >= self.maxx:
            return False
        elif py < self.miny or py >= self.maxy:
            return False
        elif pz < self.minz or pz >= self.maxz:
            return False
        
        if x < 0 or x >= self.xwidth:
            return False
        elif y < 0 or y >= self.ywidth:
            return False
        elif z < 0 or z >= self.zwidth:
            return False
        
        return True
        
    def isObstacle(self, node):   
        x,y,z = node[0], node[1], node[2]
        return self.currMap[x][y][z]
    
    def consistent(self, node):
        return self.nodeDict[node][0] == self.nodeDict[node][1]
        
    def get_obstacle_map(self,blocks,boundary):
    
        # real length of obstacles (unit:m)
        self.minx = boundary[0,0]
        self.miny = boundary[0,1]
        self.minz = boundary[0,2]
        self.maxx = boundary[0,3]
        self.maxy = boundary[0,4]
        self.maxz = boundary[0,5]
        print("minx: {a}, maxx {b}".format(a= self.minx, b=self.maxx))
        print("miny: {c}, maxy: {d}".format(c= self.miny, d=self.maxy))
        print("minz: {e}, maxz: {f}".format(e= self.minz, f=self.maxz))
        
        self.xwidth = round((self.maxx - self.minx)/ self.reso).astype(int)
        self.ywidth = round((self.maxy - self.miny)/ self.reso).astype(int)
        self.zwidth = round((self.maxz - self.minz)/ self.reso).astype(int)
        print("xwidth: {a}, ywidth: {b}, zwidth: {c}".format(a=self.xwidth, b=self.ywidth, c=self.zwidth))
        
        # obstacle map generation
        self.obmap = np.array([[[False for i in range(self.zwidth)]for j in range(self.ywidth)]for k in range(self.xwidth)])
        
        # fill the obstacles
        for i in range(blocks.shape[0]): # for each obstacle
            obs = blocks[i]
            # transform the coordinate and regulate
            ox_min, ox_max = self.length2grid(obs[0],self.minx),self.length2grid(obs[3],self.minx)
            oy_min, oy_max = self.length2grid(obs[1],self.miny),self.length2grid(obs[4],self.miny)
            oz_min, oz_max = self.length2grid(obs[2],self.minz),self.length2grid(obs[5], self.minz)
            print("obstacle size: x: {x1}/{x2}, y: {y1}/{y2}, z:{z1}/{z2}".format(x1=ox_min,x2=ox_max,y1=oy_min,y2=oy_max,z1=oz_min,z2=oz_max))
            if ox_max > self.xwidth:
                ox_max = self.xwidth-1
            if oy_max > self.ywidth:
                oy_max = self.ywidth-1
            if oz_max > self.zwidth:
                oz_max = self.zwidth-1
            # iterate through each coordinate           
            for bx in range(ox_min, ox_max):
                for by in range(oy_min, oy_max):
                    for bz in range(oz_min, oz_max):
                        #print("x: {a}, y: {b}, z: {c}".format(a=bx,b=by,c=bz))
                        self.obmap[bx][by][bz] = True      
    
    def updateObstacleMap(self, node):
        x,y,z = node[0], node[1], node[2]
        radius = int((self.obsize-1)/2)
        # fit the observation cube 
        coord = self.validGrid(x, y, z, radius)
        # grab the observation cube from the actual map
        observed = self.obmap[coord[0]:coord[1],coord[2]:coord[3],coord[4]:coord[5]]
        # add into the explored map
        self.currMap[coord[0]:coord[1],coord[2]:coord[3],coord[4]:coord[5]] = \
            np.logical_or(self.currMap[coord[0]:coord[1],coord[2]:coord[3],coord[4]:coord[5]], observed)
            
    def validGrid(self,x,y,z,radius):
        
        if x-radius < 0:
            x_low = 0
        else:
            x_low = x-radius      
        if y-radius < 0:
            y_low = 0
        else:
            y_low = y-radius           
        if z-radius < 0:
            z_low = 0
        else:
            z_low = z-radius
            
        if x+radius+1 >= self.xwidth:
            x_up = self.xwidth
        else:
            x_up = x+radius+1
        if y+radius+1 >= self.ywidth:
            y_up = self.ywidth
        else:
            y_up = y+radius+1
        if z+radius+1 >= self.zwidth:
            z_up = self.zwidth
        else:
            z_up = z+radius+1
            
        return [x_low, x_up, y_low, y_up, z_low, z_up]
        
    def get_path(self):
        
        print("Generate the current path from node {s}...".format(s=self.n_last))
        
        # everytime we derive a updated path, clear the old one
        self.current_path.clear()
        self.current_path.append(self.n_last)
        
        count = 0
        
        nextState = self.nextMin(self.n_last)
        
        while(nextState != self.n_goal):
            # count+=1
            # if count%50 == 0:
            #     break
            self.current_path.append(nextState)
            nextState = self.nextMin(nextState)
        
        # append the first state
        self.current_path.append(nextState)
        
        print("Done, path length",len(self.current_path))
        return self.current_path
    
    def moveAgent(self):
        
        blocked = False
        agentPos = self.n_last
        count = 1
        
        print("Moving agent from node {s}...".format(s=agentPos))
        
        # reach the gaol
        if agentPos == self.n_goal:
            print("The agent already reached the goal")
            return agentPos
        
        while not blocked:
            
            nextNode = self.current_path[count]
            
            # the next step is valid in this current map
            if self.validNode(nextNode) and not self.isObstacle(nextNode):
                print("next node: {s} is valid and not obstacle".format(s=nextNode))
                
                # agent move to next step
                agentPos = nextNode
                pos = self.grid2pos(agentPos)
                count += 1
                
                # reach the gaol
                if agentPos == self.n_goal:
                    print("The agent has reached the goal!")
                    self.final_path.append(pos)
                    return agentPos, (-1,-1,-1)
                
                # add this step into the final path             
                self.final_path.append(pos)
                
                # update the map through this new position
                self.updateObstacleMap(agentPos)
                
            # the next node is actually an obstacle
            elif self.isObstacle(nextNode):
                print("Hit the obstacle! The agent is now at node {n}".format(n=agentPos))
                blocked = True
                print("at this time the agent cost is ",self.nodeDict[agentPos])
                return agentPos, nextNode
            
            # the next node is not in the map
            else:
                raise ValueError("Node not in the map")
                
    def grid2pos(self,agentPos):
        px = self.grid2length(agentPos[0], self.minx) 
        py = self.grid2length(agentPos[1], self.miny)
        pz = self.grid2length(agentPos[2], self.minx) 
        return tuple([px,py,pz])
            
    def findMin(self, n_last):
        
        min_cost = np.inf
        min_idx = ()
        
        if self.isObstacle(n_last):
            return (-1,-1), np.inf
        
        # iterate through the successor of the node
        for motion in self.expand6():
            
            dx, dy, dz, c_ij = motion[0], motion[1], motion[2], motion[3]
            tmp_idx = tuple([n_last[0]+dx, n_last[1]+dy, n_last[2]+dz])
                        
            if(tmp_idx in self.nodeDict):
                tmp_node = self.nodeDict[tmp_idx]
                # if the node is obstacle, set the edge cost to infinity
                if self.isObstacle(tmp_idx):
                    c_ij = np.inf              
                if(tmp_node[0]+c_ij < min_cost):
                    min_cost = tmp_node[0]+c_ij
                    min_idx = tmp_idx
        
        #print("next min node: {s}".format(s=min_idx))
        return min_idx, min_cost   
    
    def nextMin(self, node):
        
        cur_node = self.nodeDict[node]
        min_cost = np.inf
        min_idx = ()
        
        # iterate through the successor of the node
        for motion in self.expand6():

            dx, dy, dz, c_ij = motion[0], motion[1], motion[2], motion[3]
            tmp_idx = tuple([node[0]+dx, node[1]+dy, node[2]+dz])
                        
            if tmp_idx in self.nodeDict:     
                tmp_node = self.nodeDict[tmp_idx]
                
                if self.isObstacle(tmp_idx):
                    c_ij = np.inf
                if(tmp_node[1]+c_ij< min_cost):
                    min_cost = tmp_node[1]+c_ij
                    min_idx = tmp_idx
            
        return min_idx 
    
    def length2grid(self, pos, min_p):
        grid = (round((pos-min_p) / self.reso)).astype(int)        
        return grid
    
    def grid2length(self, index, min_pos):       
        original_length = index* self.reso + min_pos
        return original_length 
        
    @staticmethod
    def expand26():
        # dx, dy, dz, cost
        motion = [[1,0,1,math.sqrt(2)] , [0,1,1,math.sqrt(2)]  , [-1,0,1,math.sqrt(2)]  , [0,-1,1,math.sqrt(2)] ,
                  [1,1,1,math.sqrt(3)] , [1,-1,1,math.sqrt(3)] , [-1,-1,1,math.sqrt(3)] , [-1,1,1,math.sqrt(3)] ,
                  [1,0,-1,math.sqrt(2)], [0,1,-1,math.sqrt(2)] , [-1,0,-1,math.sqrt(2)] , [0,-1,-1,math.sqrt(2)],
                  [1,1,-1,math.sqrt(3)], [1,-1,-1,math.sqrt(3)], [-1,-1,-1,math.sqrt(3)], [-1,1,-1,math.sqrt(3)],
                  [1,0,0,1]            , [0,1,0,1]             , [-1,0,0,1]             , [0,-1,0,1]            ,
                  [1,1,0,math.sqrt(2)] , [1,-1,0,math.sqrt(2)] , [-1,-1,0,math.sqrt(2)] , [-1,1,0,math.sqrt(2)] ,
                  [0,0,1,1]            , [0,0,-1,1]]

        return motion
    
    @staticmethod
    def expand6():
        # dx, dy, dz, cost
        motion = [[1,0,0,1], [0,1,0,1], [-1,0,0,1], [0,-1,0,1] ,
                  [0,0,1,1], [0,0,-1,1]]

        return motion
        
if __name__ == '__main__':
    
    mapdata = np.loadtxt('./maps/single_cube.txt',dtype={'names': ('type', 'xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b'),\
                                    'formats': ('S8','f', 'f', 'f', 'f', 'f', 'f', 'f','f','f')})
    blockIdx = mapdata['type'] == b'block'
    boundary = mapdata[~blockIdx][['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']].view('<f4').reshape(-1,11)[:,2:]
    blocks = mapdata[blockIdx][['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax','r','g','b']].view('<f4').reshape(-1,11)[:,2:]
    myPlanner = Dstar_Planner(blocks,boundary)
    
    print(myPlanner.grid2length((250), 0))
    
    start = np.array([5.0, 3.0, 3.])
    goal = np.array([5.0, 7.0, 3.])
    
    #final_path = np.array(myPlanner.planning(start, goal), dtype='float')
    #nodeDict = myPlanner.planning(start, goal)
    