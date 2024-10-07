from opentrons import protocol_api
from thelab._internal.open_turbidity_client import OpenTurbidityClient
import json

# metadata
metadata = {
    'protocolName': 'Solubility',
    'author': 'Muye Xiao',
    'description': 'Solubility measurement using OpenTurbidity module',
    'apiLevel': '2.13'
}


# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    def swell_tip(pipette, position):
        """
        Swells the tip in the `stock` labware location at a specified location.
        Notes
        -----
        Perform before a pipette is used for transfer.
        Parameters
        ----------
        pipette : pipette
            The pipette to be used.
        position:
            Position to swell the tip in.
        Returns
        -------
        None
        """
        for i in range(2):
            pipette.aspirate(100, position)
            protocol.delay(10)
            pipette.move_to(position.top())
            pipette.dispense(100, location=position)
        pipette.swelled = True

    def move_without_drip(position_to, position_from, pipette, amount):
        """
        Transfers substance from one location to another without dripping (hopefully).
        Notes
        -----
        Ideally, the swell function will be used before this function is called to reduce the
        probability of drips.
        Parameters
        ----------
        position_to: position
            Location of the target well plates to move substance to.
        position_from: position
            Location of the source well plates to move substance from.
        amount: float or int
            Amount of substance to be moved. (in uL)
        Returns
        -------
        None
        """
        # Check if pipette swelled before movement
        pipette.aspirate(amount, position_from)
        pipette.air_gap(15)
        pipette.dispense(location=position_to.top(z=2))

    addition_volume: int = 200  # in uL
    initial_volume: int = 2000
    cap_volume: int = 11000
    solvent_well = 'A1'
    # todo
    data_path = ''

    study_name = 'Test_study'
    folder_name = 'Test_study'
    monitor_parameters = {'tm_n_minutes': 1,
                          'tm_std_max': 10,
                          'tm_sem_max': 10,
                          'tm_upper_limit': 1,
                          'tm_lower_limit': 10,
                          'tm_range_limit': 10,
                          'slope_upper_limit': 5,
                          'slope_lower_limit': 5,
                          'measurements_per_min': 12,
                          'images_per_measurement': 10,
                          'reference_coefficient': 1.2
                          }

    # labware
    protocol.load_labware()
    OT_plate = protocol.load_labware('mx_1_wellplate_12ul', location='1')
    # todo solvent plate
    solvent_plate = protocol.load_labware('someplate', location='3')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', location='2')

    solvent_pos = solvent_plate[solvent_well]

    # pipettes
    left_pipette = protocol.load_instrument(
        'p300_single', mount='left', tip_racks=[tiprack])
    # right_pipette.flow_rate.aspirate = 40
    # right_pipette.flow_rate.dispense = 40
    left_pipette.flow_rate.aspirate = 40
    left_pipette.flow_rate.dispense = 40
    left_pipette.swelled = False
    # right_pipette.swelled = False

    # Open turbidity module
    # set parameters
    otc = OpenTurbidityClient()
    otc.wait_busy(time_out=10)
    otc.set_study_name(study_name)
    otc.wait_busy()
    otc.set_folder_name(folder_name)
    otc.wait_busy()
    otc.set_parameters(monitor_parameters)

    # get connected
    otc.hello()
    assert not otc.get_is_monitoring(), "already monitoring"
    otc.start_monitoring()
    protocol.delay(10)
    otc.wait_busy(time_out=30)
    exp_number = otc.get_run_number()
    total_volume = initial_volume
    addition_list: list[dict] = []

    #  swell tip
    left_pipette.pick_up_tip()
    swell_tip(left_pipette, solvent_pos)

    previous_state = 0
    now_state = otc.get_solution_status()
    state_changed_to_dissolved = False
    state_changed_to_stable = False
    try:
        while True:
            if total_volume >= cap_volume:
                print('Cap volume reached')
                break
            now_state = otc.get_solution_status()
            state_changed_to_dissolved: bool = now_state != previous_state and now_state == 2
            state_changed_to_stable: bool = now_state != previous_state and now_state == 1
            if state_changed_to_stable:
                time_addition, ref_addition, spl_addition = otc.get_data()
                # Add solvent
                move_without_drip(OT_plate['A1'], solvent_pos, left_pipette, amount=addition_volume)

                total_volume += addition_volume
                dict_addition = {'time': time_addition,
                                 'reference': ref_addition,
                                 'sample': spl_addition,
                                 'add_volume': addition_volume,
                                 'total_volume': total_volume,
                                 }
                addition_list.append(dict_addition)
                protocol.delay(10)
            elif state_changed_to_dissolved:
                protocol.delay(10)
                now_state = otc.get_solution_status()
                if now_state == 2:
                    print('Dissolved')
                    break

            save_dict = {'study_name': study_name,
                         'folder_name': folder_name,
                         'exp_number': exp_number,
                         'monitor_parameters': monitor_parameters,
                         'additions': addition_list,
                         }
            with open(data_path, 'w') as file:
                json.dump(save_dict, file)

            protocol.delay(4)
            previous_state = now_state
    except Exception as e:
        otc.stop_monitoring()
        protocol.delay(5)
        otc.wait_busy()
        otc.bye()
        left_pipette.drop_tip()
        raise e

    otc.stop_monitoring()
    protocol.delay(5)
    otc.wait_busy()
    otc.bye()
    left_pipette.drop_tip()
