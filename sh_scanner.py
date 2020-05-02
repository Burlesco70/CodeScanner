# glob from https://realpython.com/working-with-files-in-python/
# TO DO: reporting: https://www.xlwings.org/blog/reporting-with-python

from pathlib import Path
import os
from shutil import copyfile, move
from chardet.universaldetector import UniversalDetector
import yaml
import click
import logging
import logging.config
import re

import pyfiglet # Just for fun
import cowsay # Just for fun

class YamlHelper():
    """
    Helper class with some utilities to manage yaml files
    """

    def read_yaml(self, filename):
        """
        Read a yaml file from disk
        """
        try:
            with open(filename) as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                logging.debug(f"File {filename} succesfully read")
            return data
        except Exception as message:
            logging.error(f"Impossibile to read the file: {message}")
            return None

    def write_yaml(self, filename, obj_save):
        """
        Write some properties to generic yaml file
        :param filename: name of the file
        :param obj_save: the object you want to save
        :return: a boolean with success or insuccess
        """
        try:
            with open(filename, 'w') as file:
                yaml.dump(obj_save, file)

            logging.debug(f"File {filename} succesfully written")
            return True

        except Exception as message:
            logging.error(f'Impossible to write the file: {message}')
            return False

class CodeFileScanner():
    """
    Code scanner for encoding and for custom patterns
    """
    def __init__(self, file_name, expected_encoding, dict_patterns, auto_correct):
        logging.debug(f"Init called with: {file_name}, {expected_encoding}, {dict_patterns}")
        self.file_name = file_name
        self.expected_encoding = expected_encoding
        self.dict_patterns = dict_patterns
        self.auto_correct = auto_correct        
        self.issues = [] # Initialize list of issues
        # Guess file encoding and set attribute self.encoding
        try:
            self.guess_encoding()
            if self.auto_correct:
                # Create a backup of original file, giving bck extension
                logging.debug(f"Create a backup of original file, giving bck extension: {os.path.splitext(self.file_name)[0]}.bck")
                copyfile(self.file_name, os.path.splitext(self.file_name)[0]+".bck")
        except Exception as e:
            logging.error(f'Impossible to guess encoding o make a backup file: {e}')
            print(click.style(f'Impossible to guess encoding o make a backup file: {e}', fg='red',bg='white'))
    
    def guess_encoding(self):
        """
        Method to guess the encoding on the file using chardet library
        """
        # Encoding guesser
        detector = UniversalDetector()
        detector.reset()
        # Guess decoding
        with open(self.file_name, 'rb') as f: 
            for line in f:
                detector.feed(line)
                if detector.done: 
                    break
        detector.close()
        # detector.result is a dictionary
        logging.debug(f"Encoding found: {detector.result}")
        self.encoding = detector.result['encoding']

    def check_encoding(self):
        logging.debug(f"Check_encoding called with auto_correct param: {self.auto_correct}")
        if ( self.encoding.lower() == self.expected_encoding.lower() ) or ( self.encoding.lower() == 'ascii' ):
            logging.info(f"[{self.file_name}], ENCODING[{self.encoding}], Encoding is ok!")
        else: 
            logging.warning(f"[{self.file_name}], ENCODING[{self.encoding}], Potential ENCODING problem")
            # Add error in result
            self.issues.append(['ERROR', f'Problematic encoding {self.encoding}'])
            if self.auto_correct:

                # Try to correct wrong encoding, read with guessed encoding
                try:
                    with open(self.file_name, 'r', encoding = self.encoding) as f: 
                        data = f.read()
                except UnicodeEncodeError as uee:
                    self.issues.append( [ 'ERROR', f'Encoding {self.encoding} not supported in LINUX', 
                        f'Automatic correction not possible: error reading {self.file_name}: {uee} '])
                # Save with "encoding_correct"
                try:
                    with open(self.file_name, 'w', encoding = self.expected_encoding) as f:
                        f.write(data)
                    # Automatic correction of the error
                    self.issues.append( ['ERROR-CORRECTION', f'Encoding {self.encoding} changed into {self.expected_encoding}'])
                    logging.warning(f"[{self.file_name}], ENCODING[{self.encoding}], Corrected potential ENCODING problem")
                    
                    # Update encoding with new value
                    self.encoding = self.expected_encoding                    

                except UnicodeEncodeError as uee:
                    self.issues.append( [ 'ERROR', f'Encoding {self.encoding} not supported in LINUX', 
                        f'Automatic correction not possible: error writing {self.file_name}: {uee} '])

    def check_patterns(self):
        """
        Check for all the patterns and eventually try to correct
        To manage corrections is created a temporary file with .corrected extension
        """
        logging.debug(f"Check_patterns called with: {self.auto_correct}")
        logging.debug(f"Reopening [{self.file_name}] with encoding {self.encoding}")
        with open(self.file_name, encoding = self.encoding) as f, open(os.path.splitext(self.file_name)[0]+".corrected",'w') as fcor:
            logging.debug(f"[{self.file_name}] - Pattern analysis start")
            for i, line in enumerate(f):
                line = line.strip()
                # Check for all the patterns
                # Reminder: dict_patterns is a dictionary of lists, p is key (the pattern)
                # patterns[p][0] - tipo errore
                # patterns[p][1] - descrizione
                # patterns[p][2] - substitution pattern for correction (if present)
                for p in self.dict_patterns:
                        # Find pattern in line
                        logging.debug(f"[{self.file_name}] - Checking pattern {p} in line {i+1}: {line}")
                        if re.match(rf"{p}", line): # Note: re.I option is not correct
                            logging.warning(f"[{self.file_name}], PATTERN[{p}], LINE[{i+1}]:{line}")
                            self.issues.append( [self.dict_patterns[p][0], self.dict_patterns[p][1], f"LINE[{i+1}]:{line}"])
                            # Managing corrections (correction patterns)
                            if self.dict_patterns[p][2] and self.auto_correct:
                                logging.debug(f"Replacement rule: {self.dict_patterns[p][2]}")
                                line = re.sub(rf"{p}",rf"{self.dict_patterns[p][2]}",line)
                                logging.warning(f"Writing correction: {line} to correction file")                 
                                self.issues.append( ['ERROR-CORRECTION', self.dict_patterns[p][1], f"NEWLINE[{i+1}]:{line}"])
                if self.auto_correct:
                    fcor.write(line+"\n")                                                                                  
                logging.debug(f"[{self.file_name}] - Analysis end")
        # End of pattern checking, now just manage temporary file and file
        if self.auto_correct:
            # Swap corrected with original
            logging.debug(f"Moving file {os.path.splitext(self.file_name)[0]}.corrected to {self.file_name}")
            move(os.path.splitext(self.file_name)[0]+".corrected", self.file_name)
        else:
            # Remove .corrected temporary file
            logging.debug(f"Removing file {os.path.splitext(self.file_name)[0]}.corrected")
            try:
                os.remove(os.path.splitext(self.file_name)[0]+".corrected")
            except OSError as oe:
                logging.error(f"OS Error OS: {oe}")

def scanner_presentation():
    click.clear()
    print(click.style(pyfiglet.figlet_format("Sh Scanner"),fg='blue',bg='white'))
    print(click.style("By Mario Nardi 2020",fg='blue',bg='white'))
    print(click.style("",fg='blue',bg='white'))

def scanner(encoding_correct, auto_correction, patterns_input_file, output_file):
    """
    Simple sh code scanner for rilocabile migration.
    It scan and check for wrong patterns and create a little report in YAML format
    """
    logging.info(f"Called with parameters: {encoding_correct}, {auto_correction}, {patterns_input_file}, {output_file}")
    # Patterns to search for in sh files, read from yaml file
    # patterns is a dictionary of lists
    yh = YamlHelper()
    patterns = yh.read_yaml(patterns_input_file)
    if not patterns:
        print(click.style(f"Error loading patterns file. Check {patterns_input_file}", fg='red',bg='white'))
        exit()

    # Dictionary with scanner issues/results
    scanner_result = {}

    # Main cycle on all the files
    # Note: in this case progress bar does not work because len of iterator is not known
    base_path = Path('.')
    with click.progressbar(base_path.glob('**/*.sh')) as bar:
        for name in bar:
            logging.debug(f"Checking encoding for file {name}")
            try:
                sh = CodeFileScanner(name, encoding_correct, patterns, auto_correction)
                sh.check_encoding()
                sh.check_patterns()
            except Exception as e:
                logging.error(f'Impossible to do checking for file: {name}')
                print(click.style(f'Impossible to do checking for file: {name}; exception {e}', fg='red',bg='white'))
            # If any issues, add them to the dictionary
            if sh.issues:
                scanner_result.setdefault(str(name),[]).append(sh.issues)

    # Managing final output
    logging.debug(f"Dictionary with output: {scanner_result}")
    if yh.write_yaml(output_file, scanner_result):
        #print(click.style(f"Output in file {output_file}", fg='green', bg='white'))
        cowsay.cow(f"Complete and detailed output in file: \n{output_file}")
    else:
        print(click.style(f"Error writing output file. Check {output_file} and log files", fg='red',bg='white'))

@click.command()
@click.option('-e', '--encoding_correct', default='UTF-8', help='The correct encoding expected for sh files')
@click.option('-a', '--auto_correction', type=bool, default=False, help='Enable / disable automatic corrections for encoding and patterns (if possible). A backup will be done of the original file')
@click.option('-p', '--patterns_input_file', default='sh_scanner_patterns.yaml', help='Input YAML file with patterns to search for in sh files')
@click.option('-o', '--output_file', default='sh_scanner_result.yaml', help='Output YAML file with scanner result')
def sh_scanner(encoding_correct, auto_correction, patterns_input_file, output_file):

    # Gets logger config from yaml
    yh = YamlHelper()
    config = yh.read_yaml('log_conf.yaml')
    logging.config.dictConfig(config)  

    # Show headings
    scanner_presentation()

    # Execute scanner
    scanner(encoding_correct, auto_correction, patterns_input_file, output_file)

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    sh_scanner()