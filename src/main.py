import sys
import epc

def main(): 
    # print command line arguments
    filename = sys.argv[1]

    file = open(filename, "r")
    file_content = file.read()
    file.close()

    epc.addOMPtags(file_content, filename)


if __name__ == "__main__": 
    main()