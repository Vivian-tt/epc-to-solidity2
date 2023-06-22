from epc_parser import  produce_solidity_from_epc
import sys
def main(file_content):
    file_content = file_content.replace('/', '\\\\')
    # 在这里处理替换后的文件路径
   # print("Received file content:", file_content)
    epcfile = file_content
    outdir = 'E:\\python\\Python\\epc-to-solidity\\outputs'
    mult_chain_mode = False
    result = produce_solidity_from_epc(epcfile, outdir, mult_chain_mode)
   # print(result)
    return result



if __name__ == "__main__":
    file_content = sys.argv[1]
    main(file_content)
