def generate_vhdl_template(entity_name):
    vhdl_template = f"""
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.numeric_std_unsigned.all;


entity {entity_name} is
  port (
  
  );
end {entity_name};

architecture {entity_name}_arch of {entity_name} is
  -- Record type definition
  type reg_type is record
  end record;
  signal r,rin : reg_type;

begin
  -- Combinational process
  comb : process(input_data, r)
    variable v : record_type;
  begin
    v := r; -- default assignment
      -- Add your combinational logic here
    end if;
  end process comb;

  -- Sequential process
  seq : process
  begin
    if rising_edge(clk) then
      -- Add your sequential logic here
    end if;
  end process seq;

end {entity_name}_arch;
"""

    return vhdl_template

if __name__ == "__main__":
    entity_name = "entity_name" # we can add our entity name here

    # Define input and output records
    input_record = """
    """
    output_record = """
    """

    vhdl_code = generate_vhdl_template(entity_name)

    with open(f"{entity_name}.vhd", "w") as vhdl_file:
        vhdl_file.write(vhdl_code)

    print(f"VHDL template with record types, processes, and default assignment saved as {entity_name}.vhd")
