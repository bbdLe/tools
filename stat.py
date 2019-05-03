# -*- coding: utf-8 -*-
# 不会用excel所以造的简单统计轮子

import optparse
import re

def process_file(f):
    bill_dict = {}
    total_bill = 0
    for line in f.readlines():
        line = line.strip("\r\n")
        if re.match(r".*月.*[号日]", line):
            continue

        line_list = line.split(' ')
        if line_list[0] in bill_dict:
            bill_dict[line_list[0]] += float(line_list[1])
        else:
            bill_dict[line_list[0]] = float(line_list[1])
        
        total_bill += float(line_list[1])

    sort_list = sorted(bill_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)

    for l in sort_list:
        if l[1] < 0:
            continue

        print "{0}({1:.1f}元 [{2:.1f}%])".format(l[0], l[1], l[1] / total_bill * 100)


    print "总计:", total_bill

def main():
    parser = optparse.OptionParser()
    parser.add_option("-b", "--bill_file", dest="bill_file", default=u"./4月账单.txt")
    (options, args) = parser.parse_args()

    with open(options.bill_file) as f:
        process_file(f)

if __name__ == "__main__":
    main()