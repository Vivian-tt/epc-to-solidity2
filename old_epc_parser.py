
import os
from typing import Dict
import re
from collections import defaultdict
import xml.etree.ElementTree as ET
########################################################################################################################
########################################################################################################################
########################################################################################################################

# Variables

# List of processes fully on chain as XML elements
brokers: [ET.Element] = []

participant_names = []

# List of processes as XML elements
only_event_processes: [ET.Element] = []

# Process ID <-> Participant name
# Potential problem: Implementation uses name_or_id not process.attrib["id"]
process_names: Dict[str, str] = {}

# Message ID <-> Message/Arrow Label
message_name: Dict[str, str] = {}

# Message ID <-> Message/Arrow Action (OnChain event, or Swap)
message_action: Dict[str, str] = {}

# List of flow objects that are the source of messages flows
message_target_to_source = {}

# List of flow objects that are the target of messages flows
message_source_to_target = {}

message_flow_to_source = {}

message_flow_to_target = {}

message_source_to_flow = {}

message_target_to_flow = {}

# FlowObject ID <-> Process ID
object_s_process: Dict[str, str] = {}

# Process ID <-> Process ID
communicating_processes = defaultdict(list)

# TODO turn this into function annotations
# Flow Object ID <-> String
text_annotations = defaultdict(list)

# Process ID <-> Participant ID
processes_participant = defaultdict(list)

# Flow Object ID <-> Text Annotation ID
object_tag = defaultdict(list)

# Flow Object ID <-> Name String
object_name = {}

# Process <-> Blockchain
process_blockchain: Dict[str, str] = {}

# Flow Object ID <-> Token
object_tokens: Dict[str, str] = {}

# Process <-> Token
process_tokens = defaultdict(set)

# Info on tokes
token_info: Dict[str, str]


########################################################################################################################
########################################################################################################################
########################################################################################################################

# Functions

# Input
#       bpmn_path - Path to *.bpmn file
#       out_dir   - Path to output directory (does not need to exist)
#
# Output
#       Nada
#
# Effects
#       Saves Solidity files at bpmn_path to out_dir.
#
# Description
#       Generates Solidity files corresponding to the input BPMN file.
function_dict = {} #存放function的id和name
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
           # print(ele.attrib['source'],ele.attrib['target'])

def parse_out_first_file(node: ET.Element,out_dir: str):
    solidity_code = ""
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
# 获取根元素
    root = node
    epc_name = root.find("./epc").attrib['name']
    with open(f'outputs/{epc_name}.sol', 'w') as f: #先将已存在的内容清空，避免重复写入
        f.truncate(0)
    with open(f'outputs/{epc_name}.sol', 'w') as f:
        f.write('pragma solidity ^0.8.0;\n\n')
        f.write(f'contract {epc_name} {{\n\n')
        solidity_code += 'pragma solidity ^0.8.0;\n\n'
        solidity_code += f'contract {epc_name} {{\n\n'
        print(f'Created file {epc_name}.sol')

# 遍历第一个epc标签的子标签,将address，event和function取出来
    for participant in root.find("./epc"):
        if participant.tag == 'participant':
            participant_name = participant.find('name').text
            type = participant.find('type').text
            attribute = participant.find('attribute').text

            if (type == "address" and attribute=="payable"):
                solidity_code += f"\taddress payable public {participant_name};\n"
            if (type == "struct"):
                solidity_code += f"\tstruct  {participant_name}{{\n"
                attributes = participant.findall("./attribute")
                for attribute in attributes:
                    attribute_text=attribute.text
                    attribute_name=attribute.get("name")
                    solidity_code += f"\t\t{attribute_text} {attribute_name};\n"
            else:
                solidity_code += f"\taddress public {participant_name};\n"
    solidity_code += f"\t}}\n"
    for event in root.find("./epc"):
        # 如果子标签是event或function，则提取其name属性
         if event.tag == 'event':
            event_name = event.find('name').text
            #solidity_code += f"\tevent {event_name}("
            event_datainputs = event.findall(".//dataInput")
            if  event_datainputs:
                event_inputs_name_type = []
                for datainput in event_datainputs:
                    event_inputs_name_type.append((datainput.get("type"), datainput.text))
                first_pair = event_inputs_name_type[0]
                first_key, first_value = first_pair
                solidity_code += "\t" + f"event {event_name}"+f"({first_key} {first_value} "
                other_pairs = event_inputs_name_type[1:]
                for pair in other_pairs:
                    key, value = pair
                    solidity_code += f",{key} {value}"
                solidity_code += "); \n"
            else:
                solidity_code += "\t" +f"event {event_name}"+ f"();\n "
    for function in root.find("./epc"):
         if function.tag == 'function':
             function_name = function.find('name').text
             to_process_elem = function.find('toProcess')
             if to_process_elem is not None:
                 # 判断toProcess元素是否具有linkToEpcId属性
                 link_to_epc_id = to_process_elem.get('linkToEpcId')
                 if link_to_epc_id is not None:
                     # 输出linkToEpcId的值
                     print('linkToEpcId:', link_to_epc_id)
                     parse_next(epc_name,link_to_epc_id,root,out_dir)
             else:
                 if function_name=="constructor":
                     datainputs = function.findall(".//dataInput")
                     data_inputs_name_type = []
                     for datainput in datainputs:
                         data_inputs_name_type.append((datainput.get("type"),datainput.text))
                      #   solidity_code += f"{datainput_type} _{datainput_name}  {{\n"
                     # id = function.get('id')
                     # if id in relation_dict.keys():
                     #     values = relation_dict[id]
                     #     for value in values:
                     #         if value in participant_dict_id_name.keys():
                     #             print(value)
                     #             name_a = participant_dict_id_name[value]
                     #             type_a = participant_dict_id_type[value]
                    # solidity_code += "\t"+function_name + f"({type_a} _{name_a})  {{\n"
                     first_pair = data_inputs_name_type[0]
                     first_key, first_value = first_pair
                     solidity_code += "\t" + function_name + f"({first_key} {first_value} "
                     other_pairs = data_inputs_name_type[1:]
                     for pair in other_pairs:
                         key, value = pair
                         #print(key,value)
                         solidity_code += f",{key} {value}"
                     solidity_code += ") {\n"
                     solidity_code += "\t}\n"

                 else:
                    solidity_code += "\tfunction " + function_name + "() public {\n"
                    solidity_code += "\t// TODO: Implement function\n"

                    solidity_code += "}\n\n"

    # 关闭合约定义
    solidity_code += "}"
    out_process_sc = open(
        f'outputs/{epc_name}.sol', 'a')
    out_process_sc.write(solidity_code)
    out_process_sc.close()

def parse_next(source:str,link_to_epc_id:int,node: ET.Element,out_dir: str):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    # 获取根元素
    root = node
    target_epc = root.findall(".//epc[@epcId='" + link_to_epc_id + "']")[0]
    epc_name = target_epc.attrib['name']
    print(epc_name)
    with open(f'outputs/{epc_name}.sol', 'w') as f:  # 先将已存在的内容清空，避免重复写入
        f.truncate(0)
    with open(f'outputs/{epc_name}.sol', 'w') as f:
        f.write('pragma solidity ^0.8.0;\n\n')
        f.write(f'contract {epc_name} is {source} {{\n\n')
        print(f'Created file {epc_name}.sol')


#def parse_out_contract(node: ET.Element,out_dir: str):
    # tree = ET.parse('auction.epml')
    # root = tree.getroot()
    #
    # # Solidity代码中的函数定义
    # solidity_code = "pragma solidity ^0.8.0;\n\n"
    # for function in root.iter('function'):
    #     function_name = function.find('name').text
    #     solidity_code += "function " + function_name + "() public {\n"
    #     solidity_code += "\t// Solidity代码中的函数体\n"
    #     solidity_code += "}\n\n"
    #
    # # 输出Solidity代码
    # print(solidity_code)
    # 解析 EPML 代码
   # root = node
    # 获取合约名称
    # contract_name = root.find('epc').attrib['name']
    #
    # # 创建 Solidity 代码字符串
    # solidity_code = "pragma solidity ^0.8.0;\n\n"
    # solidity_code = solidity_code+f"contract {contract_name} {{\n"
    # 处理solidity变量，合约参与者address
    # for address in root.findall('.//'):
    #     if address.tag == 'function':
    #         address_name = address.find('name').text
    #         #print(address_name)
    #         pattern = r'\[(.*?)\]'
    #         matches = re.findall(pattern, address_name)
    #         #print(matches)
    #         if matches:
    #             #print(matches[0])
    #             patt="payable"
    #             m = re.search(patt,matches[0])
    #             #print(m)
    #             if m is not None:
    #                 t = matches[0].index(',')
    #                 match = matches[0][t+1:]
    #                 if match not in participant_names:
    #                     participant_names.append(match)
    #                     solidity_code+= f"  address payable public {match}; \n"
    #             else:
    #                 if matches[0] not in participant_names:
    #                     participant_names.append(matches[0])
    #                     solidity_code += f"  address public {matches[0]}; \n"

    # 处理事件和函数
    # for event in root.findall('.//'):
    #     if event.tag == 'event':
    #         event_name = event.find('name').text
    #         solidity_code += f"  event {event_name}();\n"
    # for function in root.findall('.//'):
    #     if function.tag == 'function':
    #         function_name = function.find('name').text
    #         function_name_without_brackets = re.sub(r'\[.*?\]', '', function_name)
    #
    #         print(function_name_without_brackets)  # 输出 "这是一个字符串"
    #         solidity_code += f"  function {function_name_without_brackets}() {{\n    // TODO: Implement function\n  }}\n"
    #
    # # 关闭合约定义
    # solidity_code += "}"

    # 输出 Solidity 代码
    # out_process_sc = open(
    #     out_dir + "/" +  "/auction.sol", "w+")
    # out_process_sc.write(solidity_code)
    # out_process_sc.close()
    # print(solidity_code)

    #
    # child: ET.Element
    # for child in node:
    #     if "epc" in child.tag:
    #         grandchild: ET.Element
    #         for grandchild in child:
    #             if "function" in grandchild.tag:
    #                 name = grandchild.attrib["name"]
    #                 actual_name = re.sub(r" *@Chain.*", "", name)
    #                # print(actual_name)
    #                 chain_ref = name.replace(actual_name, "").replace("@Chain", "").replace("(", "").replace(")", "") \
    #                     .strip(" ")
    #                # print(chain_ref)
    #                 process_names[grandchild.attrib["processRef"]] = clean_string(actual_name)
    #                 #print(process_names[grandchild.attrib["processRef"]])
    #                 processes_participant[grandchild.attrib["processRef"]] = grandchild.attrib["id"]
    #                # print(processes_participant[grandchild.attrib["processRef"]])
    #                 if chain_ref != "":
    #                     process_blockchain[grandchild.attrib["processRef"]] = chain_ref
    #
    #             elif "messageFlow" in grandchild.tag:
    #                 id: str = grandchild.attrib["id"]
    #                 source_ref: str = grandchild.attrib["sourceRef"]
    #                 target_ref: str = grandchild.attrib["targetRef"]
    #
    #                 message_flow_to_source[id] = source_ref
    #                 message_flow_to_target[id] = target_ref
    #
    #                 message_source_to_flow[source_ref] = id
    #                 message_target_to_flow[target_ref] = id
    #
    #                 if "name" in grandchild.attrib:
    #                     name = grandchild.attrib["name"].strip(" ")
    #                     if "@" in name:
    #                         actual_name = re.sub(r"\[[^\[\]]*\]", "", name).strip(" ").strip("\n")
    #                         message_name[id] = actual_name
    #                        # print(actual_name+"1")
    #                         action = name.replace(actual_name, "").replace("[", "").replace("]", "") \
    #                             .strip(" ").strip("\n")
    #                        # print(action)
    #                         message_action[id] = action
    #
    #                         if action.startswith('@Swap'):
    #                             sent = get_sent_token(action)
    #                             if sent.lower() != "eth":
    #                                 object_tokens[source_ref] = sent
    #
    #                             received = get_received_token(action)
    #                             if received.lower() != "eth":
    #                                 object_tokens[target_ref] = received
    #
    #                         elif action.startswith('@Transfer'):
    #                             sent = get_sent_token(action)
    #                             if sent.lower() != "eth":
    #                                 object_tokens[source_ref] = sent
    #
    #                     else:
    #                         message_name[id] = name
    #                 else:
    #                     message_name[id] = source_ref + "_to_" + target_ref
    #                 message_source_to_target[source_ref] = target_ref
    #                 message_target_to_source[target_ref] = source_ref
    #             elif "textAnnotation" in grandchild.tag:
    #                 for greatgrandchild in grandchild:
    #                     if "text" in greatgrandchild.tag:
    #                         text_annotations[grandchild.attrib["id"]] = greatgrandchild.text
    #             elif "association" in grandchild.tag:
    #                 object_tag[grandchild.attrib["sourceRef"]] = grandchild.attrib["targetRef"]
