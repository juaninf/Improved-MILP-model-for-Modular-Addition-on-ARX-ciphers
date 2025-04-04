
# ****************************************************************************

# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ****************************************************************************


from claasp.cipher_modules.models.cp.cp_model import solve_satisfy
from claasp.cipher_modules.models.cp.cp_models.cp_deterministic_truncated_xor_differential_model import CpDeterministicTruncatedXorDifferentialModel

from claasp.name_mappings import (CONSTANT, INTERMEDIATE_OUTPUT, CIPHER_OUTPUT, LINEAR_LAYER, SBOX, MIX_COLUMN,
                                  WORD_OPERATION, DETERMINISTIC_TRUNCATED_XOR_DIFFERENTIAL, IMPOSSIBLE_XOR_DIFFERENTIAL)
from claasp.cipher_modules.models.cp.solvers import SOLVER_DEFAULT


class CpImpossibleXorDifferentialModel(CpDeterministicTruncatedXorDifferentialModel):

    def __init__(self, cipher):
        super().__init__(cipher)
        self.inverse_cipher = cipher.cipher_inverse()
        self.middle_round = 1
    
    def add_solution_to_components_values(self, component_id, component_solution, components_values, j, output_to_parse,
                                          solution_number, string):
        inverse_cipher = self.inverse_cipher
        if component_id in self._cipher.inputs:
            components_values[f'solution{solution_number}'][f'{component_id}'] = component_solution
        elif component_id in self.inverse_cipher.inputs:
            components_values[f'solution{solution_number}'][f'inverse_{component_id}'] = component_solution
        elif f'{component_id}_i' in string:
            components_values[f'solution{solution_number}'][f'{component_id}_i'] = component_solution
        elif f'{component_id}_o' in string:
            components_values[f'solution{solution_number}'][f'{component_id}_o'] = component_solution
        elif f'inverse_{component_id} ' in string:
            components_values[f'solution{solution_number}'][f'inverse_{component_id}'] = component_solution
        elif f'{component_id} ' in string:
            components_values[f'solution{solution_number}'][f'{component_id}'] = component_solution
    
    def build_impossible_xor_differential_trail_model(self, fixed_variables=[], number_of_rounds=None, middle_round=1):
        """
        Build the CP model for the search of deterministic truncated XOR differential trails.

        INPUT:

        - ``fixed_variables`` -- **list** (default: `[]`); dictionaries containing the variables to be fixed in standard
          format
        - ``number_of_rounds`` -- **integer** (default: `None`); number of rounds

        EXAMPLES::

            sage: from claasp.cipher_modules.models.cp.cp_models.cp_deterministic_truncated_xor_differential_model import CpDeterministicTruncatedXorDifferentialModel
            sage: from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
            sage: from claasp.cipher_modules.models.utils import set_fixed_variables, integer_to_bit_list
            sage: speck = SpeckBlockCipher(block_bit_size=32, key_bit_size=64, number_of_rounds=2)
            sage: cp = CpDeterministicTruncatedXorDifferentialModel(speck)
            sage: fixed_variables = [set_fixed_variables('key', 'equal', range(64), integer_to_bit_list(0, 64, 'little'))]
            sage: cp.build_impossible_xor_differential_trail_model(fixed_variables)
        """
        self.initialise_model()
        if number_of_rounds is None:
            number_of_rounds = self._cipher.number_of_rounds
        inverse_cipher = self.inverse_cipher

        self._variables_list = []
        constraints = self.fix_variables_value_constraints(fixed_variables)
        deterministic_truncated_xor_differential = constraints
        self.middle_round = middle_round

        forward_components = []
        for r in range(middle_round):
            forward_components.extend(self._cipher.get_components_in_round(r))
        backward_components = []
        for r in range(number_of_rounds - middle_round + 1):
            backward_components.extend(inverse_cipher.get_components_in_round(r))
        
        for component in forward_components:
            component_types = [CONSTANT, INTERMEDIATE_OUTPUT, CIPHER_OUTPUT, LINEAR_LAYER,
                               SBOX, MIX_COLUMN, WORD_OPERATION]
            operation = component.description[0]
            operation_types = ['AND', 'OR', 'MODADD', 'MODSUB', 'NOT', 'ROTATE', 'SHIFT', 'XOR']
            if component.type not in component_types or \
                    (component.type == WORD_OPERATION and operation not in operation_types):
                print(f'{component.id} not yet implemented')
            if component.type == SBOX:
                variables, constraints, sbox_mant = component.cp_deterministic_truncated_xor_differential_trail_constraints(self.sbox_mant)
                self.sbox_mant = sbox_mant
            else:
                variables, constraints = component.cp_deterministic_truncated_xor_differential_trail_constraints()
            self._variables_list.extend(variables)
            deterministic_truncated_xor_differential.extend(constraints)

        inverse_variables = []
        inverse_constraints = []
        for component in backward_components:
            component_types = [CONSTANT, INTERMEDIATE_OUTPUT, CIPHER_OUTPUT, LINEAR_LAYER,
                               SBOX, MIX_COLUMN, WORD_OPERATION]
            operation = component.description[0]
            operation_types = ['AND', 'OR', 'MODADD', 'MODSUB', 'NOT', 'ROTATE', 'SHIFT', 'XOR']
            if component.type not in component_types or \
                    (component.type == WORD_OPERATION and operation not in operation_types):
                print(f'{component.id} not yet implemented')
            if component.type == SBOX:
                variables, constraints, sbox_mant = component.cp_deterministic_truncated_xor_differential_trail_constraints(self.sbox_mant, inverse = True)
                self.sbox_mant = sbox_mant
            else:
                variables, constraints = component.cp_deterministic_truncated_xor_differential_trail_constraints()
            inverse_variables.extend(variables)
            inverse_constraints.extend(constraints)
            
        for component in backward_components:
            for v in range(len(inverse_variables)):
                start = 0
                while component.id in inverse_variables[v][start:]:
                    new_start = inverse_variables[v].index(component.id, start)
                    inverse_variables[v] = inverse_variables[v][:new_start] + 'inverse_' + inverse_variables[v][new_start:]
                    start = new_start + 9
            for c in range(len(inverse_constraints)):
                start = 0
                while component.id in inverse_constraints[c][start:]:
                    new_start = inverse_constraints[c].index(component.id, start)
                    inverse_constraints[c] = inverse_constraints[c][:new_start] + 'inverse_' + inverse_constraints[c][new_start:]
                    start = new_start + 9
        for c in range(len(inverse_constraints)):
            start = 0
            while 'cipher_output' in inverse_constraints[c][start:]:
                new_start = inverse_constraints[c].index('cipher_output', start)
                inverse_constraints[c] = inverse_constraints[c][:new_start] + 'inverse_' + inverse_constraints[c][new_start:]
                start = new_start + 9
            start = 0
            while 'inverse_inverse_' in inverse_constraints[c][start:]:
                new_start = inverse_constraints[c].index('inverse_inverse_', start)
                inverse_constraints[c] = inverse_constraints[c][:new_start] + inverse_constraints[c][new_start + 8:]
                start = new_start
        for v in range(len(inverse_variables)):
            start = 0
            while 'inverse_inverse_' in inverse_variables[v][start:]:
                new_start = inverse_variables[v].index('inverse_inverse_', start)
                inverse_variables[v] = inverse_variables[v][:new_start] + inverse_variables[v][new_start + 8:]
                start = new_start
                 
        self._variables_list.extend(inverse_variables)
        deterministic_truncated_xor_differential.extend(inverse_constraints)

        variables, constraints = self.input_impossible_xor_differential_constraints(number_of_rounds = number_of_rounds, middle_round = middle_round)
        self._model_prefix.extend(variables)
        self._variables_list.extend(constraints)
        deterministic_truncated_xor_differential.extend(
            self.final_impossible_constraints(number_of_rounds, middle_round))
        self._model_constraints = self._model_prefix + self._variables_list + deterministic_truncated_xor_differential
        
    def extract_incompatibilities_from_output(self, components_values):
        
        cipher = self._cipher
        incompatibilities = {'plaintext': components_values['plaintext']}
        for component in cipher.get_all_components():
            if 'inverse_' + component.id in components_values.keys():
                incompatibility = False
                input_id_links = component.input_id_links
                input_bit_positions = component.input_bit_positions
                total_component_value = ''
                todo = True
                for id_link in input_id_links:
                    if id_link not in components_values.keys():
                        todo = False
                if todo:
                    for id_link, bit_positions in zip(input_id_links, input_bit_positions):
                        for b in bit_positions:
                            total_component_value += components_values[id_link]['value'][b]
                    if len(total_component_value) == len(components_values['inverse_' + component.id]['value']):
                        for i in range(len(total_component_value)):
                            if int(total_component_value[i]) + int(components_values['inverse_' + component.id]['value'][i]) == 1:
                                incompatibility = True
                        if incompatibility:
                            for id_link in input_id_links:
                                incompatibilities[id_link] = components_values[id_link]
                            incompatibilities['inverse_' + component.id] = components_values['inverse_' + component.id]
        incompatibilities['inverse_' + cipher.get_all_components_ids()[-1]] = components_values['inverse_' + cipher.get_all_components_ids()[-1]]
        solutions = {'solution1' : incompatibilities}
                    
        return solutions
        
    def extract_key_schedule(self):
        cipher = self._cipher
        key_schedule_components = ['key']
        for component in cipher.get_all_components():
            component_inputs = component.input_id_links
            ks = True
            for comp_input in component_inputs:
                if 'constant' not in comp_input and comp_input not in key_schedule_components:
                    ks = False
            if ks:
                key_schedule_components.append(component.id)
                
        return key_schedule_components

    def final_impossible_constraints(self, number_of_rounds, middle_round):
        """
        Return a CP constraints list for the cipher outputs and solving indications for single or second step model.

        INPUT:

        - ``number_of_rounds`` -- **integer**; number of rounds

        EXAMPLES::

            sage: from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
            sage: from claasp.cipher_modules.models.cp.cp_models.cp_deterministic_truncated_xor_differential_model import CpDeterministicTruncatedXorDifferentialModel
            sage: speck = SpeckBlockCipher(number_of_rounds=2)
            sage: cp = CpDeterministicTruncatedXorDifferentialModel(speck)
            sage: cp.final_impossible_constraints(2)[:-2]
            ['solve satisfy;']
        """
        cipher_inputs = self._cipher.inputs
        cipher = self._cipher
        inverse_cipher = self.inverse_cipher
        cipher_outputs = inverse_cipher.inputs
        cp_constraints = [solve_satisfy]
        new_constraint = 'output['
        incompatibility_constraint = 'constraint'
        key_schedule_components = self.extract_key_schedule()
        for element in cipher_inputs:
            new_constraint = f'{new_constraint}\"{element} = \"++ show({element}) ++ \"\\n\" ++'
        for element in cipher_outputs:
            new_constraint = f'{new_constraint}\"inverse_{element} = \"++ show(inverse_{element}) ++ \"\\n\" ++ \"0\" ++ \"\\n\" ++'
        for component in cipher.get_components_in_round(middle_round-1):
            if component.type != CONSTANT and component.id not in key_schedule_components:
                component_id = component.id
                input_id_links = component.input_id_links
                input_bit_positions = component.input_bit_positions
                component_inputs = []
                input_bit_size = 0
                for id_link, bit_positions in zip(input_id_links, input_bit_positions):
                    component_inputs.extend([f'{id_link}[{position}]' for position in bit_positions])
                    input_bit_size += len(bit_positions)
                    new_constraint = new_constraint + \
                        f'\"{id_link} = \"++ show({id_link})++ \"\\n\" ++ \"0\" ++ \"\\n\" ++'
                new_constraint = new_constraint + \
                    f'\"inverse_{component_id} = \"++ show(inverse_{component_id})++ \"\\n\" ++ \"0\" ++ \"\\n\" ++'
                for i in range(input_bit_size):
                    incompatibility_constraint += f'({component_inputs[i]}+inverse_{component_id}[{i}]=1) \\/ '
        incompatibility_constraint = incompatibility_constraint[:-4] + ';'
        new_constraint = new_constraint[:-2] + '];'
        cp_constraints.append(incompatibility_constraint)
        cp_constraints.append(new_constraint)

        return cp_constraints
        
    def find_all_impossible_xor_differential_trails(self, number_of_rounds,
                                                                fixed_values=[], solver_name=SOLVER_DEFAULT, middle_round=1):
        """
        Return the solution representing a differential trail with any weight.

        INPUT:

        - ``number_of_rounds`` -- **integer**; number of rounds
        - ``fixed_values`` -- **list** (default: `[]`); can be created using ``set_fixed_variables`` method
        - ``solver_name`` -- **string** (default: `None`); the name of the solver. Available values are:

          * ``'Chuffed'``
          * ``'Gecode'``
          * ``'COIN-BC'``

        EXAMPLES::

            sage: from claasp.cipher_modules.models.cp.cp_models.cp_deterministic_truncated_xor_differential_model import CpDeterministicTruncatedXorDifferentialModel
            sage: from claasp.cipher_modules.models.utils import set_fixed_variables
            sage: from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
            sage: speck = SpeckBlockCipher(number_of_rounds=3)
            sage: cp = CpDeterministicTruncatedXorDifferentialModel(speck)
            sage: plaintext = set_fixed_variables(
            ....:         component_id='plaintext',
            ....:         constraint_type='not_equal',
            ....:         bit_positions=range(32),
            ....:         bit_values=[0]*32)
            sage: key = set_fixed_variables(
            ....:         component_id='key',
            ....:         constraint_type='equal',
            ....:         bit_positions=range(64),
            ....:         bit_values=[0]*64)
            sage: cp.find_all_deterministic_truncated_xor_differential_trail(3, [plaintext,key], 'Chuffed') # random
            [{'cipher_id': 'speck_p32_k64_o32_r3',
              'components_values': {'cipher_output_2_12': {'value': '22222222222222202222222222222222',
                'weight': 0},
              ...
              'memory_megabytes': 0.02,
              'model_type': 'deterministic_truncated_xor_differential',
              'solver_name': 'Chuffed',
              'solving_time_seconds': 0.002,
              'total_weight': '0.0'}]
        """
        self.build_impossible_xor_differential_trail_model(fixed_values, number_of_rounds, middle_round)

        return self.solve(IMPOSSIBLE_XOR_DIFFERENTIAL, solver_name)

    def find_one_impossible_xor_differential_trail(self, number_of_rounds=None,
                                                                fixed_values=[], solver_name=SOLVER_DEFAULT, middle_round=1):
        """
        Return the solution representing a differential trail with any weight.

        INPUT:

        - ``number_of_rounds`` -- **integer** (default: `None`); number of rounds
        - ``fixed_values`` -- **list** (default: `[]`); can be created using ``set_fixed_variables`` method
        - ``solver_name`` -- **string** (default: `Chuffed`); the name of the solver. Available values are:

          * ``'Chuffed'``
          * ``'Gecode'``
          * ``'COIN-BC'``

        EXAMPLES::

            sage: from claasp.cipher_modules.models.cp.cp_models.cp_deterministic_truncated_xor_differential_model import CpDeterministicTruncatedXorDifferentialModel
            sage: from claasp.cipher_modules.models.utils import set_fixed_variables
            sage: from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
            sage: speck = SpeckBlockCipher(number_of_rounds=1)
            sage: cp = CpDeterministicTruncatedXorDifferentialModel(speck)
            sage: plaintext = set_fixed_variables(
            ....:         component_id='plaintext',
            ....:         constraint_type='not_equal',
            ....:         bit_positions=range(32),
            ....:         bit_values=[0]*32)
            sage: key = set_fixed_variables(
            ....:         component_id='key',
            ....:         constraint_type='equal',
            ....:         bit_positions=range(64),
            ....:         bit_values=[0]*64)
            sage: cp.find_one_deterministic_truncated_xor_differential_trail(1, [plaintext,key], 'Chuffed') # random
            [{'cipher_id': 'speck_p32_k64_o32_r1',
              'components_values': {'cipher_output_0_6': {'value': '22222222222222212222222222222220',
                'weight': 0},
               'intermediate_output_0_5': {'value': '0000000000000000', 'weight': 0},
               'key': {'value': '0000000000000000000000000000000000000000000000000000000000000000',
               'weight': 0},
               'modadd_0_1': {'value': '2222222222222221', 'weight': 0},
               'plaintext': {'value': '11111111011111111111111111111111', 'weight': 0},
               'rot_0_0': {'value': '1111111111111110', 'weight': 0},
               'rot_0_3': {'value': '1111111111111111', 'weight': 0},
               'xor_0_2': {'value': '2222222222222221', 'weight': 0},
               'xor_0_4': {'value': '2222222222222220', 'weight': 0}},
              'memory_megabytes': 0.01,
              'model_type': 'deterministic_truncated_xor_differential_one_solution',
              'solver_name': 'Chuffed',
              'solving_time_seconds': 0.0,
              'total_weight': '0.0'}]
        """
        self.build_impossible_xor_differential_trail_model(fixed_values, number_of_rounds, middle_round)

        return self.solve('impossible_xor_differential_one_solution', solver_name)
    
    def input_impossible_xor_differential_constraints(self, number_of_rounds=None, middle_round=None):
        if number_of_rounds is None:
            number_of_rounds = self._cipher.number_of_rounds

        cp_constraints = []
        cp_declarations = [f'array[0..{bit_size - 1}] of var 0..2: {input_};'
                           for input_, bit_size in zip(self._cipher.inputs, self._cipher.inputs_bit_size)]
        cipher = self._cipher
        inverse_cipher = self.inverse_cipher
        forward_components = []
        for r in range(middle_round):
            forward_components.extend(self._cipher.get_components_in_round(r))
        backward_components = []
        for r in range(number_of_rounds - middle_round + 1):
            backward_components.extend(inverse_cipher.get_components_in_round(r))
        cp_declarations.extend([f'array[0..{bit_size - 1}] of var 0..2: inverse_{input_};' for input_, bit_size in zip(inverse_cipher.inputs, inverse_cipher.inputs_bit_size)])  
        for component in forward_components:
            output_id_link = component.id
            output_size = int(component.output_bit_size)
            if 'output' in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: {output_id_link};')
            elif CIPHER_OUTPUT in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: {output_id_link};')
                cp_constraints.append(f'constraint count({output_id_link},2) < {output_size};')
            elif CONSTANT not in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: {output_id_link};')
        for component in backward_components:
            output_id_link = component.id
            output_size = int(component.output_bit_size)
            if 'output' in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: inverse_{output_id_link};')
            elif CIPHER_OUTPUT in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: inverse_{output_id_link};')
                cp_constraints.append(f'constraint count(inverse_{output_id_link},2) < {output_size};')
            elif CONSTANT not in component.type:
                cp_declarations.append(f'array[0..{output_size - 1}] of var 0..2: inverse_{output_id_link};')
        cp_constraints.append('constraint count(plaintext,1) > 0;')

        return cp_declarations, cp_constraints

    def _parse_solver_output(self, output_to_parse, model_type):
        """
        Parse solver solution (if needed).

        INPUT:

        - ``output_to_parse`` -- **list**; strings that represents the solver output
        - ``truncated`` -- **boolean** (default: `False`)

        EXAMPLES::

            sage: from claasp.cipher_modules.models.cp.cp_models.cp_xor_differential_trail_search_model import CpXorDifferentialTrailSearchModel
            sage: from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
            sage: from claasp.cipher_modules.models.utils import set_fixed_variables, integer_to_bit_list, write_model_to_file
            sage: speck = SpeckBlockCipher(block_bit_size=32, key_bit_size=64, number_of_rounds=4)
            sage: cp = CpXorDifferentialTrailSearchModel(speck)
            sage: fixed_variables = [set_fixed_variables('key', 'equal', range(64), integer_to_bit_list(0, 64, 'little'))]
            sage: fixed_variables.append(set_fixed_variables('plaintext', 'equal', range(32), integer_to_bit_list(0, 32, 'little')))
            sage: cp.build_xor_differential_trail_model(-1, fixed_variables)
            sage: write_model_to_file(cp._model_constraints,'doctesting_file.mzn')
            sage: command = ['minizinc', '--solver-statistics', '--solver', 'Chuffed', 'doctesting_file.mzn']
            sage: import subprocess
            sage: solver_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
            sage: os.remove('doctesting_file.mzn')
            sage: solver_output = solver_process.stdout.splitlines()
            sage: cp._parse_solver_output(solver_output) # random
            (0.018,
             ...
             'cipher_output_3_12': {'value': '0', 'weight': 0}}},
             ['0'])
        """
        components_values, memory, time = self.parse_solver_information(output_to_parse)
        all_components = [*self._cipher.inputs]
        for r in range(self.middle_round):
            all_components.extend([component.id for component in [*self._cipher.get_components_in_round(r)]])
        for r in range(self._cipher.number_of_rounds - self.middle_round + 1):
            all_components.extend(['inverse_' + component.id for component in [*self.inverse_cipher.get_components_in_round(r)]])
        all_components.extend([*self.inverse_cipher.inputs])
        for component_id in all_components:
            solution_number = 1
            for j, string in enumerate(output_to_parse):
                if f'{component_id} ' in string or f'{component_id}_i' in string or f'{component_id}_o' in string or f'inverse_{component_id}' in string:
                    value = self.format_component_value(component_id, string)
                    component_solution = {}
                    component_solution['value'] = value
                    self.add_solution_to_components_values(component_id, component_solution, components_values, j,
                                                           output_to_parse, solution_number, string)
                elif '----------' in string:
                    solution_number += 1
        if 'impossible' in model_type and solution_number > 1:
            components_values = self.extract_incompatibilities_from_output(components_values['solution1'])

        return time, memory, components_values
            
