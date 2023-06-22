import os
from typing import Dict
import re
from collections import defaultdict
import xml.etree.ElementTree as ET

function_dict = {} #存放function的id和name
event_dict = {} #存放event的id 和name
relation_dict = defaultdict(list)  #存放function和participant的关系
participant_dict_id_name = {} #存放participant的id和name
participant_dict_id_type = {} #存放participant的id和type
arc_dict= defaultdict(list) #存放<arc>标签中所有的关系

def produce_solidity_from_epc(epc_path: str, out_dir: str, mult_chain_mode: bool):
    parse(epc_path,out_dir)
    try:
        os.mkdir(out_dir)
    except FileExistsError:
        print
        "Warning: <./generated> folder already exists"

def parse(epc_path: str,out_dir: str):
    root = ET.parse(epc_path).getroot()
#首先将所需要的字典元素提取出来
    parse_out_direct(root)
    #生成auctionStages文件
    parse_out_first_file(root,out_dir)

def parse_out_direct(node: ET.Element):
    root = node
    for element in root.iter():
        if element.tag == 'function':
            function_dict[element.attrib['id']] = element.find('name').text
        elif element.tag == 'relation':
            relation_dict[element.attrib['from']].append(element.attrib['to'])
        elif element.tag == 'participant':
            participant_dict_id_name[element.attrib['id']] = element.find('name').text
            participant_dict_id_type[element.attrib['id']] = element.find('type').text
        elif element.tag == 'arc':
            ele = element.find('./flow')
            arc_dict[ele.attrib['source']].append(ele.attrib['target'])
        elif element.tag == 'event':
            event_dict[element.attrib['id']] = element.find('name').text


def parse_out_first_file(node: ET.Element,out_dir: str):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    root = node
    print(root)
    epc_name = root.find("./epc").attrib['name']
    with open(f'outputs/{epc_name}.sol', 'w') as f:  # 先将已存在的内容清空，避免重复写入
        f.truncate(0)
    with open(f'outputs/{epc_name}.sol', 'w') as f:
        f.write('pragma solidity ^0.8.0;\n\n')
        f.write(f'contract {epc_name} {{\n\n')
        #print(f'Created file {epc_name}.sol')
    solidity_code = ""
    epc = root.find("./epc")
    solidity_code += participant(epc, out_dir, solidity_code)
    solidity_code = event(epc, out_dir, solidity_code)
    solidity_code = function(epc, out_dir, solidity_code,epc_name)
   # print("event:"+solidity_code)
    solidity_code += "}"
    out_process_sc = open(
        f'outputs/{epc_name}.sol', 'a')
    out_process_sc.write(solidity_code)
    out_process_sc.close()

def participant(node: ET.Element,out_dir: str,solidity_code:str):
    root = node
    #print(root)
    for participant in root:
        if participant.tag == 'participant':
            participant_name = participant.find('name').text
            #print(participant_name)
            type = participant.find('type').text
            attribute = participant.find('attribute').text
            if (type == "address" and attribute=="payable"):
                solidity_code += f"\taddress payable public {participant_name};\n"

            elif (type == "struct"):
                solidity_code += f"\tstruct  {participant_name}{{\n"
                attributes = participant.findall("./attribute")
                for attribute in attributes:
                    attribute_text=attribute.text
                    attribute_name=attribute.get("name")
                    solidity_code += f"\t\t{attribute_text} {attribute_name};\n"
                solidity_code += f"\t}}\n"
            else:
                solidity_code += f"\taddress public {participant_name};\n"

    #print(solidity_code)

    return solidity_code


def event(node: ET.Element,out_dir: str,solidity_code:str):
    root = node
    for event in root:
        # 如果子标签是event或function，则提取其name属性
        if event.tag == 'event':
            event_name = event.find('name').text
            # solidity_code += f"\tevent {event_name}("
            event_datainputs = event.findall(".//dataInput")
            if event_datainputs:
                event_inputs_name_type = []
                for datainput in event_datainputs:
                    event_inputs_name_type.append((datainput.get("type"), datainput.text))
                first_pair = event_inputs_name_type[0]
                first_key, first_value = first_pair
                solidity_code += "\t" + f"event {event_name}" + f"({first_key} {first_value} "
                other_pairs = event_inputs_name_type[1:]
                for pair in other_pairs:
                    key, value = pair
                    solidity_code += f",{key} {value}"
                solidity_code += "); \n"
            else:
                solidity_code += "\t" + f"event {event_name}" + f"();\n "
        return solidity_code

def function(node: ET.Element,out_dir: str,solidity_code:str,epc_name:str):
    root = node
    event_value=''
    for function in root:
         if function.tag == 'function':
             function_id = function.attrib['id']
             function_name = function.find('name').text
             to_process_elem = function.find('toProcess')
             for key, values in arc_dict.items():
                # print(function_id)
                for value in values:
                   if value == function_id:  # 如果找到了目标value
                       auction_key = key
                      # print("key:"+key)  # 输出对应的key
                       for key1,value1 in event_dict.items():
                        #   print(key1,value1)
                           if key1 == auction_key:
                              event_value = value1

             if to_process_elem is not None:
                 # 判断toProcess元素是否具有linkToEpcId属性
                 link_to_epc_id = to_process_elem.get('linkToEpcId')
                 if link_to_epc_id is not None:
                     # 输出linkToEpcId的值
                     #print('linkToEpcId:', link_to_epc_id)
                     parse_next(epc_name,link_to_epc_id,root,out_dir)
             else:
                 if function_name=="constructor":
                     datainputs = function.findall(".//dataInput")
                     data_inputs_name_type = []
                     for datainput in datainputs:
                         data_inputs_name_type.append((datainput.get("type"),datainput.text))
                     first_pair = data_inputs_name_type[0]
                     first_key, first_value = first_pair
                     solidity_code += "\t" + function_name + f"({first_key} {first_value} "
                     other_pairs = data_inputs_name_type[1:]
                     for pair in other_pairs:
                         key, value = pair
                         solidity_code += f",{key} {value}"
                     solidity_code += ") {\n"
                   #  solidity_code += "\t\t Item MyItem;\n\t\tbeneficiary = msg.sender;\n"
                     if event_value:
                        target_epc = root.findall(".//event[name='" + event_value + "']")[0]
                        print(target_epc)
                        event_datainputs = target_epc.findall(".//dataInput")
                        if event_datainputs:
                            event_inputs_name_type = []
                            for datainput in event_datainputs:
                                event_inputs_name_type.append((datainput.get("type"), datainput.text))
                            first_pair = event_inputs_name_type[0]
                            first_key, first_value = first_pair
                            solidity_code += "\t\t" + f"emit {event_value}" + f"( {first_value} "
                            other_pairs = event_inputs_name_type[1:]
                            for pair in other_pairs:
                                key, value = pair
                                solidity_code += f", {value}"
                            solidity_code += "); \n"
                        else:
                            solidity_code += "\t\t" + f"emit {event_value}" + f"();\n "
                       # solidity_code += f"\temit {event_value}"
                     solidity_code += "\t}\n"

                 else:
                    solidity_code += "\tfunction " + function_name + "() public {\n"
                    solidity_code += "\t// TODO: Implement function\n"
                    if event_value:
                        target_epc = root.findall(".//event[name='" + event_value + "']")[0]
                        print(target_epc)
                        event_datainputs = target_epc.findall(".//dataInput")
                        if event_datainputs:
                            event_inputs_name_type = []
                            for datainput in event_datainputs:
                                event_inputs_name_type.append((datainput.get("type"), datainput.text))
                            first_pair = event_inputs_name_type[0]
                            first_key, first_value = first_pair
                            solidity_code += "\t\t" + f"emit {event_value}" + f"( {first_value} "
                            other_pairs = event_inputs_name_type[1:]
                            for pair in other_pairs:
                                key, value = pair
                                solidity_code += f", {value}"
                            solidity_code += "); \n"
                    solidity_code += "\t}\n\n"
    return solidity_code

def parse_next(source:str,link_to_epc_id:int,node: ET.Element,out_dir: str):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    root = node
    target_epc = root.findall(".//epc[@epcId='" + link_to_epc_id + "']")[0]
    #print(target_epc)
    #next_epc = root.find("./epc")
    epc_name = target_epc.attrib['name']
    #print(epc_name)
    with open(f'outputs/{epc_name}.sol', 'w') as f:  # 先将已存在的内容清空，避免重复写入
        f.truncate(0)
    with open(f'outputs/{epc_name}.sol', 'w') as f:
         f.write('pragma solidity ^0.8.0;\n\n')
         f.write(f'contract {epc_name} is {source} {{\n\n')
         #print(f'Created file {epc_name}.sol')
    solidity_code = ""
    solidity_code += participant(target_epc, out_dir, solidity_code)
    solidity_code = event(target_epc, out_dir, solidity_code)
    solidity_code = function(target_epc, out_dir, solidity_code,epc_name)
    # # print("event:"+solidity_code)
    solidity_code += "}"
    out_process_sc = open(
        f'outputs/{epc_name}.sol', 'a')
    out_process_sc.write(solidity_code)
    out_process_sc.close()