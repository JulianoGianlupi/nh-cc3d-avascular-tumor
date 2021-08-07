from cc3d.cpp.PlayerPython import * 
from cc3d import CompuCellSetup

from cc3d.core.PySteppables import *
import numpy as np


class ConstraintInitializerSteppable(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self,frequency)

    def start(self):
    
        for cell in self.cell_list:

            cell.targetVolume = 64
            cell.lambdaVolume = 8.0
        
        
class GrowthSteppable(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self, frequency)
        
        self.p_q = 0.5*100/(np.e/2) # threshold to change from prolif to quies
        self.q_p = 1.1*self.p_q # threshold to change from quies to prolif
        self.q_n = 0.5*100/(np.e) # threshold to change from quies to necro

    def step(self, mcs):
        
        # iterating over all cells in simulation    
        if not mcs:
            for cell in self.cell_list:
                # types thrs
                cell.dict['p_q'] = self.p_q
                cell.dict['q_p'] = self.q_p
                cell.dict['q_n'] = self.q_n
                # uptake
                cell.dict['upt_max'] = 1
                cell.dict['upt_rel'] = .1
                # growth rate
                cell.dict['growth'] = 0.5
        
        
        
        field = self.field.nutr
        # Make sure Secretion plugin is loaded
        # make sure this field is defined in one of the PDE solvers
        # you may reuse secretor for many cells. Simply define it outside the loop
        secretor = self.get_field_secretor("nutr")
        # list of  cell types (capitalized)
        for cell in self.cell_list_by_type(self.PROLIF):
            # arguments are: cell, max uptake, relative uptake
            r = secretor.uptakeInsideCellTotalCount(cell, cell.dict['upt_max'], cell.dict['upt_rel'])
            concentrationAtCOM = field[int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)]
            # you can access/manipulate cell properties here
            # print ("id=", cell.id, r.tot_amount)
            if concentrationAtCOM < cell.dict['p_q']:
                # READ/WRITE  ACCESS                
                cell.type = self.QUIES
            else:
                cell.targetVolume += cell.dict['growth'] * abs(r.tot_amount) / cell.volume
        
        for cell in self.cell_list_by_type(self.QUIES):
            # you can access/manipulate cell properties here
            r = secretor.uptakeInsideCellTotalCount(cell, cell.dict['upt_max'], cell.dict['upt_rel'])
            concentrationAtCOM = field[int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)]
            # print ("id=", cell.id, r.tot_amount)
            if concentrationAtCOM > cell.dict['q_p']:
                # READ/WRITE  ACCESS                
                cell.type = self.PROLIF
                cell.targetVolume += cell.dict['growth'] * abs(r.tot_amount) / cell.volume
            elif concentrationAtCOM < cell.dict['q_n']:
                cell.type = self.NECRO
                # cell.lambdaVolume = 0
                cell.targetVolume = 0
    
        # for cell in self.cell_list:
            # cell.targetVolume += 1        

        # # alternatively if you want to make growth a function of chemical concentration uncomment lines below and comment lines above        

        # field = self.field.CHEMICAL_FIELSD_NAME
        
        # for cell in self.cell_list:
            # concentrationAtCOM = field[int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)]

            # # you can use here any fcn of concentrationAtCOM
            # cell.targetVolume += 0.01 * concentrationAtCOM       

        
class MitosisSteppable(MitosisSteppableBase):
    def __init__(self,frequency=1):
        MitosisSteppableBase.__init__(self,frequency)
        self.mut_chance = 0.5
        self.mut_attribs = ['p_q', 'q_p', 'q_n', 'upt_max', 'upt_rel', 'growth']
        for att in self.mut_attribs:
            self.track_cell_level_scalar_attribute(field_name=att, 
                                                   attribute_name=att)
        
        

    def step(self, mcs):

        cells_to_divide=[]
        for cell in self.cell_list:
            if cell.volume>2*64:
                cells_to_divide.append(cell)

        for cell in cells_to_divide:

            self.divide_cell_random_orientation(cell)
            # Other valid options
            # self.divide_cell_orientation_vector_based(cell,1,1,0)
            # self.divide_cell_along_major_axis(cell)
            # self.divide_cell_along_minor_axis(cell)
    
    def do_mutation(self, cell, mut_chance):
        if np.random.uniform() < mut_chance:
            print('mutating')
            mutate_attr = np.random.choice(list(cell.dict.keys()))
            cell.dict[mutate_attr] *= np.random.uniform(0.9, 1.1)
            print(f'mutated {mutate_attr} to {cell.dict[mutate_attr]}')
    
    def update_attributes(self):
        # reducing parent target volume
        self.parent_cell.targetVolume /= 2.0                  

        self.clone_parent_2_child()
        
        self.do_mutation(self.parent_cell, self.mut_chance)
        self.do_mutation(self.child_cell, self.mut_chance)
        

        # for more control of what gets copied from parent to child use cloneAttributes function
        # self.clone_attributes(source_cell=self.parent_cell, target_cell=self.child_cell, no_clone_key_dict_list=[attrib1, attrib2]) 
        
        # if self.parent_cell.type==1:
            # self.child_cell.type=2
        # else:
            # self.child_cell.type=1

        