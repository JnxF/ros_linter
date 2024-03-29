#!/usr/bin/env python3

import os
import sys
from lxml import etree
import re
import rospy
from std_msgs.msg import String

pip = list(map(lambda package: package.strip(), open(
    'built-in_pip_packages.txt', 'r').readlines()))
rospack = list(map(lambda package: package.strip(), open(
    'built-in_rospack_packages.txt', 'r').readlines()))


def find_launch_dependencies(path):
    error_packages = set()
    packages = os.popen(f'find {path} -type f -name "package.xml"').readlines()
    for package in packages:
        package_path = package.replace('package.xml', '').strip()
        paths = os.popen(
            f"find {package_path} -type f -name '*.launch'").readlines()

        for p in paths:
            try:
                tree = etree.parse(p.strip())
                finds = tree.xpath('//@file')
                errors = check_finds(finds, package, packages, p)
                error_packages = error_packages | errors
            except:
                continue

    error_packages = list(error_packages)
    return error_packages


def check_finds(elements, package, packages, path):
    errors = set()
    for element in elements:
        regex = re.compile(r'(\$\(find )(\w*)\)', re.IGNORECASE)
        match = regex.match(element)
        if not match or len(match.regs) is not 3:
            continue
        dependency = match[2]
        package_dependencies = parse_package(package)
        if (not exists_in_workspace(dependency, packages) and dependency not in package_dependencies and dependency not in pip and dependency not in rospack):
            errors.add(
                (dependency, path.strip(), package.strip()))

    return errors


def parse_package(package):
    tree = etree.parse(package.strip())
    metapackage = tree.xpath('//metapackage')
    if metapackage:
        return None
    depends = parse_depends(tree)
    name = tree.xpath('//name')
    depends.append(name[0].text)
    return depends


def exists_in_workspace(package, packages):
    metapackage_dependencies = parse_metapackage(packages)
    if package in metapackage_dependencies:
        return True
    return False


def parse_metapackage(packages):
    for package in packages:
        tree = etree.parse(package.strip())
        metapackage = tree.xpath('//metapackage')
        if metapackage:
            return parse_depends(tree)


def parse_depends(tree):
    run_depends = tree.xpath('//run_depend')
    run_depends = list(map(lambda dep: dep.text, run_depends))
    depends = tree.xpath('//depend')
    depends = list(map(lambda dep: dep.text, depends))
    if depends:
        run_depends.extend(depends)
    exec_depends = tree.xpath('//exec_depend')
    exec_depends = list(map(lambda dep: dep.text, exec_depends))
    if exec_depends:
        run_depends.extend(exec_depends)
    return run_depends


def print_errors(errors, pub):
    if (errors):
        pprint("\nMissing dependencies:", pub)
        for (error, launch_file, package) in errors:
            pprint(
                f"\t'{error}' found in '{launch_file}' \n\tis missing in '{package}'\n", pub)
    else:
        pprint("No errors found.", pub)

def pprint(t, pub):
    rospy.loginfo(t)
    pub.publish(t)

def talker():
    pub = rospy.Publisher('chatter', String, queue_size=10)
    rospy.init_node('talker', anonymous=True)
    rate = rospy.Rate(10) # 10hz

    path = rospy.get_param('path')
    pprint(f"Checking .launch files in {path} for undeclared dependencies...", pub)
    errors = find_launch_dependencies(path)
    print_errors(errors, pub)

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass