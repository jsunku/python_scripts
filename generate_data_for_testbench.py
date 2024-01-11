#!/usr/bin/env python3

import random
import argparse
import os
import logging

def int_to_bin(value, size):
    """Convert an integer to a binary string of specified size."""
    return format(value, f'0{size}b')

def log_metadata(metadata):
    logging.info("Metadata:")
    for key, value in metadata.items():
        logging.info(f"{key}: {value}")

def log_generated_data(data,name):
    logging.info(f"Generated {name} data:")
    for size, values in data.items():
        for value in values:
            logging.info(f"{size}-bit: {value}")

def log_generated_data_packet(data,name):
    logging.info(f"Generated {name} data:")
    for field, values in data.items():
        values_concatenated =''.join(values)
        logging.info(f"{field}: {values_concatenated}")

def generate_data(manual, sizes):
    data = {}

    for size in sizes:
        if size not in data:
            data[size] = []

    if manual:
        for size in sizes:
            print(f"Enter data for size {size} in decimal or hex (e.g., 255 or 0xFF):")
            value = input()
            if value.startswith("0x"):  # Hexadecimal input
                value_int = int(value, 16)
            else:  # Decimal input
                value_int = int(value)

            data[size].append(int_to_bin(value_int, size))
    else:
        for size in sizes:
            data_value = ''.join(random.choice(['0', '1']) for _ in range(size))
            data[size].append(data_value)

    return data

def choose_packet_structure():
    packet_structures = [
        {'name': 'Integrity Frame G1G RCC', 'fields' : {'Service Descriptor':2, 'Galileo Global Region Status':8, 'Integrity Data for Galileo Global Region':150,'EDBS Data':40,'Spare':128}},
        {'name': 'Message Sub-Frame G1G RCC', 'fields' : {'Data Packet 0':264, 'Data Packet 1':264, 'Data Packet 2':264, 'Data Packet 3':264,'Data Packet 4':264,'Data Packet 5':264,'Spare':200,'Data Packet 6':264,'Data Packet 7':264,'Data Packet 8':264,'Data Packet 9':264,'Data Packet 10':264,'Data Packet 11':264,}},
        {'name': 'Mission Frame G2G RCC', 'fields' : {'Version No':2,'Spacecraft ID':8,'Virtual Channel ID':6,'VC Frame Count':24,'Replay Flag':1,'VC Frame Count Usage Flag':1,'Spare':2,'VC Frame Count Cycle':4,'VCA SDU':3616},'manual_fields':['Version No']},
        # Add more data structures
    ]

    print("Available packet structures:")
    for i, structure in enumerate(packet_structures, start=1):
        manual_fields = ', '.join(structure.get('manual_fields',[]))
        print(f"{i}. {structure['name']} - Fields: {', '.join(structure['fields'])}, Manual Fields: {manual_fields}")

    while True:
        try:
            choice = int(input("Choose a structure (enter the corresponsinf number): "))
            if  1<= choice <= len(packet_structures):
                chosen_structure = packet_structures[choice -1]
                print(f"Chosen structure: {chosen_structure['name']}")
                return chosen_structure
            else:
                print ("Invalid Choice. Try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        
def generate_packet(structure):
    print(f"Generating {structure['name']} packet...")
    
    packet_data = {}

    manual_fields = structure.get('manual_fields',[])
    for field, size in structure['fields'].items():
        if manual_fields and field in structure['manual_fields']:
            # Manually input field
            user_input = input(f"Enter {field}: ")
            packet_data[field] = int_to_bin(int(user_input),size)
        else:
            # Randomly generate values for non specified fields
            data_value = ''.join(random.choice(['0','1']) for _ in range(size))
            packet_data[field] = data_value

    return packet_data

#### Function to save the data stream in file #########
def save_to_file_data(data, filename):
    with open(filename, 'w') as f:
        for size, values in data.items():
            for value in values:
                reversed_value = value[::-1]
                f.write(reversed_value + '\n')

#### Function to save packets in the packet name file ########
def save_to_file_packet(packet_data, filename):
    with open(filename, 'a') as f:
        reversed_values = [value[::-1] for value in reversed(packet_data.values())]
        line = ''.join(reversed_values)
        f.write(line+'\n')

#### Meta data infomration/Logging ######
def log_metadata(metadata):
    logging.info("Metadata:")
    for key, value in metadata.items():
        logging.info(f"{key}: {value}")

def main():
    parser = argparse.ArgumentParser(description='Generate data for VHDL testbench.')
    parser.add_argument('--manual', action='store_true', help='Enable manual data input')
    parser.add_argument('--p', action='store_true', help='Generate packet')
    parser.add_argument('--sizes', nargs='+', type=int, default=[8], help='List of data sizes (bit-widths) to generate data for')
    parser.add_argument('--filename', type=str, default='data_file.txt', help='Output filename for the generated data')  # New argument for filename
    
    args = parser.parse_args()

    # Check if provided path is a directory
    if os.path.isdir(args.filename):
        args.filename = os.path.join(args.filename, 'data_file.txt')
    
    # Logging always enabled by default
    logging.basicConfig(level=logging.INFO, filename='output.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    if args.p:
        chosen_structure = choose_packet_structure()
        if chosen_structure and 'manual_fields' in chosen_structure:
            generated_packet = generate_packet(chosen_structure)
            log_metadata({"Packet Type": chosen_structure['name']})
            log_generated_data_packet(generated_packet,chosen_structure['name'])

            packet_filename = f"{chosen_structure['name']}_packet.txt"
            save_to_file_packet(generated_packet, packet_filename)
            logging.info(f"Packet data saved to {packet_filename}")
        elif chosen_structure:
            logging.warning(f"Chosen structure '{chosen_structure['name']}' does not have manual fields.")
            generated_packet = generate_packet(chosen_structure)
            log_metadata({"Packet Type": chosen_structure['name']})
            log_generated_data_packet(generated_packet,chosen_structure['name'])

            packet_filename = f"{chosen_structure['name']}_packet.txt"
            save_to_file_packet(generated_packet, packet_filename)
            logging.info(f"Packet data saved to {packet_filename}")
        else: 
            logging.error("Cannot generate packet for the chosen structure. Missing manual fields")
    else:
        generated_data = generate_data(args.manual, args.sizes)
        log_metadata({"Data Type": "Generated Data"})
        log_generated_data(generated_data, "Data")
        save_to_file_data(generated_data, args.filename)  # Use the provided filename
        logging.info(f"Data saved to {args.filename}")

if __name__ == "__main__":
    main()