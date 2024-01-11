#!/usr/bin/env python3

import os
import sys

def extract_custom_content(file_path):
    """Extract content from a file based on custom comment delimiters."""
    extracted_blocks = []
    with open(file_path,'r',errors='replace') as f: #errors='replace' helps in reading files with non-UTF-8 characters
        lines = f.readlines()

    #Define start and end patterns
    start_pattern = "--/#?"
    end_pattern = "--?#/"

    in_block = False
    block_content =""
    for line in lines:
        if start_pattern in line and not in_block:
            in_block = True
            continue #skip the start pattern line

        if end_pattern in line and in_block:
            in_block = False
            extracted_blocks.append(block_content.strip())
            block_content = ""
            continue # Skip the end pattern line

        if in_block:
            block_content+= line
        elif "--Comment" in line:
            comment_start = line.find("--Comment") + len("--Comment")
            comment_content = line[comment_start:].strip()
            extracted_blocks.append("-"+ comment_content)

    return extracted_blocks

def main(directory):
    # Clear or create the customs.dox file at the beginning and add the header
    header = """/*! \page customtodos Custom To-Do List
*
*\n"""
    with open('custom_todos.dox', 'w') as f:
        f.write(header)

    # Iterate through all files in the given directory
    for root, _,files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root,file)
            extracted_contents = extract_custom_content(file_path)
            if extracted_contents:
                with open('custom_todos.dox','a') as output_file:
                    for content in extracted_contents:
                        if content.startswith("-"): # Single line comment
                            cleaned_content = content[2:].lstrip() # Remove "- " prefix and all leading whitespaces
                            output_file.write("* "+ "- " + cleaned_content + "\n")
                        else: # This is a block content
                            output_file.write("* \\code{.vhd}\n")
                            for line in content.split('\n'):
                                if line.strip(): #If its not an empty line
                                    output_file.write("* "+ line + "\n")
                                else:
                                    output_file.write("*\n")   
                            output_file.write("* \\endcode\n")
    
    # Append the closing tag for the header
    with open('custom_todos.dox','a') as f:
        f.write("*/\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script_name.py <directory_path>")
        sys.exit(1)
    directory_path = sys.argv[1]
    main(directory_path)