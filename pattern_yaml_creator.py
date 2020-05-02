import yaml

def write_yaml(filename, obj_save):
    """
    Write some properties to generic yaml file
    :param to_path: where you want to save your file
    :param filename: name of the file
    :param obj_save: the object you want to save
    :return: a boolean with success or insuccess
    """
    try:
        with open(filename, 'w') as file:
            yaml.dump(obj_save, file)

        print(f"File successfully write to: {filename}")
        return True

    except Exception as message:
        print(f'Impossible to write the file: {message}')
        return False

patterns =   {  r'set -A': ['ERROR', 'Linux does not support array definition with this syntax',''],
                r'remsh': ['WARNING', 'remsh deprecatate, use ssh',''], 
                r'rpc' : ['WARNING', 'rpc deprecated, use scp',''], 
                r'cut(.)*0' : ['ERROR', 'Linux does not support end-of-raw delimiter with value 0 (zero)',''], 
                r'cut(\s)+-d(\s)+\'\#' : ['ERROR', 'Linux does not support string as field delimiter',''], 
                r'mailx -m|mailx(.)+-m' : ['ERROR', 'Linux non prevede l’opzione -m ( gestione allegati ) con il comando mailx',''], 
                r'typeset': ['ERROR', 'Linux non supporta alcune opzioni del comando, in particolare pad left/rigth',''], 
                r'wc': ['WARNING', 'Con wc possibile problema di compatibilità con Linux',''], 
                r'FTPsecGBS': ['WARNING', 'FTPsecGBS invoca un commando ftp con delle opzioni per i certificati non supportate (-Z)',''], 
                r'(if)(\s)+(\[.*\])(\s)+(then)':['ERROR', 'Linux richiede sempre il punto e virgola nel comando IF dopo le quadre',r'\1\2\3;\4\5'],
                r'(if)(\s)+(\[.*\])(\s)*($)':['ERROR', 'Linux richiede sempre il punto e virgola nel comando IF dopo le quadre',r'\1\2\3;\4\5'],
  }  

write_yaml('sh_scanner_patterns.yaml',patterns)