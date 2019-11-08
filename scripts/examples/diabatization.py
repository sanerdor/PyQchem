from pyqchem.qchem_core import get_output_from_qchem
from pyqchem.qc_input import QchemInput
from pyqchem.parsers.parser_optimization import basic_optimization
from pyqchem.parsers.parser_rasci import rasci as rasci_parser
from pyqchem.structure import Structure

import numpy as np
import matplotlib.pyplot as plt


# define molecule
coor_monomer = [[ 0.6695,  0.0000,  0.0000],
                [-0.6695,  0.0000,  0.0000],
                [ 1.2321,  0.9289,  0.0000],
                [ 1.2321, -0.9289,  0.0000],
                [-1.2321,  0.9289,  0.0000],
                [-1.2321, -0.9289,  0.0000]]

symbols_monomer = ['C', 'C', 'H', 'H', 'H', 'H']

monomer = Structure(coordinates=coor_monomer,
                    atomic_elements=symbols_monomer,
                    charge=0,
                    multiplicity=1)

# optimization
qc_input = QchemInput(monomer,
                      jobtype='opt',
                      exchange='hf',
                      basis='sto-3g',
                      geom_opt_tol_gradient=300,
                      geom_opt_tol_energy=100,
                      geom_opt_coords=-1,
                      geom_opt_tol_displacement=1200)

parsed_data, err, fchk = get_output_from_qchem(qc_input,
                                               processors=4,
                                               parser=basic_optimization,
                                               read_fchk=True)

opt_monomer = parsed_data['optimized_molecule']

print('Optimized monomer structure')
print(opt_monomer)


coor_monomer2 = np.array(opt_monomer.get_coordinates())
coor_monomer2[:, 2] += 4.0  # monomer separation

coordinates = opt_monomer.get_coordinates() + coor_monomer2.tolist()
symbols_dimer = symbols_monomer * 2

dimer = Structure(coordinates=coordinates,
                  atomic_elements=symbols_dimer,
                  charge=0,
                  multiplicity=1)

print('Dimer structure')
print(dimer)

# sequential diabatization
diabatization_scheme = [{'method': 'ER',
                         'states': [1, 2, 3, 4]},
                        {'method': 'Boys',
                         'states': [3, 4]}
                        ]

# create qchem input
qc_input = QchemInput(dimer,
                      jobtype='sp',
                      exchange='hf',
                      correlation='rasci',
                      basis='sto-3g',
                      ras_act=6,
                      ras_elec=4,
                      ras_spin_mult=1,
                      ras_roots=12,
                      ras_do_hole=False,
                      ras_do_part=False,
                      # ras_sts_tm=True,
                      ras_diabatization_states=[3, 4, 5, 6],
                      ras_diabatization_scheme=diabatization_scheme,
                      set_iter=30)

# print(qc_input.get_txt())

parsed_data, _ = get_output_from_qchem(qc_input,
                                       processors=14,
                                       force_recalculation=False,
                                       parser=rasci_parser
                                       )


# print(parsed_data)
# parsed_data = rasci_parser(parsed_data)
# print(parsed_data)
print('Adiabatic states\n--------------------')
for i, state in enumerate(parsed_data['excited states rasci']):
    print('\nState {}'.format(i+1))
    print('Transition DM: ', state['transition_moment'])
    print('Energy: ', state['excitation_energy'])
    print(' Alpha  Beta   Amplitude')
    for conf in state['amplitudes']:
        print('  {}  {} {:8.3f}'.format(conf['alpha'], conf['beta'], conf['amplitude']))

diabatization = parsed_data['diabatization']

print('\nRotation Matrix')
print(np.array(diabatization['rot_matrix']))

print('\nAdiabatic Matrix')
print(np.array(diabatization['adiabatic_matrix']))

print('\nDiabatic Matrix')
print(np.array(diabatization['diabatic_matrix']))

print('Diabatic states\n--------------------')
for i, state in enumerate(diabatization['mulliken_analysis']):
    print('\nMulliken analysis - state', i+1)
    print('         Attach    Detach    Total ')
    for i_atom, (at, det) in enumerate(zip(state['attach'], state['detach'])):
        print('{:5}  {:8.4f}  {:8.4f}  {:8.4f}'.format(i_atom+1, at, det, at+det))

    bars = range(1, dimer.get_number_of_atoms()+1)
    plt.figure(i+1)
    plt.suptitle('Mulliken analysis')
    plt.title('State {}'.format(i+1))
    plt.bar(bars, state['attach'], label='Attachment')
    plt.bar(bars, state['detach'], label='Detachment')
    plt.plot(bars, state['total'], label='Total', color='r')
    plt.xlabel('Atoms')
    plt.ylabel('Charge [e-]')
    plt.axvline((monomer.get_number_of_atoms()+0.5), color='black')
    plt.legend()

plt.show()
