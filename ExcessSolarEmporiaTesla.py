#Last updated 2023-07-04
#!/usr/bin/python3

import teslapy
import pyemvue
import datetime
import time
import schedule
from pyemvue.enums import Scale, Unit

def func():

    def print_recursive(usage_dict, info, depth=0):
        for gid, device in usage_dict.items():
            for channelnum, channel in device.channels.items():
                name = channel.name
                if name == 'Main Meter':
                    name = info[gid].device_name
                print(channel.usage)
                if channel.nested_devices:
                    print_recursive(channel.nested_devices, info, depth+1)

    vue = pyemvue.PyEmVue()
    vue.login(username='#EMPORIAUSERHERE#', password='#EMPORIAPASSHERE#', token_storage_file='keys.json')

    devices = vue.get_devices()
    device_gids = []
    device_info = {}
    for device in devices:
        if not device.device_gid in device_gids:
            device_gids.append(device.device_gid)
            device_info[device.device_gid] = device
        else:
            device_info[device.device_gid].channels += device.channels

    usage_over_time = None

    # returns a list of recent usages or a single recent usage. If it is [None], it will retry until it gets a value other than [None]
    while usage_over_time is None or all(val is None for val in usage_over_time):
        usage_over_time, start_time = vue.get_chart_usage(
            devices[0].channels[0],
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5),
            datetime.datetime.now(datetime.timezone.utc),
            scale=Scale.SECOND.value,
            unit=Unit.KWH.value)

    # sets curret_net_metering to instant usage, uses [-1] in case there are multiple values returned, which can happen since we're asking for up to 5 seconds of usage.
    current_net_metering = 3600 * (float(usage_over_time[-1]))

    print("Instant net metering:", current_net_metering, " kW as of", datetime.datetime.now())
    print('Positive is drawing from the grid, negative is net producing.')

    # starts with Tesla API auth
    tesla = teslapy.Tesla('#TESLAEMAILHERE')
    if not tesla.authorized:
        print('Use browser to login. Page Not Found will be shown at success.')
        print('Open this URL: ' + tesla.authorization_url())
        tesla.fetch_token(authorization_response=input('Enter URL after authentication: '))

    #if tesla authorized, proceeds
    vehicles = tesla.vehicle_list()
    vehicles[0].sync_wake_up()

    #pulls charging status and assigned current request, stops if car is unplugged.
    if vehicles:
        # Retrieve the first vehicle
        vehicle = vehicles[0]

        # Access the vehicle's data
        vehicle_data = vehicle.get_vehicle_data()

        # Extract various values and assigns to variables
        charge_current_request = vehicle_data.get('charge_state', {}).get('charge_current_request')
        batt_percentage = vehicle_data.get('charge_state', {}).get('battery_level')
        target_level = vehicle_data.get('charge_state', {}).get('charge_limit_soc')
        charging_state = vehicle_data.get('charge_state', {}).get('charging_state')
        chargingkW = (charge_current_request * 240)
        available_power = current_net_metering

    else:
        print('No vehicles found.')

    #Some data to display about the car and its charging - always assumes 240V and will not work right on 120V:
    print('Car was previously (and currently) set to charge to ',charge_current_request, 'A and therefore', chargingkW/1000, 'kW at 240V.')
    print('Car charging is currently', charging_state , 'and the battery is charged to', batt_percentage,"% with a target charge level of", target_level, "%.")

    #Stops script if car is unplugged.
    if charging_state == 'Disconnected':
        print('Vehicle is unplugged, stopping script.')
        exit()

    #to prevent code from interfering with Supercharging at 50A or higher if this is accidentally left running
    if charge_current_request > 50:
        exit()

    if batt_percentage == 100:
        print('Battery fully charged. Ending')
        exit()

    if charging_state == 'Stopped':

        if current_net_metering > -1.5:
            print('Not enough excess solar to begin charging.')

        if -1.5 > current_net_metering > -2.4:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='5')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 5A for solar production between 1.5kW and 2.4kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()

        if -2.4 > current_net_metering > -3.6:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='10')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 10A for solar production between 2.4kW and 3.6kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()

        if -3.6 > current_net_metering > -4.8:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='15')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 15A for solar production between 3.6kW and 4.8kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()

        if -4.8 > current_net_metering > -6:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='20')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 20A for solar production between 4.8kW and 6.0kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()

        if -6 > current_net_metering > -7.2:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='25')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 25A for solar production between 6kW and 7.2kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()

        if -7.2 > current_net_metering:
            vehicles = tesla.vehicle_list()
            vehicles[0].command('CHARGING_AMPS', charging_amps='30')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 30A for solar production greater than 7.2kW, starting charge. Clearing low-energy count file.')
            file_to_delete = open("FiveAmpCount.txt", 'w')
            file_to_delete.close()


    if charging_state == 'Charging':

        if available_power == 0:
            print('Emporia output error? Doing nothing.')

        if -0.6 < available_power < 0:
            vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request - 3))
            print('Excess solar is low, e.g., -0.6kW and 0kW, lowering charging amps by 3A. Will ramp up every 2 minutes if able.')

        if 0 < available_power < 2:
            vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request - 10))
            print('Because grid draw is between 0kW and 2 kW, lowering charging amps by 10A. Will ramp up every 2 minutes if able.')

        if 2 < available_power:
                vehicles[0].command('CHARGING_AMPS', charging_amps='5')
                print('Because grid draw is above 2kW, there is not enough available solar power. Lowering charging amps to 5A and ramping up every 2 minutes if able.')
                # List to store the timestamps of 5A charging
                FiveAmpCount = []
                # Current timestamp when 5A charging is set, with a label
                FiveAmpSet = (time.strftime('%Y-%m-%d %H:%M:%S'))
                # Append the timestamp to the FiveAmpCount list
                FiveAmpCount.append(FiveAmpSet)
                # Write the timestamps to the text file
                with open('FiveAmpCount.txt', 'a') as file:
                    file.write('\n'.join(FiveAmpCount) + '\n')
                print('If this continues for 10 instances within 30 minutes, charging will be stopped automatically.')

        with open('FiveAmpCount.txt', 'r') as file:
            lines = file.readlines()
            recent_lines = []
            current_time = time.time()
            threshold = 30 * 60  # 30 minutes in seconds

            # Filter the lines within the last 30 minutes
            for line in lines:
                timestamp = time.mktime(time.strptime(line.strip(), '%Y-%m-%d %H:%M:%S'))
                if current_time - timestamp <= threshold:
                    recent_lines.append(line)

            # Check if there are at least 20 recent lines
            if len(recent_lines) >= 10:
                vehicles[0].command('STOP_CHARGE')
                print("There are at least 10 instances of charging being set to 5A in the last 30 minutes. Ending charging")

        if -2.5 > available_power > -9.5:
            vehicles = tesla.vehicle_list()
            vehicle_data.get('charge_state', {}).get('charge_current_request')
            if ((charge_current_request + 7) < 41):
                vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request + 7))
                print('Set charging amps to', (charge_current_request + 7),'A (increased by 7A) for production excess between 2.5kW and 9.5W, continuing charge.')
            else:
                vehicles[0].command('CHARGING_AMPS', charging_amps='40')
                print('Cannot increase beyond 40A. Set to 40A.')
        if -1.5 > available_power > -2.5:
            vehicles = tesla.vehicle_list()
            if ((charge_current_request + 6) < 41):
                vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request + 6))
                print('Set charging amps to', (charge_current_request + 6),'A (increased by 6A) for production excess between 1.5kW and 2.5kW, continuing charge.')
            else:
                vehicles[0].command('CHARGING_AMPS', charging_amps='40')
                print('Cannot increase beyond 40A. Set to 40A.')
        if -.3 > available_power > -1.5:
            vehicles = tesla.vehicle_list()
            if ((charge_current_request + 3) < 41):
                vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request + 3))
                print('Set charging amps to', (charge_current_request + 3),'A (increased by 3A) for production excess between 0.3kW and 1.5kW, continuing charge.')
            else:
                vehicles[0].command('CHARGING_AMPS', charging_amps='40')
                print('Cannot increase beyond 40A. Set to 40A.')
        if available_power < -8.5:
            print('You seem to have an impossible amount of excess solar, check to see what is going on here.')

    print('--- Iteration done at' , datetime.datetime.now() , '. ---')

    if charging_state == 'Complete':
        print('Since charging is complete, the program will exit until relaunched. Setting charge amps to 40A for next time.')
        vehicles[0].command('CHARGING_AMPS', charging_amps='40')
        exit()

schedule.every().day.at('08:00').until('17:30').do(func)
schedule.every(2).minutes.do(func)

func()
while True:
    schedule.run_pending()
    time.sleep(1)
