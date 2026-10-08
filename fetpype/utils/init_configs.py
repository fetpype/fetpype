import argparse                                                                                                                                                                                                                                       
import shutil                                                                                                                                                                                                                                         
from importlib.resources import as_file, files                                                                                                                                                                                                        
                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                    
def main():                                                                                                                                                                                                                                           
    parser = argparse.ArgumentParser(                                                                                                                                                                                                                 
        description="Copy the default fetpype configs to a folder to make them easily editable."                                                                                                                                                                      
    )                                                                                                                                                                                                                                                 
    parser.add_argument("out_dir", help="Folder where the configs are copied.")                                                                                                                                                                       
    args = parser.parse_args()                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                    
    with as_file(files("fetpype") / "configs") as src:
        shutil.copytree(src, args.out_dir)
    print(f"Configs copied to {args.out_dir}. Use them with "
        f"--config {args.out_dir}/default_docker.yaml")
