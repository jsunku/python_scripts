#!/usr/bin/env python3

import re
import sys
import os
import argparse

def extract_ports(vhdl_content):
    port_pattern = re.compile(r'(\w+)\s*:\s*(in|out)\s+([\w_]+\([\w\s\d]+\)|[\w_]+)\s*;?', re.IGNORECASE)
    return port_pattern.findall(vhdl_content)

def extract_record_type_contents(vhdl_content, record_type_name):
    record_type_pattern = re.compile(fr'type\s+{record_type_name}\s+is\s+record(.*?)end\s+record;', re.IGNORECASE | re.DOTALL)
    match = record_type_pattern.search(vhdl_content)
    if match: 
        return match.group(1).strip()
    return None

def convert_to_signal(port_tuple, vhdl_content, processed_record_types, package_filename = None):
    name, _, data_type = port_tuple
    
    default_values = {
        r'std_logic_vector': "(others => '0')",
        r'std_logic': "'0'",
        r'unsigned' : "(others => '0')",
        r'signed' : "(others => '0')",
        r'integer': 0, 
        # Add more patterns and default values as required
    }

    default_value = "UNKNOWN_TYPE"

    # Loop through the patterns to find a match and get the default value
    for pattern, value in default_values.items():
        if re.search(pattern, data_type, re.IGNORECASE):
            default_value = value
            break

    return f'signal {name} : {data_type} := {default_value};'

def create_port_map(port_tuple):
    name, _, _ = port_tuple
    return f'{name} => {name}'

def extract_entity_name(vhdl_content):
    entity_pattern = re.compile(r'entity\s+(\w+)\s+is', re.IGNORECASE)
    match = entity_pattern.search(vhdl_content)
    if match:
        return match.group(1)
    return None

def create_component_declaration(generics,ports,entity_name):
    component_name = entity_name  # Use the provided entity_name
    
    generic_declarations = ['   {}'.format(generic.strip()) for generic in generics if generic.strip()]
    port_declarations = ['    {name} : {direction} {data_type}'.format(name=name, direction=direction, data_type=data_type) for name, direction, data_type in ports]
    
    component_decl = """component {component_name} is"""
    if generic_declarations:
        component_decl += """
        generic(
            {generic_declarations}
        );"""
        component_decl+= """
        port (
            {port_declarations}
        );
        end component;"""
    else:
        component_decl+= """
        port (
            {port_declarations}
        );
        end component;"""
    return component_decl.format(component_name=component_name, generic_declarations=';\n'.join(generic_declarations), port_declarations=';\n'.join(port_declarations))

def extract_libraries(vhdl_content):
    library_pattern = re.compile(r'library\s+(\w+);', re.IGNORECASE)
    libraries = library_pattern.findall(vhdl_content)

    use_pattern = re.compile(r'use\s+(.*?);',re.IGNORECASE)
    uses = use_pattern.findall(vhdl_content)

    return libraries, uses

def extract_generics(vhdl_content):
    generic_pattern = re.compile(r'generic\s*\(\s*(.*?)\s*\)', re.IGNORECASE | re.DOTALL)
    match = generic_pattern.search(vhdl_content)
    if match:
        return match.group(1).strip().split(';')
    return[]

def create_generic_map(generic):
    return f'{generic.split(":")[0].strip()} => {generic.split(":")[0].strip()}'

def update_testbench_content(existing_content, ports, generics, libraries_declaration, uses_declaration, vhdl_base_filename, signals, component_declaration, generic_maps, entity_name, port_maps):
    # Extract the part between markers
    start_marker = "-- testbench logic starts here."
    end_marker = "-- testbench logic ends here."
    start_index = existing_content.find(start_marker)
    end_index = existing_content.find(end_marker)

    if start_index != -1 and end_index != -1:
        logic_to_preserve = existing_content[start_index + len(start_marker):end_index].strip()
    else:
        logic_to_preserve = ""
    # Construct the updated content
    updated_content = """
{libraries_declaration}
{uses_declaration}

library STD;
use std.env.all;
use std.textio.all;

library uvvm_util;
context uvvm_util.uvvm_util_context;

entity {tb_name} is
end {tb_name};

architecture sim of {tb_name} is
    constant SYSCLK_PERIOD: time := 31.25 ns; --32MHz
    signal SYSCLK: std_logic := '0';
    signal clock_ena : boolean := false;
-- Converted signals:
{converted_signals}

{component_declaration}

-----------------------------------------------------------------------------
  -- Function to convert string to std_logic_vector
-----------------------------------------------------------------------------
function convert_string_to_slv(s: STRING) return std_logic_vector is 
    variable result: std_logic_vector(s'length-1 downto 0);
begin
    for i in s'range loop
        if s(i) = '1' then 
            result(i-s'left) := '1';
        else
            result(i-s'left) := '0';
        end if;    
    end loop; 
    return result;
end function convert_string_to_slv;

begin

 -----------------------------------------------------------------------------
  -- Clock Generator
  -----------------------------------------------------------------------------
  clock_generator(sysclk, clock_ena, SYSCLK_Period, "TB clock");
--============================================================


-- testbench logic starts here.

--============================================================
{preserved_logic}
--============================================================


-- testbench logic ends here.


UUT: entity work.{entity_name} 
    {generic_map_line}
    port map (
        {port_maps}
    );
--====================Connect these ports or comment them out========================================
<= SYSCLK
<= reset 
end sim;
""".format(libraries_declaration=libraries_declaration,
           uses_declaration=uses_declaration,
           tb_name=f"tb_{vhdl_base_filename}",
           converted_signals="\n".join(signals), 
           component_declaration=component_declaration,
           entity_name=entity_name,
           generic_map_line = 'generic map ('+','.join(generic_maps) + ')' if generic_maps else '',
           port_maps=",\n    ".join(port_maps),
           preserved_logic = logic_to_preserve)
    
    return updated_content

def main():
    parser = argparse.ArgumentParser(description="Generate VHDL testbench.")
    parser.add_argument("vhdl_filename", help="Path to the VHDL file.")
    parser.add_argument("--package", help = "Path to the VHDL package file.")
    
    args = parser.parse_args()

    vhdl_filename = args.vhdl_filename
    package_filename = args.package

    if not vhdl_filename:
        print("usage: script_testbench.py <your_vhdl_file> --package <your_package_file> ")
        return
    
    # Read the VHDL file
    with open(vhdl_filename, 'r') as file:
        vhdl_content = file.read()

    # Extract libraries and use statements
    libraries, uses = extract_libraries(vhdl_content)

    # Construct the libraries and use declaration for inclusion in the testbench
    libraries_declaration = '\n'.join([f"library {lib};" for lib in libraries])
    uses_declaration = '\n'.join([f"use {use};" for use in uses])

    # Create an empty set to keep track of processed record types
    processed_record_types = set()
    # Extract generics
    generics = extract_generics(vhdl_content)
    # Extract ports
    ports = extract_ports(vhdl_content)
    
    # Convert generics to generic map
    generic_maps = [create_generic_map(generic) for generic in generics if generic.strip()]
    # Convert ports to signals and create port map
    signals = [convert_to_signal(port, vhdl_content, processed_record_types, package_filename) for port in ports]
    port_maps = [create_port_map(port) for port in ports]
    entity_name = extract_entity_name(vhdl_content)
    if not entity_name:
        print("Error: Unable to extract entity name from VHDL file.")
        return

    component_declaration = create_component_declaration(generics, ports, entity_name)
     # Extract filename without the extension
    vhdl_base_filename = os.path.splitext(os.path.basename(vhdl_filename))[0]
    # Construct testbench with tb_prefix
    testbench_filename = f"tb_{vhdl_base_filename}.vhd"
    # Combine with the desired relative path
    testbench_filepath = os.path.join("simulation",testbench_filename)

    if os.path.exists(testbench_filepath):
        # Read the existing testbench file
        with open(testbench_filepath, 'r') as existing_file:
            existing_content = existing_file.read()

        # Update the necessary parts in the testbench content
        updated_content = update_testbench_content(existing_content, ports, generics, libraries_declaration, uses_declaration, vhdl_base_filename, signals, component_declaration, generic_maps, entity_name, port_maps)
        # Save the testbench content to a file
        with open(testbench_filepath, 'w') as file:
            file.write(updated_content)
        print(f"Testbench updated at {testbench_filepath}!")
    else:
        # Create the testbench content from scratch
        updated_content = update_testbench_content("", ports, generics, libraries_declaration, uses_declaration, vhdl_base_filename, signals, component_declaration, generic_maps, entity_name, port_maps)
         # Save the testbench content to a file
        with open(testbench_filepath, 'w') as file:
            file.write(updated_content)
        print(f"Testbench written to {testbench_filepath}!")

if __name__ == '__main__':
    main()