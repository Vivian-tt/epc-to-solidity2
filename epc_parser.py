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
arc_dict_FunctionEvent= defaultdict(list) #存放<arc>标签中FunctionEventArc的关系
eventDefinition_dict = {}
functionDefinition_dict = {}
def produce_solidity_from_epc(epc_path: str, out_dir: str, mult_chain_mode: bool):
    result = parse(epc_path,out_dir)
    try:
        os.mkdir(out_dir)
    except FileExistsError:
        print
        "Warning: <./generated> folder already exists"
    return result

def parse(epc_path: str,out_dir: str):
    root = ET.parse(epc_path).getroot()
#首先将所需要的字典元素提取出来
    parse_out_direct(root)
    #生成auctionStages文件
    result = parse_out_first_file(root,out_dir)
    return result

def parse_out_direct(node: ET.Element):
    root = node
    for element in root.iter():
        if element.tag == 'definitions':
            for ele in element:
                if ele.tag == 'eventDefinition':
                    eventDefinition_dict[ele.attrib["DefId"]]=ele.attrib["name"]
                if ele.tag == 'functionDefinition':
                    functionDefinition_dict[ele.attrib["DefId"]]=ele.attrib["name"]
        if element.tag == 'function':
            function_name = element.find('name')
            if function_name is not None:
                function_dict[element.attrib['id']] = element.find('name').text
            else:
                for reference in element:
                    if reference.tag=='reference':
                        defRef_id = reference.attrib["defRef"]
                        defRef_name = functionDefinition_dict[defRef_id]
                        function_dict[element.attrib['id']] = defRef_name

        elif element.tag == 'relation':
            relation_dict[element.attrib['from']].append(element.attrib['to'])
        elif element.tag == 'view':
            view_name = element.attrib['name']
            # print(view_name)
            if (view_name == 'Party'):
                for participant in element:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        participant_dict_id_name[participant.attrib['unitId']] = participant_name
                        participant_dict_id_type[participant.attrib['unitId']] = "address"
            elif (view_name == 'Time' or view_name =='Price'):
                for participant in element:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        # 使用正则表达式模块匹配模式
                        pattern = r"(.*)@mapping\[(.*),(.*)\]"
                        match = re.match(pattern, participant_name)
                        if match:
                            participant_dict_id_name[participant.attrib['unitId']] = participant_name
                            participant_dict_id_type[participant.attrib['unitId']] = "mapping"
                        else:
                            participant_dict_id_name[participant.attrib['unitId']] = participant_name
                            participant_dict_id_type[participant.attrib['unitId']] = "uint"
            elif (view_name == 'state'):
                for participant in element:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        participant_dict_id_name[participant.attrib['unitId']] = participant_name
                        participant_dict_id_type[participant.attrib['unitId']] = "bool"
        elif element.tag == 'arc':
            ele_info = element.find('syntaxInfo')
            ele_flow = element.find('flow')
            implicitType = ele_info.attrib['implicitType']
            source = ele_flow.attrib['source']
            target = ele_flow.attrib['target']
            if implicitType == "FunctionEventArc":
                arc_dict_FunctionEvent[source].append(target)
        elif element.tag == 'event':
            event_name = element.find('name')
            if event_name is not None:
                event_dict[element.attrib['id']] = element.find('name').text
            else:
                for reference in element:
                    if reference.tag == 'reference':
                        defRef_id = reference.attrib["defRef"]
                        defRef_name = eventDefinition_dict[defRef_id]
                        event_dict[element.attrib['id']] = defRef_name
           # print(element.find('name').text)


def parse_out_first_file(node: ET.Element,out_dir: str):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    root = node
    epc_name = root.find(".//epc").attrib['name']
   # print(epc_name)
    with open(f'outputs/{epc_name}.sol', 'w') as f:  # 先将已存在的内容清空，避免重复写入
        f.truncate(0)
    with open(f'outputs/{epc_name}.sol', 'w') as f:
        f.write('pragma solidity ^0.8.0;\n\n')
        f.write(f'contract {epc_name} {{\n\n')
        #print(f'Created file {epc_name}.sol')
    solidity_code = ""

    epc = root.find("./directory")
    solidity_code += participant(epc, out_dir, solidity_code)
    epc = root.find(".//epc")
    solidity_code = event(epc, out_dir, solidity_code)
    epc = root.find(".//epc")
    solidity_code = function(epc, out_dir, solidity_code,epc_name)
   # print("event:"+solidity_code)
    solidity_code += "}"
    out_process_sc = open(
        f'outputs/{epc_name}.sol', 'a')
    out_process_sc.write(solidity_code)
    out_process_sc.close()
    #print(solidity_code)
    # 打开文件并读取内容到变量
    with open(f'outputs/{epc_name}.sol', 'r') as file:
        file_contents = file.read()
    # 输出文件内容
    print(file_contents)
    return file_contents
def participant(node: ET.Element,out_dir: str,solidity_code:str):
    root = node
    #print(root)
    for view in root:
        #print(view)
        if view.tag == 'view':
            view_name = view.attrib['name']
            #print(view_name)
            if (view_name == 'Party'):
                for participant in view:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        solidity_code += f"\taddress payable public {participant_name};\n"
            elif (view_name == 'Time' or view_name =='Price'):
                for participant in view:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        # 使用正则表达式模块匹配模式
                        pattern = r"(.*)@mapping\[(.*),(.*)\]"
                        match = re.match(pattern, participant_name)
                        if match:
                            # 如果有匹配，则提取键和值类型
                            key_type1 = match.group(2)
                            key_type2 = match.group(3)
                            match2 = re.search(r'(\w+)@', participant_name)
                            if match2:
                                participant_name_new = match2.group(1)
                            solidity_code += f"\tmapping ({key_type1}=>{key_type2})public {participant_name_new};\n"
                        else:
                           # print("No match found.")
                            solidity_code += f"\tuint public {participant_name};\n"
            elif (view_name == 'state'):
                for participant in view:
                    if participant.tag == 'unit':
                        participant_name = participant.attrib['name']
                        solidity_code += f"\tbool  {participant_name};\n"
    #print(solidity_code)

    return solidity_code


def event(node: ET.Element,out_dir: str,solidity_code:str):
    root = node
    count =0
    for event in root:
        # 如果子标签是event或function，则提取其name属性
        if event.tag == 'event':
            event_id = event.attrib["id"]
            event_name = event_dict[event_id]
            a = event.find('syntaxInfo').attrib['implicitType']
            # if (a):
            #     # print(a)
            if a != "EventStart":
                solidity_code += f"\tevent {event_name}("
                for var in event:
                    if var.tag == 'description':
                        var_value = var.text
                        # 使用正则表达式模块匹配模式
                        #print(var_value)
                        if var_value:
                            pattern = r"\[(.*?)\]"
                            match = re.match(pattern, var_value)
                            #print(match)
                            if match:
                                # 如果有匹配，则提取键和值类型
                                key_type1 = match.group(1).split(',')
                                #print(key_type1)
                                if len(key_type1) != 0:
                                    for item in key_type1[:-1]:
                                        if item in participant_dict_id_name.keys():
                                            type = participant_dict_id_type[item]
                                            name = participant_dict_id_name[item]
                                            solidity_code += f"{type} {name}, "
                                    solidity_code += f"{participant_dict_id_type[key_type1[-1]]} {participant_dict_id_name[key_type1[-1]]});\n"

                        else:
                             solidity_code += ");\n"
            # else:
            #     solidity_code += f"\tevent {event_name}(\n"
            #     if len(key_type1):
            #         for item in key_type1:
            #             solidity_code += item


    return solidity_code

def function(node: ET.Element,out_dir: str,solidity_code:str,epc_name:str):
    root = node
    event_value=''
    for function in root:
         if function.tag == 'function':
             syntaxInfo = function.find('syntaxInfo').attrib['implicitType']
             #function_name = function.find('name').text
             function_id = function.attrib['id']
             function_name = function_dict[function_id]
             #print(syntaxInfo)
             unitRef_list = []
             for reference in function:
                 if reference.tag == "unitReference":
                    # print(reference.attrib['unitRef'])
                     unitRef_list.append(reference.attrib['unitRef'])
             count = len(unitRef_list)
             #print(count)
             if syntaxInfo == 'initial':
                 solidity_code += "\t" + "constructor" + f"("
                 if count >= 1:
                     solidity_code += f"{participant_dict_id_type[unitRef_list[0]]} {participant_dict_id_name[unitRef_list[0]]}"
                     new_unitRef_list = unitRef_list[1:]
                     for i in new_unitRef_list:
                         solidity_code += f",{participant_dict_id_type[i]} {participant_dict_id_name[i]}"
                 solidity_code += ") { \n"
                 if function_id in arc_dict_FunctionEvent.keys():
                     event_id = arc_dict_FunctionEvent[function_id][0]
                     #print(event_id)
                     event_name = event_dict[event_id]
                     #print(event_name)
                     solidity_code += f"\t\temit {event_name}();\n"
                 solidity_code += "\t}\n\n"
             elif syntaxInfo == "payable":
                 solidity_code += f"\tfunction {function_name} ("
                 if count >= 1:
                     solidity_code += f"{participant_dict_id_type[unitRef_list[0]]} {participant_dict_id_name[unitRef_list[0]]}"
                     new_unitRef_list = unitRef_list[1:]
                     for i in new_unitRef_list:
                         solidity_code += f",{participant_dict_id_type[i]} {participant_dict_id_name[i]}"
                 solidity_code += ") public payable { \n"
                 if function_id in arc_dict_FunctionEvent.keys():
                     event_id = arc_dict_FunctionEvent[function_id][0]
                     #print(event_id)
                     event_name = event_dict[event_id]
                     #print(event_name)
                     solidity_code += f"\t\temit {event_name}();\n"
                 solidity_code += "\t}\n\n"

             elif syntaxInfo == "returns(bool)":
                 solidity_code += f"\tfunction {function_name} ("
                 if count >= 1:
                     solidity_code += f"{participant_dict_id_type[unitRef_list[0]]} {participant_dict_id_name[unitRef_list[0]]}"
                     new_unitRef_list = unitRef_list[1:]
                     for i in new_unitRef_list:
                         solidity_code += f",{participant_dict_id_type[i]} {participant_dict_id_name[i]}"
                 solidity_code += f") public {syntaxInfo} {{\n"
                 if function_id in arc_dict_FunctionEvent.keys():
                     event_id = arc_dict_FunctionEvent[function_id][0]
                     #print(event_id)
                     event_name = event_dict[event_id]
                     #print(event_name)
                     solidity_code += f"\t\temit {event_name}();\n"
                 solidity_code += "\t}\n\n"

             elif syntaxInfo.startswith("only"):
                  pattern = r"(.*)\[(.*)]"
                  match = re.match(pattern, syntaxInfo)
                  #print(match.group(2))
                  solidity_code += f"\tmodifier only{match.group(2)} (){{\n" \
                                   f"\t\trequire(msg.sender == {match.group(2)},"+ f"'only {match.group(2)} can call this.'"+");\n"\
                                   f"\t\t_;\n" \
                                   f"\t}}\n"
                  solidity_code += f"\tfunction {function_name} ("
                  if count >= 1:
                      solidity_code += f"{participant_dict_id_type[unitRef_list[0]]} {participant_dict_id_name[unitRef_list[0]]}"
                      new_unitRef_list = unitRef_list[1:]
                      for i in new_unitRef_list:
                          solidity_code += f",{participant_dict_id_type[i]} {participant_dict_id_name[i]}"
                  solidity_code += f") public only{match.group(2)} {{\n"
                  if function_id in arc_dict_FunctionEvent.keys():
                      event_id = arc_dict_FunctionEvent[function_id][0]
                      # print(event_id)
                      event_name = event_dict[event_id]
                      #print(event_name)
                      solidity_code += f"\t\temit {event_name}();\n"
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
    print(solidity_code)
    return solidity_code

def emitevent(eventname:str,node: ET.Element,out_dir: str,solidity_code:str):
    event_name = eventname
    root = node
    count = 0
    for event in root:
        # 如果子标签是event或function，则提取其name属性
        if event.tag == 'event':
            for var in event:
                if var.tag == 'name':
                    var_name = var.text
                    if var_name == event_name:
                        solidity_code += f"emit {event_name}("
                        if var.tag == 'description':
                            var_value = var.text
                            # 使用正则表达式模块匹配模式
                           # print(var_value)
                            if var_value:
                                pattern = r"\[(.*?)\]"
                                match = re.match(pattern, var_value)
                              # print(match)
                                if match:
                                    # 如果有匹配，则提取键和值类型
                                    key_type1 = match.group(1).split(',')
                                 #   print(key_type1)
                                    if len(key_type1) != 0:
                                        for item in key_type1[:-1]:
                                            if item in participant_dict_id_name.keys():
                                                type = participant_dict_id_type[item]
                                                name = participant_dict_id_name[item]
                                                solidity_code += f"<{type} {name}>, "
                                        solidity_code += f" <{participant_dict_id_type[key_type1[-1]]} {participant_dict_id_name[key_type1[-1]]}>);\n"

                            else:
                                solidity_code += ");\n"
        # else:
        #     solidity_code += f"\tevent {event_name}(\n"
        #     if len(key_type1):
        #         for item in key_type1:
        #             solidity_code += item

    return solidity_code

