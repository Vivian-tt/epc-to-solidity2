import re
def main():
    string = "payable,highestbidder"
    pattren = "payabls"
    m = re.search(pattren,string)
    if(m):
        print(m)

if __name__ == "__main__":
    main()
